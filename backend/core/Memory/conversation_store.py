from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Check if PostgreSQL is available
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, Json
    from psycopg2.pool import SimpleConnectionPool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 not available. ConversationStore will use SQLite or be disabled.")


class ConversationStore:
    def __init__(
            self,
            connection_string: str,
            min_connections: int = 2,
            max_connections: int = 20
    ):
        self.conn_string = connection_string
        
        # If it's a SQLite connection or psycopg2 is not available, raise an error
        # The chatbot will catch this and use DummyConversationStore
        if connection_string.startswith("sqlite:///"):
            raise ValueError("ConversationStore requires PostgreSQL. Use DummyConversationStore for SQLite.")
        
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required for ConversationStore but is not installed.")
        
        self.pool = SimpleConnectionPool(
            min_connections,
            max_connections,
            connection_string
        )

        logger.info(f"PostgreSQL connection pool created (min={min_connections}, max={max_connections})")

    def _get_conn(self):
        return self.pool.getconn()

    def _put_conn(self, conn):
        self.pool.putconn(conn)

    def create_session(self, session_id: str, user_id: Optional[str] = None, metadata: Dict = None) -> str:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO conversations (session_id, user_id, metadata)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET updated_at = NOW()
                    RETURNING id
                    """,
                    (session_id, user_id, Json(metadata or {}))
                )
                result = cur.fetchone()
                conn.commit()
                logger.info(f"Created/updated session: {session_id}")
                return str(result[0])
        finally:
            self._put_conn(conn)

    def add_message(
            self,
            session_id: str,
            role: str,
            content: str,
            tokens_used: int = 0,
            response_time_ms: int = None,
            metadata: Dict = None,
    ) -> int:
        conn = self._get_conn()
        try:
            conv_id = self._get_conversation_id(session_id)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO messages (conversation_id, role, content, tokens_used, response_time_ms, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (conv_id, role, content, tokens_used, response_time_ms, Json(metadata or {})),
                )
                msg_id = cur.fetchone()[0]

                cur.execute(
                    "UPDATE conversations SET updated_at = NOW() WHERE id = %s",
                    (conv_id,),
                )

                if role == "user":
                    cur.execute(
                        """
                        SELECT COUNT(*) 
                        FROM messages 
                        WHERE conversation_id = %s AND role = 'user'
                        """,
                        (conv_id,),
                    )
                    user_count = cur.fetchone()[0]

                    if user_count == 1:
                        first_line = content.strip().split("\n", 1)[0]
                        short = first_line[:60]
                        title = short + "..." if len(first_line) > 60 else short
                        cur.execute(
                            "UPDATE conversations SET title = %s WHERE id = %s",
                            (title, conv_id),
                        )

                conn.commit()
                return msg_id
        finally:
            self._put_conn(conn)

    def get_messages(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            conv_id = self._get_conversation_id(session_id)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT role, content, tokens_used, response_time_ms, created_at, metadata
                    FROM messages
                    WHERE conversation_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (conv_id, limit)
                )
                messages = cur.fetchall()
                return [dict(msg) for msg in reversed(messages)]
        finally:
            self._put_conn(conn)

    def get_full_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self.get_messages(session_id, limit=1000)

    def clear_session(self, session_id: str) -> int:
        conn = self._get_conn()
        try:
            conv_id = self._get_conversation_id(session_id)
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM messages WHERE conversation_id = %s",
                    (conv_id,)
                )
                deleted = cur.rowcount
                conn.commit()
                logger.info(f"Cleared {deleted} messages from session: {session_id}")
                return deleted
        finally:
            self._put_conn(conn)

    def session_exists(self, session_id: str) -> bool:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM conversations WHERE session_id = %s",
                    (session_id,)
                )
                return cur.fetchone() is not None
        finally:
            self._put_conn(conn)

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        conn = self._get_conn()
        try:
            conv_id = self._get_conversation_id(session_id)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT 
                        COUNT(*) as message_count,
                        SUM(tokens_used) as total_tokens,
                        AVG(response_time_ms) as avg_response_time,
                        MIN(created_at) as first_message,
                        MAX(created_at) as last_message
                    FROM messages
                    WHERE conversation_id = %s
                    """,
                    (conv_id,)
                )
                stats = dict(cur.fetchone())
                return stats
        finally:
            self._put_conn(conn)

    def get_all_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT 
                        c.session_id,
                        COALESCE(c.title, 'New Chat') AS title,
                        c.created_at,
                        c.updated_at,
                        (
                            SELECT COUNT(*) 
                            FROM messages m 
                            WHERE m.conversation_id = c.id
                        ) AS message_count
                    FROM conversations c
                    ORDER BY c.updated_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
                return [dict(r) for r in rows]
        finally:
            self._put_conn(conn)

    def update_session_title(self, session_id: str, title: str):
        conv_id = self._get_conversation_id(session_id)
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE conversations SET title = %s WHERE id = %s",
                    (title, conv_id)
                )
                conn.commit()
        finally:
            self._put_conn(conn)

    def _get_conversation_id(self, session_id: str) -> str:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM conversations WHERE session_id = %s",
                    (session_id,)
                )
                result = cur.fetchone()
                if not result:
                    raise ValueError(f"Session {session_id} not found. Create it first.")
                return str(result[0])
        finally:
            self._put_conn(conn)

    def delete_session(self, session_id: str) -> int:
        conn = self._get_conn()
        try:
            conv_id = self._get_conversation_id(session_id)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM messages WHERE conversation_id = %s", (conv_id,))
                msg_deleted = cur.rowcount

                cur.execute("DELETE FROM conversations WHERE session_id = %s", (session_id,))
                conv_deleted = cur.rowcount

                conn.commit()
                return msg_deleted + conv_deleted
        finally:
            self._put_conn(conn)

    def get_pool_stats(self) -> Dict[str, Any]:
        try:
            return {
                'min_connections': self.pool.minconn,
                'max_connections': self.pool.maxconn,
                'available': len(self.pool._pool) if hasattr(self.pool, '_pool') else 0,
                'status': 'healthy'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def close(self):
        self.pool.closeall()
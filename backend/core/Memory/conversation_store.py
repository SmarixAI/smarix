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
    logger.warning(
        "psycopg2 not available. ConversationStore will use SQLite or be disabled."
    )


class ConversationStore:
    def __init__(
        self,
        connection_string: str,
        min_connections: int = 2,
        max_connections: int = 20,
    ):
        self.conn_string = connection_string

        # If it's a SQLite connection or psycopg2 is not available, raise an error
        if connection_string.startswith("sqlite:///"):
            raise ValueError(
                "ConversationStore requires PostgreSQL. Use DummyConversationStore for SQLite."
            )

        if not PSYCOPG2_AVAILABLE:
            raise ImportError(
                "psycopg2 is required for ConversationStore but is not installed."
            )

        self.pool = SimpleConnectionPool(
            min_connections, max_connections, connection_string
        )

        logger.info(
            f"PostgreSQL connection pool created (min={min_connections}, max={max_connections})"
        )

    def _get_conn(self):
        return self.pool.getconn()

    def _put_conn(self, conn):
        self.pool.putconn(conn)

    def _set_schema_context(self, cur, schema_name: str):
        """
        Crucial for Multi-Tenancy:
        Sets the search path to the specific user's schema first, then public.
        This ensures queries hit the user's isolated tables.
        """
        if schema_name:
            # We sanitize minimally here, but schema_name should be validated by the caller (routes.py)
            # 'public' is added as fallback for extensions like uuid-ossp or shared tables
            cur.execute(f"SET search_path TO {schema_name}, public")

    def create_session(
        self,
        session_id: str,
        schema_name: str,
        user_id: Optional[str] = None,
        metadata: Dict = None,
    ) -> str:
        """
        Creates a session in the specific user's schema.
        """
        if not schema_name:
            raise ValueError("schema_name is required for creating a session")

        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                self._set_schema_context(cur, schema_name)

                cur.execute(
                    """
                    INSERT INTO conversations (session_id, user_id, metadata)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET updated_at = NOW()
                    RETURNING id
                    """,
                    (session_id, user_id, Json(metadata or {})),
                )
                result = cur.fetchone()
                conn.commit()
                logger.info(
                    f"Created/updated session: {session_id} in schema: {schema_name}"
                )
                return str(result[0])
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating session in {schema_name}: {e}")
            raise e
        finally:
            self._put_conn(conn)

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        schema_name: str,
        tokens_used: int = 0,
        response_time_ms: int = None,
        metadata: Dict = None,
    ) -> int:
        if not schema_name:
            raise ValueError("schema_name is required to add a message")

        conn = self._get_conn()
        cur = None
        try:
            cur = conn.cursor()
            self._set_schema_context(cur, schema_name)

            # ✅ Get or create conversation
            conv_id = self._get_conversation_id(cur, session_id)
            
            if conv_id is None:
                # Conversation doesn't exist - create it
                print(f"🆕 Creating new conversation for session {session_id}")
                cur.execute(
                    """
                    INSERT INTO conversations (session_id, created_at, updated_at, title)
                    VALUES (%s, NOW(), NOW(), 'New Chat')
                    RETURNING id
                    """,
                    (session_id,),
                )
                conv_id = cur.fetchone()[0]
                print(f"✅ Created conversation_id: {conv_id}")

            cur.execute(
                """
                INSERT INTO messages (conversation_id, role, content, tokens_used, response_time_ms, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    conv_id,
                    role,
                    content,
                    tokens_used,
                    response_time_ms,
                    Json(metadata or {}),
                ),
            )
            msg_id = cur.fetchone()[0]

            cur.execute(
                "UPDATE conversations SET updated_at = NOW() WHERE id = %s",
                (conv_id,),
            )

            # Generate title if it's the first user message in this schema
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

            # ✅ CRITICAL: Commit BEFORE closing cursor
            conn.commit()
            
            # ✅ Verify the message was actually saved
            cur.execute(
                "SELECT COUNT(*) FROM messages WHERE id = %s",
                (msg_id,)
            )
            verify_count = cur.fetchone()[0]
            
            print(f"✅ Added message {msg_id} to conversation {conv_id} (verified: {verify_count} row exists)")
            
            if verify_count == 0:
                raise Exception(f"Message {msg_id} was not saved to database!")
            
            return msg_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error adding message in {schema_name}: {e}")
            import traceback
            traceback.print_exc()
            raise e
        finally:
            if cur:
                cur.close()
            if conn:
                self._put_conn(conn)



    def get_messages(
        self, session_id: str, schema_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                self._set_schema_context(cur, schema_name)

                conv_id = self._get_conversation_id(cur, session_id)
                
                if conv_id is None:
                    print(f"📖 No conversation_id found for session {session_id}, returning empty messages")
                    return []

                # ✅ Changed: Order ASC (oldest first) so we don't need to reverse
                cur.execute(
                    """
                    SELECT id, role, content, tokens_used, response_time_ms, created_at, metadata
                    FROM messages
                    WHERE conversation_id = %s
                    ORDER BY created_at ASC, id ASC
                    LIMIT %s
                    """,
                    (conv_id, limit),
                )
                messages = cur.fetchall()
                
                print(f"📖 Found {len(messages)} messages for conversation_id {conv_id}")
                
                # ✅ Debug: Print first and last message
                if messages:
                    print(f"  First message: role={messages[0]['role']}, content={messages[0]['content'][:50]}")
                    print(f"  Last message: role={messages[-1]['role']}, content={messages[-1]['content'][:50]}")
                
                # ✅ No need to reverse since we ordered ASC
                return [dict(msg) for msg in messages]
                
        except Exception as e:
            logger.error(f"Error fetching messages in {schema_name}: {e}")
            import traceback
            traceback.print_exc() 
            return []
        finally:
            self._put_conn(conn)

    def get_full_history(
        self, session_id: str, schema_name: str
    ) -> List[Dict[str, Any]]:
        return self.get_messages(session_id, schema_name, limit=1000)

    def clear_session(self, session_id: str, schema_name: str) -> int:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                self._set_schema_context(cur, schema_name)

                conv_id = self._get_conversation_id(cur, session_id)
                cur.execute(
                    "DELETE FROM messages WHERE conversation_id = %s", (conv_id,)
                )
                deleted = cur.rowcount
                conn.commit()
                logger.info(
                    f"Cleared {deleted} messages from session: {session_id} in {schema_name}"
                )
                return deleted
        finally:
            self._put_conn(conn)

    def session_exists(self, session_id: str, schema_name: str) -> bool:
        if not schema_name:
            return False

        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                self._set_schema_context(cur, schema_name)
                cur.execute(
                    "SELECT 1 FROM conversations WHERE session_id = %s", (session_id,)
                )
                return cur.fetchone() is not None
        except Exception:
            return False
        finally:
            self._put_conn(conn)

    def get_session_stats(self, session_id: str, schema_name: str) -> Dict[str, Any]:
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                self._set_schema_context(cur, schema_name)

                # Get conversation_id - handle case where it doesn't exist
                try:
                    conv_id = self._get_conversation_id(cur, session_id)
                except Exception as e:
                    print(f"⚠️ Error getting conversation_id for session {session_id}: {e}")
                    # Return default stats for new/empty sessions
                    return {
                        'message_count': 0,
                        'total_tokens': 0,
                        'avg_response_time': 0,
                        'first_message': '',
                        'last_message': ''
                    }
                
                # Handle invalid conversation_id
                if not conv_id or conv_id == 0:
                    print(f"⚠️ Invalid conversation_id ({conv_id}) for session {session_id}")
                    return {
                        'message_count': 0,
                        'total_tokens': 0,
                        'avg_response_time': 0,
                        'first_message': '',
                        'last_message': ''
                    }

                cur.execute(
                    """
                    SELECT 
                        COUNT(*) as message_count,
                        COALESCE(SUM(tokens_used), 0) as total_tokens,
                        COALESCE(AVG(response_time_ms), 0) as avg_response_time,
                        MIN(created_at) as first_message,
                        MAX(created_at) as last_message
                    FROM messages
                    WHERE conversation_id = %s
                    """,
                    (conv_id,),
                )
                
                result = cur.fetchone()
                
                # Handle empty result or all-NULL result
                if not result:
                    return {
                        'message_count': 0,
                        'total_tokens': 0,
                        'avg_response_time': 0,
                        'first_message': '',
                        'last_message': ''
                    }
                
                stats = dict(result)
                
                # Convert None values to defaults
                stats['message_count'] = stats.get('message_count') or 0
                stats['total_tokens'] = stats.get('total_tokens') or 0
                stats['avg_response_time'] = stats.get('avg_response_time') or 0
                stats['first_message'] = stats.get('first_message') or ''
                stats['last_message'] = stats.get('last_message') or ''
                
                return stats
                
        except Exception as e:
            print(f"❌ Exception in get_session_stats for {session_id}: {e}")
            import traceback
            traceback.print_exc()
            # Return defaults instead of raising
            return {
                'message_count': 0,
                'total_tokens': 0,
                'avg_response_time': 0,
                'first_message': '',
                'last_message': ''
            }
        finally:
            self._put_conn(conn)

    def get_all_sessions(
        self, schema_name: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Gets sessions ONLY for the specific schema (User).
        This naturally filters data so user A cannot see user B's chats.
        """
        if not schema_name:
            return []

        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                self._set_schema_context(cur, schema_name)

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
        except Exception as e:
            logger.error(f"Error fetching sessions for {schema_name}: {e}")
            return []
        finally:
            self._put_conn(conn)

    def update_session_title(self, session_id: str, title: str, schema_name: str):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                self._set_schema_context(cur, schema_name)

                conv_id = self._get_conversation_id(cur, session_id)
                cur.execute(
                    "UPDATE conversations SET title = %s WHERE id = %s",
                    (title, conv_id),
                )
                conn.commit()
        finally:
            self._put_conn(conn)

    def _get_conversation_id(self, cur, session_id: str) -> Optional[int]:
        """Get conversation_id from session_id, returns None if not found"""
        cur.execute(
            "SELECT id FROM conversations WHERE session_id = %s",
            (session_id,)
        )
        result = cur.fetchone()
        if result:
            return result[0] if isinstance(result, tuple) else result['id']
        return None 

    def delete_session(self, session_id: str, schema_name: str) -> int:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                self._set_schema_context(cur, schema_name)

                conv_id = self._get_conversation_id(cur, session_id)

                cur.execute(
                    "DELETE FROM messages WHERE conversation_id = %s", (conv_id,)
                )
                msg_deleted = cur.rowcount

                cur.execute(
                    "DELETE FROM conversations WHERE session_id = %s", (session_id,)
                )
                conv_deleted = cur.rowcount

                conn.commit()
                return msg_deleted + conv_deleted
        finally:
            self._put_conn(conn)

    def get_pool_stats(self) -> Dict[str, Any]:
        try:
            return {
                "min_connections": self.pool.minconn,
                "max_connections": self.pool.maxconn,
                "available": len(self.pool._pool) if hasattr(self.pool, "_pool") else 0,
                "status": "healthy",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def close(self):
        self.pool.closeall()

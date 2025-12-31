import redis
import hashlib
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password

        pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=100,
            socket_connect_timeout=5,
            socket_timeout=5,
            socket_keepalive=True,
            retry_on_timeout=True,
            health_check_interval=30
        )

        self.client = redis.Redis(connection_pool=pool, decode_responses=True)

        try:
            self.client.ping()
            logger.info(f"Redis connected: {host}:{port}/{db}")
            logger.info(f"Redis pool: max_connections=100, health_check_interval=30s")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise

    def get(self, key: str) -> Optional[str]:
        try:
            return self.client.get(key)
        except Exception:
            return None

    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        try:
            return self.client.setex(key, ttl, value)
        except Exception:
            return False

    def delete(self, key: str) -> int:
        try:
            return self.client.delete(key)
        except Exception:
            return 0

    def hash_key(self, session_id: str, query: str, prefix: str = 'rewrite') -> str:
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()[:8]
        return f"{prefix}:{session_id}:{query_hash}"

    def invalidate_session(self, session_id: str) -> int:
        try:
            pattern = f"rewrite:{session_id}:*"
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception:
            return 0

    def get_stats(self) -> Dict[str, Any]:
        try:
            info = self.client.info()
            pool_stats = self.client.connection_pool.get_connection('_').get_pool_stats() if hasattr(
                self.client.connection_pool, 'get_connection') else {}

            return {
                'connected': True,
                'memory_used': info.get('used_memory_human', '0B'),
                'keys_total': self.client.dbsize(),
                'uptime': info.get('uptime_in_seconds', 0),
                'connections_active': info.get('connected_clients', 0),
                'pool_max': 100
            }
        except Exception:
            return {'connected': False}

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
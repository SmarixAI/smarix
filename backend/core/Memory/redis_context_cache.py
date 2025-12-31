import json
import time
from typing import Optional, Dict, Any

from .redis_client import RedisClient


class RedisContextCache:
    """
    Cache layer for query rewrites and (optionally) session context.
    Used to avoid repeated DB+LLM work for the same (session, query).
    """

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.prefix_rewrite = "rewrite"

    def _rewrite_key(self, session_id: str, query: str) -> str:
        return self.redis.hash_key(session_id, query, prefix=self.prefix_rewrite)

    def get_rewritten_query(self, session_id: str, query: str) -> Optional[str]:
        """
        Return cached rewritten query if present.
        """
        key = self._rewrite_key(session_id, query)
        raw = self.redis.get(key)
        if not raw:
            return None

        try:
            data = json.loads(raw)
        except Exception:
            return None

        return data.get("rewritten")

    def set_rewritten_query(self, session_id: str, query: str, rewritten: str, ttl: int = 3600) -> None:
        """
        Cache a rewritten query for this (session, query).
        """
        key = self._rewrite_key(session_id, query)
        payload: Dict[str, Any] = {
            "original": query,
            "rewritten": rewritten,
            "ts": int(time.time()),
        }
        self.redis.set(key, json.dumps(payload), ttl=ttl)

    def invalidate_session(self, session_id: str) -> int:
        """
        Delete all rewrite cache entries for a session.
        """
        try:
            pattern = f"{self.prefix_rewrite}:{session_id}:*"
            keys = self.redis.client.keys(pattern)
            if not keys:
                return 0
            return self.redis.client.delete(*keys)
        except Exception:
            return 0

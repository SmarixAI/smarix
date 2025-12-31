import json
import time
import hashlib
from typing import Optional, Dict, Any
import logging

from .redis_client import RedisClient

logger = logging.getLogger(__name__)


class RedisResponseCache:
    def __init__(self, redis_client: RedisClient, ttl: int = 3600):
        self.redis = redis_client
        self.ttl = ttl
        self.prefix = "response"

    def _normalize_query(self, query: str) -> str:
        return query.lower().strip()

    def _cache_key(self, query: str, session_id: Optional[str] = None) -> str:
        normalized = self._normalize_query(query)

        if session_id:
            query_hash = hashlib.md5(f"{normalized}:{session_id}".encode()).hexdigest()[:12]
            return f"{self.prefix}:{session_id}:{query_hash}"
        else:
            query_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
            return f"{self.prefix}:global:{query_hash}"

    def get(self, query: str, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        key = self._cache_key(query, session_id)
        raw = self.redis.get(key)

        if not raw:
            return None

        try:
            cached_data = json.loads(raw)
            logger.info(
                f"🎯 RESPONSE CACHE HIT | query='{query[:50]}...', session={session_id[:8] if session_id else 'global'}")

            cached_data['cached'] = True
            cached_data['cache_timestamp'] = cached_data.get('timestamp')

            return cached_data
        except Exception as e:
            logger.error(f"Cache deserialization error: {e}")
            return None

    def set(self, query: str, response: Dict[str, Any], session_id: Optional[str] = None) -> bool:
        key = self._cache_key(query, session_id)

        cache_payload = {
            'query': query,
            'answer': response.get('answer'),
            'sources': response.get('sources', []),
            'chunks_retrieved': response.get('chunks_retrieved', 0),
            'query_type': response.get('query_type'),
            'context_quality': response.get('context_quality', 0.0),
            'emails': response.get('emails', []),
            'has_diagram': response.get('has_diagram', False),
            'flow_data': response.get('flow_data'),
            'related_knowledge': response.get('related_knowledge'),
            'is_metrics_query': response.get('is_metrics_query', False),
            'chronological_entity': response.get('chronological_entity'),
            'timestamp': int(time.time()),
            'session_id': session_id,
            'cached': False
        }

        try:
            self.redis.set(key, json.dumps(cache_payload), ttl=self.ttl)
            logger.info(
                f"💾 RESPONSE CACHED | query='{query[:50]}...', session={session_id[:8] if session_id else 'global'}")
            return True
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            return False

    def invalidate(self, query: str, session_id: Optional[str] = None) -> bool:
        key = self._cache_key(query, session_id)
        deleted = self.redis.delete(key)
        return deleted > 0

    def invalidate_session(self, session_id: str) -> int:
        pattern = f"{self.prefix}:{session_id}:*"
        try:
            keys = self.redis.client.keys(pattern)
            if keys:
                return self.redis.client.delete(*keys)
            return 0
        except Exception:
            return 0

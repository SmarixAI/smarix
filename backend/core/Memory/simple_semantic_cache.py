import json
import time
import hashlib
import numpy as np
from typing import Optional, Dict, Any, Set, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract critical entities from queries"""

    @staticmethod
    def extract_entities(query: str) -> Dict[str, Set[str]]:
        """Extract PR numbers, issue numbers, files, functions, etc."""
        entities = {
            "pr_numbers": set(),
            "issue_numbers": set(),
            "file_paths": set(),
            "function_names": set(),
            "class_names": set(),
            "line_numbers": set(),
            "commit_hashes": set(),
        }

        # PR numbers: PR #123, PR-123, pr123, pull request 123
        # IMPORTANT: do NOT treat bare "#123" as PR.
        pr_patterns = [
            r"\bPR[#\s-]?(\d+)",
            r"\bpr[#\s-]?(\d+)",
            r"\bpull request[#\s-]?(\d+)",
        ]
        for pattern in pr_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entities["pr_numbers"].add(match.group(1))

        # Issue numbers
        issue_patterns = [r"\bissue[#\s-]?(\d+)", r"\bbug[#\s-]?(\d+)"]
        for pattern in issue_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entities["issue_numbers"].add(match.group(1))

        # File paths
        file_patterns = [
            r"[\w/\\]+\.(?:py|js|ts|jsx|tsx|java|cpp|c|h|go|rs|rb|php|css|html|json|yaml|yml|md|txt)",
            r"`([^`]+\.\w+)`",
            r'"([^"]+\.\w+)"',
            r"\'([^\']+\.\w+)\'",
        ]
        for pattern in file_patterns:
            matches = re.finditer(pattern, query)
            for match in matches:
                file_path = match.group(1) if match.lastindex else match.group(0)
                entities["file_paths"].add(file_path.lower())

        # Function names
        function_patterns = [
            r"\bdef\s+(\w+)",
            r"\bfunction\s+(\w+)",
            r"\b([a-z_][a-z0-9_]*)\s*\(",
            r"`([a-z_][a-z0-9_]*)\(\)`",
        ]
        for pattern in function_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                func_name = match.group(1)
                if len(func_name) > 2:
                    entities["function_names"].add(func_name.lower())

        # Class names (CamelCase)
        class_patterns = [
            r"\bclass\s+([A-Z][a-zA-Z0-9]*)",
            r"\b([A-Z][a-z]+[A-Z][a-zA-Z0-9]*)",
            r"`([A-Z][a-zA-Z0-9]+)`",
        ]
        for pattern in class_patterns:
            matches = re.finditer(pattern, query)
            for match in matches:
                class_name = match.group(1)
                if len(class_name) > 2:
                    entities["class_names"].add(class_name)

        # Line numbers
        line_patterns = [r"\bline[s]?\s+(\d+)", r"\bL(\d+)", r":(\d+)"]
        for pattern in line_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entities["line_numbers"].add(match.group(1))

        # Commit hashes (7-40 hex chars)
        commit_pattern = r"\b([a-f0-9]{7,40})\b"
        matches = re.finditer(commit_pattern, query, re.IGNORECASE)
        for match in matches:
            commit_hash = match.group(1)
            if len(commit_hash) >= 7:
                entities["commit_hashes"].add(commit_hash.lower())

        return entities

    @staticmethod
    def entities_match(
        entities1: Dict[str, Set[str]], entities2: Dict[str, Set[str]]
    ) -> Tuple[bool, float]:
        """
        Check if entities match
        Returns (match_bool, penalty_score)
        - 1.0 = perfect match or no entities
        - 0.5 = partial match
        - 0.0 = complete mismatch (reject)
        """

        critical_types = ["pr_numbers", "issue_numbers", "commit_hashes"]
        important_types = ["file_paths", "function_names", "class_names"]

        critical_mismatch = False
        important_mismatch = False

        has_critical_entities = False
        has_important_entities = False

        # Critical entities must match exactly
        for entity_type in critical_types:
            set1 = entities1.get(entity_type, set())
            set2 = entities2.get(entity_type, set())

            if set1 or set2:
                has_critical_entities = True
                if set1 != set2:
                    critical_mismatch = True
                    logger.debug(f"ENTITY MISMATCH | {entity_type}: {set1} vs {set2}")

        # Important entities should overlap reasonably
        for entity_type in important_types:
            set1 = entities1.get(entity_type, set())
            set2 = entities2.get(entity_type, set())

            if set1 or set2:
                has_important_entities = True
                if set1 and set2:
                    overlap = len(set1 & set2) / len(set1 | set2)
                    if overlap < 0.5:
                        important_mismatch = True
                elif set1 != set2:
                    important_mismatch = True

        if critical_mismatch:
            return False, 0.0

        if important_mismatch:
            return False, 0.5

        if has_critical_entities or has_important_entities:
            return True, 1.0

        return True, 1.0


class SimpleSemanticCache:

    def __init__(
        self,
        redis_client,
        embedding_function,
        dimension: int = 1536,
        exact_threshold: float = 0.98,
        high_threshold: float = 0.92,
        medium_threshold: float = 0.82,
        low_threshold: float = 0.72,
        ttl: int = 604800,
        max_cache_size: int = 10000,
        cache_failures: bool = False,  # NEW: do not reuse failure responses semantically
    ):
        self.redis = redis_client
        self.embedding_function = embedding_function
        self.dimension = dimension

        self.exact_threshold = exact_threshold
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.low_threshold = low_threshold

        self.ttl = ttl
        self.max_cache_size = max_cache_size
        self.cache_failures = cache_failures

        self.cache_index: Dict[str, Dict[str, Any]] = {}

        self.stats = {
            "total_queries": 0,
            "exact_matches": 0,
            "high_matches": 0,
            "medium_matches": 0,
            "low_matches": 0,
            "no_matches": 0,
            "entity_rejections": 0,
            "cost_saved_usd": 0.0,
        }

        logger.info("Simple Semantic Cache initialized (Entity-Aware)")
        logger.info(
            f"Thresholds: Exact >={exact_threshold * 100:.0f}%, "
            f"High >={high_threshold * 100:.0f}%, "
            f"Medium >={medium_threshold * 100:.0f}%, "
            f"Low >={low_threshold * 100:.0f}%"
        )

    @staticmethod
    def _is_failure_response(response: Dict[str, Any]) -> bool:
        """
        Detect responses that should not be reused semantically:
        - no context found
        - explicit error flag
        - empty/None payload
        """
        if not response:
            return True
        if response.get("error"):
            return True
        msg = (response.get("answer") or response.get("message") or "").lower()
        if "no context" in msg or "no relevant context" in msg:
            return True
        return False

    def _query_hash(self, query: str) -> str:
        return hashlib.sha256(query.lower().encode()).hexdigest()[:16]

    def _redis_key(self, session_id: str, query_hash: str) -> str:
        return f"simple:cache:{session_id}:{query_hash}"

    def get(self, query: str, session_id: str) -> Optional[Dict[str, Any]]:
        start_time = time.time()
        self.stats["total_queries"] += 1

        logger.info(f"[DEBUG] SimpleSemanticCache.get() called | query='{query[:40]}' | session={session_id[:8]} | cache_size={len(self.cache_index)}")

        try:
            query_embedding = self.embedding_function(query)
            query_entities = EntityExtractor.extract_entities(query)

            is_pr_issue_query = bool(
                query_entities.get("pr_numbers") or query_entities.get("issue_numbers")
            )
            logger.debug(f"PR/ISSUE QUERY? {is_pr_issue_query} | pr_numbers={query_entities.get('pr_numbers')}")

            best_match_key = None
            best_similarity = 0.0
            best_cache_data = None
            best_entity_penalty = 1.0

            for cache_key, cache_data in self.cache_index.items():
                if not cache_key.startswith(f"{session_id}:"):
                    continue

                cached_query = cache_data["query"]
                cached_entities = EntityExtractor.extract_entities(cached_query)

                entities_match, entity_penalty = EntityExtractor.entities_match(
                    query_entities, cached_entities
                )

                if entity_penalty == 0.0:
                    logger.debug(
                        f"ENTITY REJECTION | '{query[:40]}' vs '{cached_query[:40]}' | "
                        f"query_entities={query_entities.get('pr_numbers', set())} | "
                        f"cached_entities={cached_entities.get('pr_numbers', set())}"
                    )
                    self.stats["entity_rejections"] += 1
                    continue

                cached_embedding = np.array(cache_data["embedding"])
                similarity = self._cosine_similarity(query_embedding, cached_embedding)

                adjusted_similarity = similarity * entity_penalty

                if adjusted_similarity > best_similarity:
                    best_similarity = adjusted_similarity
                    best_match_key = cache_key
                    best_cache_data = cache_data
                    best_entity_penalty = entity_penalty

            if not best_match_key or best_similarity < self.low_threshold:
                elapsed_ms = (time.time() - start_time) * 1000
                self.stats["no_matches"] += 1
                logger.info(
                    f"NO MATCH | query='{query[:60]}...' | "
                    f"best_sim={best_similarity:.3f} | time={elapsed_ms:.1f}ms"
                )
                return None

            age_hours = (time.time() - best_cache_data["timestamp"]) / 3600
            freshness_factor = np.exp(-age_hours / 24.0)

            quality_score = best_cache_data.get("quality_score", 0.8)
            quality_factor = 0.5 + 0.5 * max(0.0, min(1.0, quality_score))

            confidence = (
                best_similarity * quality_factor * (0.85 + 0.15 * freshness_factor)
            )

            elapsed_ms = (time.time() - start_time) * 1000

            if confidence >= self.exact_threshold:
                match_level = "exact"
                self.stats["exact_matches"] += 1
            elif confidence >= self.high_threshold:
                match_level = "high"
                self.stats["high_matches"] += 1
            elif confidence >= self.medium_threshold:
                match_level = "medium"
                self.stats["medium_matches"] += 1
            else:
                match_level = "low"
                self.stats["low_matches"] += 1

            is_failure = self._is_failure_response(best_cache_data["response"])

            logger.info(
                f"SEMANTIC CACHE HIT | query='{query[:60]}...' | "
                f"matched='{best_cache_data['query'][:60]}...' | "
                f"similarity={best_similarity:.3f} | "
                f"confidence={confidence:.3f} | "
                f"level={match_level} | "
                f"entity_penalty={best_entity_penalty:.2f} | "
                f"is_pr_issue={is_pr_issue_query} | "  # NEW
                f"age={age_hours:.1f}h | "
                f"is_failure={is_failure} | "
                f"time={elapsed_ms:.1f}ms"
            )

            # Do not reuse failure responses semantically
            if is_failure and not self.cache_failures:
                self.stats["no_matches"] += 1
                logger.info(
                    f"SKIP FAILURE RESPONSE | query='{query[:60]}...' | "
                    f"matched='{best_cache_data['query'][:60]}...'"
                )
                return None

            if confidence >= self.high_threshold:
                # STRICTER: PR/issue queries with DIFFERENT intent need near-exact match
                # But if entities match perfectly AND similarity is high, it's safe to return cached
                if is_pr_issue_query:
                    # Check if this is just formatting difference (e.g., "PR #1" vs "PR 1")
                    # If entities match AND confidence >= 0.85, treat as same query
                    if entities_match and confidence >= 0.85:
                        # Same PR/issue, similar wording -> safe to cache
                        result = best_cache_data["response"].copy()
                        result["cached"] = True
                        result["cache_confidence"] = confidence
                        result["cache_tier"] = match_level
                        self._update_cost_savings(best_cache_data["response"])
                        logger.info(
                            f"PR/ISSUE ENTITY MATCH | same entity + high similarity | "
                            f"returning cached | confidence={confidence:.3f}"
                        )
                        return result
                    elif confidence < 0.95:
                        # Different intent (e.g., "What is PR #1?" vs "Why was PR #1 created?")
                        logger.info(
                            f"PR/ISSUE STRICT | confidence={confidence:.3f} < 0.95 | "
                            f"forcing generation | query='{query[:60]}...'"
                        )
                        return {
                            "_requires_generation": True,
                            "_context_hints": best_cache_data["response"],
                            "_original_query": query,
                            "_confidence": confidence,
                            "_reason": "pr_issue_strict",
                        }

            elif confidence >= self.medium_threshold:
                self._update_cost_savings(best_cache_data["response"])
                if age_hours > 1.0:
                    return {
                        "_requires_augmentation": True,
                        "_cached_response": best_cache_data["response"],
                        "_original_query": query,
                        "_cached_query": best_cache_data["query"],
                        "_confidence": confidence,
                    }
                else:
                    result = best_cache_data["response"].copy()
                    result["cached"] = True
                    result["cache_confidence"] = confidence
                    return result

            else:
                # Low confidence: use only as weak context hint
                return {
                    "_requires_generation": True,
                    "_context_hints": best_cache_data["response"],
                    "_original_query": query,
                    "_confidence": confidence,
                }

        except Exception as e:
            logger.error(f"Cache lookup error: {e}")
            return None

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def set(
        self,
        query: str,
        response: Dict[str, Any],
        session_id: str,
        quality_score: float = 0.8,
    ) -> bool:
        try:
            query_hash = self._query_hash(query)
            query_embedding = self.embedding_function(query)
            embedding_list = (
                query_embedding.tolist()
                if hasattr(query_embedding, "tolist")
                else list(query_embedding)
            )

            redis_key = self._redis_key(session_id, query_hash)
            self.redis.set(redis_key, json.dumps(response), ttl=self.ttl)

            is_failure = self._is_failure_response(response)

            if is_failure and not self.cache_failures:
                logger.info(f"NOT INDEXING FAILURE RESPONSE | query='{query[:60]}...'")
            else:
                cache_key = f"{session_id}:{query_hash}"
                self.cache_index[cache_key] = {
                    "query": query,
                    "embedding": embedding_list,
                    "response": response,
                    "timestamp": time.time(),
                    "quality_score": quality_score,
                    "access_count": 0,
                }

                if len(self.cache_index) > self.max_cache_size:
                    self._cleanup_old_entries()

                logger.info(
                    f"[DEBUG] CACHED | query='{query[:60]}...' | "
                    f"session={session_id[:8]} | "
                    f"index_size={len(self.cache_index)} | is_failure={is_failure}"
                )

            return True

        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            return False

    def _cleanup_old_entries(self):
        to_remove = int(len(self.cache_index) * 0.1)
        if to_remove <= 0:
            return

        sorted_entries = sorted(
            self.cache_index.items(), key=lambda x: x[1]["timestamp"]
        )

        for key, _ in sorted_entries[:to_remove]:
            del self.cache_index[key]

        logger.info(f"Cleaned up {to_remove} old entries")

    def _update_cost_savings(self, response: Dict[str, Any]):
        chunks = response.get("chunks_retrieved", 5)
        tokens = chunks * 200
        cost = (tokens / 1000) * 0.002
        self.stats["cost_saved_usd"] += cost

    def update_ages(self):
        # Optional: implement if you want external age management
        pass

    def invalidate_session(self, session_id: str) -> int:
        count = 0

        try:
            pattern = f"simple:cache:{session_id}:*"
            keys = self.redis.client.keys(pattern)
            if keys:
                count += self.redis.client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis invalidation error: {e}")

        to_delete = [
            k for k in self.cache_index.keys() if k.startswith(f"{session_id}:")
        ]
        for key in to_delete:
            del self.cache_index[key]
            count += 1

        logger.info(f"Invalidated {count} entries for session {session_id[:8]}...")
        return count

    def get_stats(self) -> Dict[str, Any]:
        total = self.stats["total_queries"]

        if total > 0:
            exact_rate = (self.stats["exact_matches"] / total) * 100
            high_rate = (self.stats["high_matches"] / total) * 100
            medium_rate = (self.stats["medium_matches"] / total) * 100
            low_rate = (self.stats["low_matches"] / total) * 100
            miss_rate = (self.stats["no_matches"] / total) * 100
            rejection_rate = (self.stats["entity_rejections"] / total) * 100

            total_hits = total - self.stats["no_matches"]
            overall_hit_rate = (total_hits / total) * 100
        else:
            exact_rate = high_rate = medium_rate = low_rate = miss_rate = (
                rejection_rate
            ) = overall_hit_rate = 0.0

        return {
            "total_queries": total,
            "overall_hit_rate": round(overall_hit_rate, 2),
            "entity_rejections": self.stats["entity_rejections"],
            "entity_rejection_rate": round(rejection_rate, 2),
            "confidence_levels": {
                "exact": {
                    "count": self.stats["exact_matches"],
                    "rate": round(exact_rate, 2),
                },
                "high": {
                    "count": self.stats["high_matches"],
                    "rate": round(high_rate, 2),
                },
                "medium": {
                    "count": self.stats["medium_matches"],
                    "rate": round(medium_rate, 2),
                },
                "low": {"count": self.stats["low_matches"], "rate": round(low_rate, 2)},
                "no_match": {
                    "count": self.stats["no_matches"],
                    "rate": round(miss_rate, 2),
                },
            },
            "cache_size": len(self.cache_index),
            "cost_saved_usd": round(self.stats["cost_saved_usd"], 4),
            "llm_calls_avoided": total - self.stats["no_matches"],
        }

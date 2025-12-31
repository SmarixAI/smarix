"""
Semantic Cache with Entity-Aware Matching
Prevents false matches when critical entities differ (PR numbers, files, etc.)
"""

import json
import time
import hashlib
import numpy as np
from typing import Optional, Dict, Any, List, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Universal confidence levels"""
    EXACT = "exact"
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class CacheStrategy(Enum):
    """How to use cached result"""
    RETURN_AS_IS = "return_as_is"
    RETURN_IF_FRESH = "return_if_fresh"
    AUGMENT = "augment"
    USE_AS_CONTEXT = "use_as_context"
    IGNORE = "ignore"


@dataclass
class CacheMatch:
    """Represents a semantic cache match"""
    original_query: str
    cached_query: str
    cached_response: Dict[str, Any]

    embedding_similarity: float
    overall_confidence: float
    confidence_level: ConfidenceLevel
    strategy: CacheStrategy

    semantic_score: float
    intent_score: float
    topic_score: float
    context_score: float
    freshness_score: float

    age_hours: float
    access_count: int
    quality_score: float

    entities_match: bool  # NEW: Track if entities match
    entity_penalty: float  # NEW: Penalty applied for entity mismatch

    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_query': self.original_query,
            'cached_query': self.cached_query,
            'embedding_similarity': round(self.embedding_similarity, 4),
            'overall_confidence': round(self.overall_confidence, 4),
            'confidence_level': self.confidence_level.value,
            'strategy': self.strategy.value,
            'age_hours': round(self.age_hours, 2),
            'entities_match': self.entities_match,
            'entity_penalty': round(self.entity_penalty, 4),
            'detailed_scores': {
                'semantic': round(self.semantic_score, 4),
                'intent': round(self.intent_score, 4),
                'topic': round(self.topic_score, 4),
                'context': round(self.context_score, 4),
                'freshness': round(self.freshness_score, 4)
            }
        }


class EntityExtractor:
    """
    Extract critical entities that make queries fundamentally different
    """

    @staticmethod
    def extract_entities(query: str) -> Dict[str, Set[str]]:
        """
        Extract all critical entities from query
        """
        entities = {
            'pr_numbers': set(),
            'issue_numbers': set(),
            'file_paths': set(),
            'function_names': set(),
            'class_names': set(),
            'variable_names': set(),
            'line_numbers': set(),
            'commit_hashes': set()
        }

        # PR numbers: #123, PR #123, PR-123, pr123
        pr_patterns = [
            r'#(\d+)',
            r'\bPR[#\s-]?(\d+)',
            r'\bpr[#\s-]?(\d+)',
            r'\bpull request[#\s-]?(\d+)'
        ]
        for pattern in pr_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entities['pr_numbers'].add(match.group(1))

        # Issue numbers: issue #123, issue-123
        issue_patterns = [
            r'\bissue[#\s-]?(\d+)',
            r'\bbug[#\s-]?(\d+)'
        ]
        for pattern in issue_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entities['issue_numbers'].add(match.group(1))

        # File paths: src/main.py, /path/to/file.js, file.py
        file_patterns = [
            r'[\w/\\]+\.(?:py|js|ts|jsx|tsx|java|cpp|c|h|go|rs|rb|php|css|html|json|yaml|yml|md|txt)',
            r'`([^`]+\.\w+)`',
            r'"([^"]+\.\w+)"',
            r'\'([^\']+\.\w+)\''
        ]
        for pattern in file_patterns:
            matches = re.finditer(pattern, query)
            for match in matches:
                file_path = match.group(1) if match.lastindex else match.group(0)
                entities['file_paths'].add(file_path.lower())

        # Function names: def function(), function(), functionName()
        function_patterns = [
            r'\bdef\s+(\w+)',
            r'\bfunction\s+(\w+)',
            r'\b([a-z_][a-z0-9_]*)\s*\(',
            r'`([a-z_][a-z0-9_]*)\(\)`'
        ]
        for pattern in function_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                func_name = match.group(1)
                if len(func_name) > 2:  # Filter out "if", "or", etc.
                    entities['function_names'].add(func_name.lower())

        # Class names: class ClassName, ClassName class
        class_patterns = [
            r'\bclass\s+([A-Z][a-zA-Z0-9]*)',
            r'\b([A-Z][a-z]+[A-Z][a-zA-Z0-9]*)',  # CamelCase
            r'`([A-Z][a-zA-Z0-9]+)`'
        ]
        for pattern in class_patterns:
            matches = re.finditer(pattern, query)
            for match in matches:
                class_name = match.group(1)
                if len(class_name) > 2:
                    entities['class_names'].add(class_name)

        # Variable names in backticks or quotes
        var_patterns = [
            r'`([a-z_][a-z0-9_]+)`',
            r'variable\s+["\']?(\w+)["\']?'
        ]
        for pattern in var_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                var_name = match.group(1)
                if len(var_name) > 2:
                    entities['variable_names'].add(var_name.lower())

        # Line numbers: line 123, L123, :123
        line_patterns = [
            r'\bline[s]?\s+(\d+)',
            r'\bL(\d+)',
            r':(\d+)'
        ]
        for pattern in line_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entities['line_numbers'].add(match.group(1))

        # Commit hashes: 7-40 hex characters
        commit_pattern = r'\b([a-f0-9]{7,40})\b'
        matches = re.finditer(commit_pattern, query, re.IGNORECASE)
        for match in matches:
            commit_hash = match.group(1)
            if len(commit_hash) >= 7:
                entities['commit_hashes'].add(commit_hash.lower())

        return entities

    @staticmethod
    def entities_match(entities1: Dict[str, Set[str]], entities2: Dict[str, Set[str]]) -> Tuple[bool, float]:
        """
        Check if critical entities match between two queries
        Returns (match_bool, penalty_score)

        penalty_score:
        - 1.0 = perfect match or no entities
        - 0.5 = partial match (some entities match, some don't)
        - 0.0 = complete mismatch (different entities)
        """

        # Critical entity types (must match exactly)
        critical_types = ['pr_numbers', 'issue_numbers', 'commit_hashes']

        # Important entity types (should match, but not critical)
        important_types = ['file_paths', 'function_names', 'class_names']

        critical_mismatch = False
        important_mismatch = False

        has_critical_entities = False
        has_important_entities = False

        # Check critical entities
        for entity_type in critical_types:
            set1 = entities1.get(entity_type, set())
            set2 = entities2.get(entity_type, set())

            if set1 or set2:
                has_critical_entities = True

                # If one has entities and other doesn't, or they're different
                if set1 != set2:
                    critical_mismatch = True
                    logger.debug(f"ENTITY MISMATCH | {entity_type}: {set1} vs {set2}")

        # Check important entities
        for entity_type in important_types:
            set1 = entities1.get(entity_type, set())
            set2 = entities2.get(entity_type, set())

            if set1 or set2:
                has_important_entities = True

                # Calculate overlap
                if set1 and set2:
                    overlap = len(set1 & set2) / len(set1 | set2)
                    if overlap < 0.5:
                        important_mismatch = True
                elif set1 != set2:
                    important_mismatch = True

        # Determine penalty
        if critical_mismatch:
            # Critical entity mismatch = 0% confidence (reject)
            return False, 0.0

        if important_mismatch:
            # Important entity mismatch = 50% penalty
            return False, 0.5

        if has_critical_entities or has_important_entities:
            # Has entities and they all match = 100%
            return True, 1.0

        # No entities at all = 100% (generic query)
        return True, 1.0


class UniversalConfidenceScorer:
    """
    Generic confidence scoring with entity awareness
    """

    @staticmethod
    def detect_volatility(query: str) -> str:
        """Detect if query asks for time-sensitive information"""
        high_volatility_keywords = [
            'latest', 'current', 'recent', 'now', 'today', 'newest',
            'last', 'updated', 'changed', 'new'
        ]

        low_volatility_keywords = [
            'explain', 'what is', 'how to', 'concept', 'theory',
            'architecture', 'design', 'pattern', 'principle'
        ]

        q_lower = query.lower()

        if any(kw in q_lower for kw in high_volatility_keywords):
            return 'high'
        elif any(kw in q_lower for kw in low_volatility_keywords):
            return 'low'
        else:
            return 'medium'

    @staticmethod
    def calculate_freshness_score(age_hours: float, query_volatility: str = 'medium') -> float:
        """Freshness score based on cache age"""
        if query_volatility == 'high':
            half_life = 1.0
        elif query_volatility == 'low':
            half_life = 168.0
        else:
            half_life = 24.0

        freshness = np.exp(-age_hours / half_life)
        return freshness

    @classmethod
    def calculate_overall_confidence(
            cls,
            query1: str,
            query2: str,
            embedding_similarity: float,
            age_hours: float,
            quality_score: float,
            entity_penalty: float = 1.0  # NEW: Entity penalty
    ) -> Tuple[float, Dict[str, float]]:
        """
        Simplified confidence with entity awareness
        """

        volatility = cls.detect_volatility(query1)
        freshness_score = cls.calculate_freshness_score(age_hours, volatility)

        # Apply entity penalty BEFORE calculating confidence
        adjusted_similarity = embedding_similarity * entity_penalty

        overall = adjusted_similarity * (0.90 + 0.10 * freshness_score)

        breakdown = {
            'semantic': adjusted_similarity,
            'intent': adjusted_similarity,
            'topic': adjusted_similarity,
            'context': adjusted_similarity,
            'freshness': freshness_score
        }

        return overall, breakdown


class UniversalSemanticCache:
    """
    Universal semantic cache with entity-aware matching
    """

    def __init__(
            self,
            redis_client,
            embedding_function,
            dimension: int = 1536,
            very_high_threshold: float = 0.95,
            high_threshold: float = 0.90,
            medium_threshold: float = 0.80,
            low_threshold: float = 0.70,
            fresh_hours: float = 1.0,
            acceptable_hours: float = 24.0,
            stale_hours: float = 168.0,
            ttl: int = 604800,
            max_cache_size: int = 10000,
            enable_augmentation: bool = True,
            enable_context_hints: bool = True,
    ):
        self.redis = redis_client
        self.embedding_function = embedding_function
        self.dimension = dimension

        self.very_high_threshold = very_high_threshold
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.low_threshold = low_threshold

        self.fresh_hours = fresh_hours
        self.acceptable_hours = acceptable_hours
        self.stale_hours = stale_hours

        self.ttl = ttl
        self.max_cache_size = max_cache_size
        self.enable_augmentation = enable_augmentation
        self.enable_context_hints = enable_context_hints

        self.cache_index: Dict[str, Dict[str, Any]] = {}

        self.stats = {
            'total_queries': 0,
            'exact_matches': 0,
            'very_high_matches': 0,
            'high_matches': 0,
            'medium_matches': 0,
            'low_matches': 0,
            'no_matches': 0,
            'entity_rejections': 0,  # NEW
            'augmentations': 0,
            'context_hints': 0,
            'cost_saved_usd': 0.0,
        }

        logger.info("🌐 Universal Semantic Cache initialized (Entity-Aware)")
        logger.info(f"   Very High: ≥{very_high_threshold * 100}%")
        logger.info(f"   High: {high_threshold * 100}-{very_high_threshold * 100}%")
        logger.info(f"   Medium: {medium_threshold * 100}-{high_threshold * 100}%")
        logger.info(f"   Low: {low_threshold * 100}-{medium_threshold * 100}%")

    def _normalize_query(self, query: str) -> str:
        return query.strip()

    def _query_hash(self, query: str) -> str:
        normalized = self._normalize_query(query).lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _redis_key(self, session_id: str, query_hash: str) -> str:
        return f"universal:cache:{session_id}:{query_hash}"

    def get(self, query: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Cache lookup with entity-aware matching
        """
        start_time = time.time()
        self.stats['total_queries'] += 1

        query_normalized = self._normalize_query(query)
        query_hash = self._query_hash(query)

        # Extract entities from current query
        query_entities = EntityExtractor.extract_entities(query)

        # === EXACT MATCH ===
        exact_match = self._check_exact_match(query_hash, session_id)
        if exact_match:
            elapsed_ms = (time.time() - start_time) * 1000
            self.stats['exact_matches'] += 1
            self._update_cost_savings(exact_match)

            logger.info(
                f"⚡ EXACT MATCH | query='{query[:60]}...' | "
                f"time={elapsed_ms:.1f}ms"
            )

            result = exact_match.copy()
            result['cached'] = True
            result['cache_confidence'] = 1.0
            result['cache_tier'] = 'exact'
            return result

        # === SEMANTIC MATCHING ===
        try:
            query_embedding = self.embedding_function(query)

            best_match = self._find_best_match(
                query, query_embedding, query_entities, session_id
            )

            if not best_match:
                elapsed_ms = (time.time() - start_time) * 1000
                self.stats['no_matches'] += 1
                logger.info(f"❌ NO MATCH | query='{query[:60]}...' | time={elapsed_ms:.1f}ms")
                return None

            # Decide strategy
            strategy = self._decide_strategy(best_match)
            best_match.strategy = strategy

            elapsed_ms = (time.time() - start_time) * 1000

            self._update_stats_by_level(best_match.confidence_level)
            self._update_cost_savings(best_match.cached_response)

            logger.info(
                f"✅ SEMANTIC CACHE HIT | query='{query[:60]}...' | "
                f"matched='{best_match.cached_query[:60]}...' | "
                f"confidence={best_match.overall_confidence} | "
                f"tier={best_match.confidence_level.value} | "
                f"entities_match={best_match.entities_match} | "
                f"time={elapsed_ms:.1f}ms"
            )

            # Execute strategy
            if strategy == CacheStrategy.RETURN_AS_IS:
                result = best_match.cached_response.copy()
                result['cached'] = True
                result['cache_confidence'] = best_match.overall_confidence
                result['cache_match_details'] = best_match.to_dict()
                return result

            elif strategy == CacheStrategy.RETURN_IF_FRESH:
                result = best_match.cached_response.copy()
                result['cached'] = True
                result['cache_confidence'] = best_match.overall_confidence
                result['cache_match_details'] = best_match.to_dict()
                result['cache_age_hours'] = best_match.age_hours
                return result

            elif strategy == CacheStrategy.AUGMENT:
                self.stats['augmentations'] += 1
                return {
                    '_requires_augmentation': True,
                    '_cached_response': best_match.cached_response,
                    '_original_query': query,
                    '_cached_query': best_match.cached_query,
                    '_match_details': best_match.to_dict()
                }

            elif strategy == CacheStrategy.USE_AS_CONTEXT:
                self.stats['context_hints'] += 1
                return {
                    '_requires_generation': True,
                    '_context_hints': best_match.cached_response,
                    '_original_query': query,
                    '_match_details': best_match.to_dict()
                }

            else:
                return None

        except Exception as e:
            logger.error(f"Cache lookup error: {e}")
            return None

    def _check_exact_match(
            self, query_hash: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        redis_key = self._redis_key(session_id, query_hash)
        cached_data = self.redis.get(redis_key)

        if cached_data:
            try:
                return json.loads(cached_data)
            except:
                return None

        return None

    def _find_best_match(
            self,
            query: str,
            embedding: np.ndarray,
            query_entities: Dict[str, Set[str]],
            session_id: str
    ) -> Optional[CacheMatch]:
        """
        Find best semantic match with entity awareness
        """

        best_match = None
        best_confidence = 0.0

        for cache_key, cache_data in self.cache_index.items():
            if not cache_key.startswith(f"{session_id}:"):
                continue

            # Extract entities from cached query
            cached_query = cache_data['query']
            cached_entities = EntityExtractor.extract_entities(cached_query)

            # Check entity match FIRST
            entities_match, entity_penalty = EntityExtractor.entities_match(
                query_entities, cached_entities
            )

            # If critical entities don't match, skip this cache entry
            if entity_penalty == 0.0:
                logger.debug(
                    f"ENTITY REJECTION | '{query[:40]}' vs '{cached_query[:40]}' | "
                    f"query_entities={query_entities.get('pr_numbers', set())} | "
                    f"cached_entities={cached_entities.get('pr_numbers', set())}"
                )
                self.stats['entity_rejections'] += 1
                continue

            # Calculate embedding similarity
            cached_embedding = np.array(cache_data['embedding'])
            embedding_sim = self._cosine_similarity(embedding, cached_embedding)

            if embedding_sim < self.low_threshold:
                continue

            # Calculate confidence with entity penalty
            overall_conf, breakdown = UniversalConfidenceScorer.calculate_overall_confidence(
                query1=query,
                query2=cached_query,
                embedding_similarity=embedding_sim,
                age_hours=cache_data['age_hours'],
                quality_score=cache_data.get('quality_score', 0.8),
                entity_penalty=entity_penalty
            )

            if overall_conf > best_confidence:
                best_confidence = overall_conf

                if overall_conf >= self.very_high_threshold:
                    conf_level = ConfidenceLevel.VERY_HIGH
                elif overall_conf >= self.high_threshold:
                    conf_level = ConfidenceLevel.HIGH
                elif overall_conf >= self.medium_threshold:
                    conf_level = ConfidenceLevel.MEDIUM
                elif overall_conf >= self.low_threshold:
                    conf_level = ConfidenceLevel.LOW
                else:
                    conf_level = ConfidenceLevel.NONE

                best_match = CacheMatch(
                    original_query=query,
                    cached_query=cached_query,
                    cached_response=cache_data['response'],
                    embedding_similarity=embedding_sim,
                    overall_confidence=overall_conf,
                    confidence_level=conf_level,
                    strategy=CacheStrategy.RETURN_AS_IS,
                    semantic_score=breakdown['semantic'],
                    intent_score=breakdown['intent'],
                    topic_score=breakdown['topic'],
                    context_score=breakdown['context'],
                    freshness_score=breakdown['freshness'],
                    age_hours=cache_data['age_hours'],
                    access_count=cache_data.get('access_count', 0),
                    quality_score=cache_data.get('quality_score', 0.8),
                    entities_match=entities_match,
                    entity_penalty=entity_penalty
                )

        return best_match

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def _decide_strategy(self, match: CacheMatch) -> CacheStrategy:
        conf_level = match.confidence_level
        age = match.age_hours

        if conf_level == ConfidenceLevel.VERY_HIGH:
            if age <= self.fresh_hours:
                return CacheStrategy.RETURN_AS_IS
            elif age <= self.acceptable_hours:
                return CacheStrategy.RETURN_IF_FRESH
            elif age <= self.stale_hours:
                return CacheStrategy.AUGMENT if self.enable_augmentation else CacheStrategy.USE_AS_CONTEXT
            else:
                return CacheStrategy.IGNORE

        elif conf_level == ConfidenceLevel.HIGH:
            if age <= self.fresh_hours:
                return CacheStrategy.RETURN_AS_IS
            elif age <= self.acceptable_hours:
                return CacheStrategy.RETURN_IF_FRESH
            else:
                return CacheStrategy.AUGMENT if self.enable_augmentation else CacheStrategy.IGNORE

        elif conf_level == ConfidenceLevel.MEDIUM:
            if age <= self.fresh_hours:
                return CacheStrategy.RETURN_IF_FRESH
            else:
                return CacheStrategy.AUGMENT if self.enable_augmentation else CacheStrategy.USE_AS_CONTEXT

        elif conf_level == ConfidenceLevel.LOW:
            if self.enable_context_hints:
                return CacheStrategy.USE_AS_CONTEXT
            else:
                return CacheStrategy.IGNORE

        else:
            return CacheStrategy.IGNORE

    def _update_stats_by_level(self, level: ConfidenceLevel):
        if level == ConfidenceLevel.VERY_HIGH:
            self.stats['very_high_matches'] += 1
        elif level == ConfidenceLevel.HIGH:
            self.stats['high_matches'] += 1
        elif level == ConfidenceLevel.MEDIUM:
            self.stats['medium_matches'] += 1
        elif level == ConfidenceLevel.LOW:
            self.stats['low_matches'] += 1

    def _update_cost_savings(self, response: Dict[str, Any]):
        chunks = response.get('chunks_retrieved', 5)
        tokens = chunks * 200
        cost = (tokens / 1000) * 0.002
        self.stats['cost_saved_usd'] += cost

    def set(
            self,
            query: str,
            response: Dict[str, Any],
            session_id: str,
            quality_score: float = 0.8
    ) -> bool:
        try:
            query_normalized = self._normalize_query(query)
            query_hash = self._query_hash(query)

            query_embedding = self.embedding_function(query)
            embedding_list = query_embedding.tolist() if hasattr(query_embedding, 'tolist') else list(query_embedding)

            redis_key = self._redis_key(session_id, query_hash)
            self.redis.set(redis_key, json.dumps(response), ttl=self.ttl)

            cache_key = f"{session_id}:{query_hash}"
            self.cache_index[cache_key] = {
                'query': query,
                'embedding': embedding_list,
                'response': response,
                'timestamp': time.time(),
                'age_hours': 0.0,
                'quality_score': quality_score,
                'access_count': 0
            }

            if len(self.cache_index) > self.max_cache_size:
                self._cleanup_old_entries()

            logger.info(f"💾 CACHED | query='{query[:60]}...' | index_size={len(self.cache_index)}")

            return True

        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            return False

    def _cleanup_old_entries(self):
        to_remove = int(len(self.cache_index) * 0.1)

        sorted_entries = sorted(
            self.cache_index.items(),
            key=lambda x: x[1]['timestamp']
        )

        for key, _ in sorted_entries[:to_remove]:
            del self.cache_index[key]

        logger.info(f"🗑️ Cleaned up {to_remove} old entries")

    def update_ages(self):
        current_time = time.time()
        for cache_data in self.cache_index.values():
            age_seconds = current_time - cache_data['timestamp']
            cache_data['age_hours'] = age_seconds / 3600

    def invalidate_session(self, session_id: str) -> int:
        count = 0

        try:
            pattern = f"universal:cache:{session_id}:*"
            keys = self.redis.client.keys(pattern)
            if keys:
                count += self.redis.client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis invalidation error: {e}")

        to_delete = [k for k in self.cache_index.keys() if k.startswith(f"{session_id}:")]
        for key in to_delete:
            del self.cache_index[key]
            count += 1

        logger.info(f"🗑️ Invalidated {count} entries for session {session_id[:8]}...")
        return count

    def get_stats(self) -> Dict[str, Any]:
        total = self.stats['total_queries']

        if total > 0:
            exact_rate = (self.stats['exact_matches'] / total) * 100
            very_high_rate = (self.stats['very_high_matches'] / total) * 100
            high_rate = (self.stats['high_matches'] / total) * 100
            medium_rate = (self.stats['medium_matches'] / total) * 100
            low_rate = (self.stats['low_matches'] / total) * 100
            miss_rate = (self.stats['no_matches'] / total) * 100
            rejection_rate = (self.stats['entity_rejections'] / total) * 100

            total_hits = total - self.stats['no_matches']
            overall_hit_rate = (total_hits / total) * 100
        else:
            exact_rate = very_high_rate = high_rate = medium_rate = low_rate = miss_rate = rejection_rate = overall_hit_rate = 0.0

        return {
            'total_queries': total,
            'overall_hit_rate': round(overall_hit_rate, 2),
            'entity_rejections': self.stats['entity_rejections'],
            'entity_rejection_rate': round(rejection_rate, 2),
            'confidence_levels': {
                'exact': {'count': self.stats['exact_matches'], 'rate': round(exact_rate, 2)},
                'very_high': {'count': self.stats['very_high_matches'], 'rate': round(very_high_rate, 2)},
                'high': {'count': self.stats['high_matches'], 'rate': round(high_rate, 2)},
                'medium': {'count': self.stats['medium_matches'], 'rate': round(medium_rate, 2)},
                'low': {'count': self.stats['low_matches'], 'rate': round(low_rate, 2)},
                'no_match': {'count': self.stats['no_matches'], 'rate': round(miss_rate, 2)}
            },
            'strategies_used': {
                'augmentations': self.stats['augmentations'],
                'context_hints': self.stats['context_hints']
            },
            'cache_size': len(self.cache_index),
            'cost_saved_usd': round(self.stats['cost_saved_usd'], 4),
            'llm_calls_avoided': total - self.stats['no_matches']
        }
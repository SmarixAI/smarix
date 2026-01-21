"""
Query routing logic for multi-index retrieval.
"""
from typing import List, Tuple
from ..query_type import QueryType


class QueryRoutingMixin:
    """Mixin for query routing to appropriate indexes."""
    
    def _route_to_indexes(self, query_text: str, query_type: str) -> List[Tuple[str, float]]:
        """
        Route query to top-3 indexes with confidence scores.
        
        Returns:
            List of (index_name, confidence) tuples
        """
        top3_indexes = []
        
        # Try query router first
        if query_text and hasattr(self, 'query_router'):
            try:
                top3_indexes = self.query_router.route_top3_indexes(query_text)
                self.logger.info(f"ROUTING | TOP-3 indexes: {[(idx, f'{conf:.2f}') for idx, conf in top3_indexes]}")
            except Exception as e:
                self.logger.warning(f"ROUTING | TOP-3 routing failed: {e}, using fallback")
                top3_indexes = [('code', 0.6), ('documentation', 0.4), ('pr', 0.3)]
        else:
            # Fallback routing using LLM semantic reasoning
            if hasattr(self, "llm_manager"):
                try:
                    routing_prompt = f"""
                You are ranking search databases for a retrieval augmented GitHub chatbot.
                Available indexes: code, documentation, pr, issue, email, commit, repo_metrics, onboarding.
                Based on the query below, return the indexes in order of priority (most important first).
                Output ONLY a Python list. Example: ["email", "documentation", "code"]

                QUERY: {query_text}
                """
                    response = self.llm_manager.call_llm(
                        system_prompt="Rank priority search indexes for retrieval.",
                        user_prompt=routing_prompt
                    )

                    ranked = eval(response.strip()) if response.strip().startswith("[") else None

                    if ranked and isinstance(ranked, list):
                        # Convert to [('index', confidence), ...]
                        top3_indexes = [(idx, 1.0 - i * 0.15) for i, idx in enumerate(ranked[:3])]
                        self.logger.info(f"ROUTING | LLM priority: {top3_indexes}")
                    else:
                        raise Exception("LLM returned unexpected format")

                except Exception as e:
                    self.logger.warning(f"ROUTING | Semantic routing failed ({e}), using basic fallback")
                    top3_indexes = self._get_fallback_routing(query_type)
            else:
                top3_indexes = self._get_fallback_routing(query_type)

        # Adjust indexes for special query types
        adjusted_indexes = []
        for idx_name, conf in top3_indexes:
            if idx_name == 'impact_analysis':
                adjusted_indexes.append(('graph_nodes', conf))
                if not any(i[0] == 'code' for i in top3_indexes):
                    adjusted_indexes.append(('code', conf * 0.8))
            elif idx_name == 'traceability':
                adjusted_indexes.append(('graph_nodes', conf))
                if not any(i[0] == 'pr' for i in top3_indexes):
                    adjusted_indexes.append(('pr', conf * 0.9))
            else:
                adjusted_indexes.append((idx_name, conf))
        
        # Extract index types (ensure we have exactly 3)
        index_types = [idx for idx, _ in adjusted_indexes[:3]]
        if len(index_types) < 3:
            # Fill with defaults
            default_indexes = ['code', 'documentation', 'pr', 'email']
            for idx in default_indexes:
                if idx not in index_types and len(index_types) < 3:
                    index_types.append(idx)
        
        return adjusted_indexes[:3]
    
    def _get_fallback_routing(self, query_type: str) -> List[Tuple[str, float]]:
        """Get fallback routing based on query type."""
        if query_type == QueryType.CODE_STRUCTURE:
            return [('repository_overview', 0.9), ('analyzed_file', 0.8), ('code', 0.6)]
        elif query_type in [QueryType.ISSUE_SPECIFIC, QueryType.PR_SPECIFIC]:
            return [('pr', 0.8), ('code', 0.6), ('documentation', 0.4)]
        elif query_type == QueryType.COMMIT_SPECIFIC:
            return [('commit', 0.8), ('code', 0.6), ('pr', 0.4)]
        elif query_type in [QueryType.HOW_TO, QueryType.CONCEPTUAL]:
            return [('documentation', 0.8), ('code', 0.6), ('pr', 0.4)]
        else:
            return [('code', 0.7), ('documentation', 0.5), ('pr', 0.4)]


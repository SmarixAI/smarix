"""
Gmail correlation with GitHub results.
"""
from typing import List, Dict, Any
import numpy as np
from utils.metadata_normalizer import MetadataNormalizer


class GmailCorrelationMixin:
    """Mixin for Gmail correlation with GitHub results."""
    
    def retrieve_gmail_correlated(
        self,
        github_results: List[Dict[str, Any]],
        query_embedding: np.ndarray,
        keywords: List[str] = []
    ) -> List[Dict[str, Any]]:
        """Retrieve correlated Gmail results based on GitHub entities."""
        if not self.gmail_db or not github_results:
            return []

        github_entities = {
            'authors': set(),
            'issue_numbers': set(),
            'pr_numbers': set()
        }

        for result in github_results[:5]:
            # Use metadata normalizer for unified access
            meta_norm = MetadataNormalizer(result.get('metadata', {}), result)
            author = meta_norm.get('author')
            if author:
                github_entities['authors'].add(str(author).lower())
            issue_number = meta_norm.get_issue_number()
            if issue_number is not None:
                github_entities['issue_numbers'].add(str(issue_number))
            pr_number = meta_norm.get_pr_number()
            if pr_number is not None:
                github_entities['pr_numbers'].add(str(pr_number))

        gmail_results = self.gmail_db.search(query_embedding, top_k=20)

        correlated = []
        for email in gmail_results:
            metadata = email.get('metadata', {})

            if not metadata.get('is_git_related'):
                continue

            correlation = metadata.get('correlation_score', 0)
            correlated_entities = metadata.get('correlated_entities', {})

            entity_matches = 0
            for author in github_entities['authors']:
                if author in str(correlated_entities.get('correlated_authors', [])).lower():
                    entity_matches += 2

            for issue_num in github_entities['issue_numbers']:
                if issue_num in str(correlated_entities.get('correlated_issues', [])):
                    entity_matches += 3

            for pr_num in github_entities['pr_numbers']:
                if pr_num in str(correlated_entities.get('correlated_prs', [])):
                    entity_matches += 3

            if entity_matches > 0 or correlation > 3:
                email['relevance_score'] = correlation + entity_matches
                correlated.append(email)

        return sorted(correlated, key=lambda x: x.get('relevance_score', 0), reverse=True)[:5]
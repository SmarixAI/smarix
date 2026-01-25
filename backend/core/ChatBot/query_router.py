"""
Query Router: Intelligent routing to appropriate vector indices
Supports keyword-based, embedding-based, and LLM-based routing
"""

import os
import re
from typing import Dict, List, Optional, Tuple
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Constants for routing
VALID_INDEX_TYPES = [
    'documentation', 'code', 'pr', 'commit', 'email', 'issue', 
    'impact_analysis', 'traceability', 'multi',
    'pr_issue_tutorial', 'pr_issue_coding_question', 'random_pr_generator'
]

# Confidence thresholds
MULTI_QUERY_THRESHOLD = 0.7  # Score threshold for multi-query detection
DEFAULT_CONFIDENCE = 0.3  # Default confidence for unmatched queries
HIGH_CONFIDENCE_MULTI = 0.8  # Confidence multiplier for multi-query
DEFAULT_TOP3_CONFIDENCES = [0.6, 0.4, 0.3]  # Default confidences for top-3 fallback

# Score multipliers
IMPACT_ANALYSIS_BOOST = 2.0
PR_ISSUE_CONTEXT_BOOST = 3.0
PATTERN_MATCH_BOOST = 2.0


class QueryRouter:
    """
    Routes queries to appropriate vector indices based on query intent.
    """
    
    # Keyword mappings for routing
    KEYWORD_ROUTES = {
        'documentation': [
            'setup', 'install', 'configure', 'configuration', 'config',
            'readme', 'documentation', 'docs', 'guide', 'tutorial',
            'getting started', 'how to install', 'how to setup',
            'requirements', 'dependencies', 'prerequisites'
        ],
        'code': [
            'implement', 'function', 'class', 'method', 'code',
            'implementation', 'how does', 'how is', 'where is',
            'show me the', 'find the', 'locate', 'definition',
            'functionality', 'logic', 'algorithm'
        ],
        'pr': [
            'why', 'why was', 'why did', 'feature', 'added',
            'pull request', 'pr', 'change', 'changed',
            'reason', 'rationale', 'decision', 'why this',
            'what was the reason', 'explain the change'
        ],
        'commit': [
            'when', 'who changed', 'who modified', 'who updated',
            'commit', 'committed', 'history', 'timeline',
            'last modified', 'recent change', 'when was',
            'author', 'who wrote', 'who created'
        ],
        'email': [
            'email', 'emails', 'gmail', 'inbox', 'subject', 'sender', 'from', 'to',
            'thread', 'message', 'mail', 'attachment', 'attachments', 'sent', 'received',
            'cc', 'bcc', 'mailbox'
        ],
        'issue': [
            'issue', 'bug', 'error', 'fix', 'exception', 'stacktrace',
            'ticket', 'crash', 'failure', 'broken', 'not working',
            'debug', 'investigate', 'troubleshoot', 'why failing',
            'reproduce', 'replication', 'regression'
        ],
        'impact_analysis': [
            'what breaks', 'what happens if', 'impact of', 'dependencies',
            'depend on', 'relies on', 'used by', 'who calls', 'callers of',
            'where is used', 'change impact', 'consequences of changing',
            'coupling', 'inheritance', 'hierarchy', 'call graph', 'structure',
            'relationship', 'connected to'
        ],
        'traceability': [
            'who changed', 'who modified', 'who updated', 'who wrote',
            'who created', 'author of', 'creator of', 'history of',
            'evolution of', 'timeline of', 'changes to', 'past versions',
            'who is the expert', 'who knows about'
        ],

        'pr_issue_tutorial': [
            'tutorial', 'guide me', 'teach me', 'show me how',
            'step by step', 'walkthrough', 'learn', 'tutorial for',
            'explain step by step', 'how to solve', 'solution walkthrough'
        ],
        'pr_issue_coding_question': [
            'question', 'practice', 'challenge', 'exercise',
            'test my', 'quiz', 'problem', 'coding question',
            'practice question', 'coding challenge', 'solve this'
        ],
        'random_pr_generator': [
            'random pr', 'random pull request', 'generate random pr',
            'pick random pr', 'select random pr', 'choose random pr',
            'find random pr', 'get random pr', 'show random pr',
            'give me random pr', 'any random pr', 'suggest pr'
        ]
    }

    def __init__(self,
                 routing_method: str = "keyword",
                 embedding_model=None,
                 llm_client=None):
        """
        Initialize query router.

        Args:
            routing_method: 'keyword', 'embedding', or 'llm'
            embedding_model: Optional embedding model for embedding-based routing
            llm_client: Optional LLM client for LLM-based routing
        """
        self.routing_method = routing_method
        self.embedding_model = embedding_model
        self.llm_client = llm_client

        # Build keyword lookup (case-insensitive)
        self.keyword_lookup = {}
        for index_type, keywords in self.KEYWORD_ROUTES.items():
            for keyword in keywords:
                self.keyword_lookup[keyword.lower()] = index_type

        logger.info(f"Initialized QueryRouter with method: {routing_method}")

    def _initialize_scores(self) -> Dict[str, float]:
        """
        Initialize score dictionary for all index types.
        
        Returns:
            Dictionary with all index types initialized to 0.0
        """
        return {
            'documentation': 0.0,
            'code': 0.0,
            'pr': 0.0,
            'commit': 0.0,
            'email': 0.0,
            'issue': 0.0,
            'impact_analysis': 0.0,
            'traceability': 0.0,
            'pr_issue_tutorial': 0.0,
            'pr_issue_coding_question': 0.0,
            'random_pr_generator': 0.0
        }
    
    def _clean_json_response(self, text: str) -> str:
        """
        Clean JSON response by removing markdown code blocks.
        
        Args:
            text: Raw response text
            
        Returns:
            Cleaned JSON string
        """
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    
    def _call_llm_client(self, prompt: str, system_message: str = None, max_tokens: int = 150) -> Optional[str]:
        """
        Unified LLM client call handler supporting OpenAI and Anthropic.
        
        Args:
            prompt: User prompt
            system_message: Optional system message (defaults to routing expert)
            max_tokens: Maximum tokens in response
            
        Returns:
            Response text or None if failed
        """
        if self.llm_client is None:
            return None
        
        system_message = system_message or "You are a query routing expert. Always respond with valid JSON only."
        
        try:
            if hasattr(self.llm_client, 'chat'):
                # OpenAI-style
                try:
                    response = self.llm_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=max_tokens,
                        response_format={"type": "json_object"}
                    )
                except TypeError:
                    # Fallback if response_format not supported
                    response = self.llm_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=max_tokens
                    )
                return response.choices[0].message.content.strip()
                
            elif hasattr(self.llm_client, 'messages'):
                # Anthropic-style
                response = self.llm_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    temperature=0.1,
                    system=system_message,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
            else:
                logger.warning("Unknown LLM client type")
                return None
                
        except Exception as e:
            logger.error(f"LLM client call failed: {e}")
            return None
    
    def _parse_llm_json_response(self, result_text: str) -> Optional[Dict[str, any]]:
        """
        Parse and validate LLM JSON response.
        
        Args:
            result_text: Raw LLM response text
            
        Returns:
            Parsed JSON dict or None if parsing fails
        """
        import json
        try:
            cleaned_text = self._clean_json_response(result_text)
            result_json = json.loads(cleaned_text)
            return result_json
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return None

    def route(self, query: str) -> str:
        """
        Route query to appropriate index.

        Args:
            query: User query string

        Returns:
            Index type: 'documentation', 'code', 'pr', 'commit', 'issue', 'email',
                       'pr_issue_tutorial', 'pr_issue_coding_question', or 'multi'
        """

        query_lower = query.lower().strip()

        # 1️⃣ NEW: detect direct ID queries
        match = re.search(r'\b(?:pr|pull request)\s*#?\s*(\d+)\b', query_lower)
        if match:
            return "pr"



        if self.routing_method == "keyword":
            return self.keyword_route(query)
        elif self.routing_method == "embedding":
            return self.embedding_route(query)
        elif self.routing_method == "llm":
            return self.llm_route(query)
        else:
            logger.warning(f"Unknown routing method: {self.routing_method}, using keyword")
            return self.keyword_route(query)

    def keyword_route(self, query: str) -> str:
        """
        Route based on keywords in query.

        Args:
            query: User query string

        Returns:
            Index type string
        """
        query_lower = query.lower()

        # Count keyword matches for each index type
        scores = self._initialize_scores()

        # Check for direct keyword matches
        for keyword, index_type in self.keyword_lookup.items():
            if keyword in query_lower:
                scores[index_type] += 1

        has_pr_issue_context = any(pattern in query_lower for pattern in [
            'from pr', 'from pull request', 'from issue', 'based on pr', 'based on issue',
            'pr #', 'issue #', 'pull request #', 'using pr', 'using issue'
        ])

        has_random_pr_pattern = any(pattern in query_lower for pattern in [
            'random pr', 'generate pr', 'create random pr',
            'random pull request', 'make a pr', 'new random pr'
        ])

        if has_pr_issue_context:
            if any(word in query_lower for word in ['tutorial', 'guide', 'teach', 'show', 'learn', 'walkthrough']):
                scores['pr_issue_tutorial'] += PR_ISSUE_CONTEXT_BOOST
            if any(word in query_lower for word in ['question', 'practice', 'challenge', 'quiz', 'exercise']):
                scores['pr_issue_coding_question'] += PR_ISSUE_CONTEXT_BOOST

        if has_random_pr_pattern:
            scores['random_pr_generator'] += PR_ISSUE_CONTEXT_BOOST

        # Check for phrase patterns
        if any(phrase in query_lower for phrase in ['how to', 'how do', 'how can']):
            # Check if it's about setup/install
            if any(word in query_lower for word in ['setup', 'install', 'configure', 'get started']):
                scores['documentation'] += PATTERN_MATCH_BOOST
            else:
                scores['code'] += 1

        if any(phrase in query_lower for phrase in ['why', 'reason', 'rationale']):
            scores['pr'] += PATTERN_MATCH_BOOST

        if any(phrase in query_lower for phrase in ['when', 'who', 'author', 'timeline']):
            scores['commit'] += PATTERN_MATCH_BOOST

        # Check for code-specific patterns
        if any(pattern in query_lower for pattern in ['function', 'class', 'method', 'implementation']):
            scores['code'] += PATTERN_MATCH_BOOST

        # Check for PR-specific patterns
        if any(pattern in query_lower for pattern in ['pull request', 'pr #', 'feature', 'change']):
            scores['pr'] += PATTERN_MATCH_BOOST

        # Check for ISSUE-specific patterns
        if any(pattern in query_lower for pattern in [
            'error', 'exception', 'stacktrace', 'traceback', 'crash',
            'not working', 'failing', 'failure', 'bug', 'fix', 'debug',
            'investigate', 'troubleshoot', 'regression', 'reproduce']):
            scores['issue'] += PATTERN_MATCH_BOOST

        # Check for EMAIL-specific patterns
        if any(pattern in query_lower for pattern in [
            'email', 'gmail', 'mail', 'message', 'inbox', 'sent mail', 'received mail',
            'from:', 'to:', 'cc:', 'bcc:', 'subject', 'sender', 'recipient', 'attachment',
            'thread', 'conversation', 'mailbox']):
            scores['email'] += PATTERN_MATCH_BOOST

        if any(pattern in query_lower for pattern in [
            'what breaks', 'impact of', 'if i change', 'who uses', 'callers of',
            'dependencies', 'dependents', 'inheritance', 'call graph', 'hierarchy']):
            scores['impact_analysis'] += PR_ISSUE_CONTEXT_BOOST


        # Get max score
        max_score = max(scores.values())

        if max_score == 0:
            # No clear match, default to 'code' for technical queries
            logger.info(f"No keyword match for query, defaulting to 'code'")
            return 'code'

        # Get index type with max score
        best_index = max(scores.items(), key=lambda x: x[1])[0]

        # Check if multiple indices have high scores (multi-query)
        high_scores = [idx for idx, score in scores.items() if score >= max_score * MULTI_QUERY_THRESHOLD]

        if len(high_scores) > 1:
            logger.info(f"Multiple indices matched: {high_scores}, using 'multi'")
            return 'multi'

        logger.info(f"Routed '{query[:50]}...' to '{best_index}' (score: {max_score})")
        return best_index

    def embedding_route(self, query: str) -> str:
        """
        Route based on embedding similarity to index samples.
        Requires embedding_model to be set.

        Args:
            query: User query string

        Returns:
            Index type string
        """
        if self.embedding_model is None:
            logger.warning("Embedding model not set, falling back to keyword routing")
            return self.keyword_route(query)

        try:
            # Sample queries for each index type
            sample_queries = {
                'documentation': [
                    "How to install and setup the project?",
                    "What are the configuration requirements?",
                    "Readme and documentation guide"
                ],
                'code': [
                    "Show me the implementation of authentication",
                    "Where is the login function defined?",
                    "How does the API endpoint work?"
                ],
                'pr': [
                    "Why was this feature added?",
                    "What was the reason for this change?",
                    "Explain the pull request decision"
                ],
                'commit': [
                    "When was this file last modified?",
                    "Who changed the authentication code?",
                    "Show commit history for this feature"
                ],
                'issue': [
                    "Why is authentication throwing an error?",
                    "How do I debug the login crash?",
                    "Stacktrace shows null reference — how to fix?",
                    "Recent bug ticket: investigation and fix"
                ],
                'email': [
                    "Find email messages in Gmail",
                    "Who sent this email?",
                    "Search inbox for subject containing onboarding",
                    "Show thread with attachments",
                    "Retrieve emails from the last week"
                ],
                'impact_analysis': [
                    "What breaks if I change the User class?",
                    "Show me all functions that call verify_token",
                    "What are the dependencies of the auth module?",
                    "Impact of modifying this function",
                    "Who inherits from BaseController?",
                    "Show the call graph for login"
                ],
                'traceability': [
                    "Who is the expert on auth.py?",
                    "Who modified the login function recently?",
                    "Show the history of changes for this file",
                    "Timeline of Pull Requests for the API",
                    "Who created this module?"
                ],

                'pr_issue_tutorial': [
                    "Create a tutorial from PR #45",
                    "Guide me through how issue #23 was solved",
                    "Step-by-step walkthrough of pull request changes"
                ],
                'pr_issue_coding_question': [
                    "Generate a coding question from issue #67",
                    "Practice problem based on PR #89",
                    "Create a challenge from the bug fix in issue #45"
                ],
                'random_pr_generator': [
                    "Generate a random pull request",
                    "Create a new random PR for testing",
                    "Make a random pull request suggestion"
                ]
            }
            
            # Embed query
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Embed samples and find best match
            best_index = 'code'  # default
            best_score = -1
            
            for index_type, samples in sample_queries.items():
                sample_embeddings = self.embedding_model.encode(samples)
                
                # Calculate average similarity
                similarities = np.dot(sample_embeddings, query_embedding)
                avg_similarity = np.mean(similarities)
                
                if avg_similarity > best_score:
                    best_score = avg_similarity
                    best_index = index_type
            
            logger.info(f"Embedding route: '{query[:50]}...' → '{best_index}' (score: {best_score:.3f})")
            return best_index
            
        except Exception as e:
            logger.error(f"Embedding routing failed: {e}, falling back to keyword")
            return self.keyword_route(query)
    
    def llm_route(self, query: str) -> str:
        """
        Route using LLM to classify query intent with predefined options.
        Uses structured JSON output for reliable parsing.
        
        Args:
            query: User query string
            
        Returns:
            Index type string: 'documentation', 'code', 'pr', 'commit','issue', or 'multi'
        """
        if self.llm_client is None:
            logger.warning("LLM client not set, falling back to keyword routing")
            return self.keyword_route(query)
        
        try:
            # Enhanced prompt with clear definitions and examples
            prompt = f"""Analyze the following user query and determine which index type would best contain the answer.

                AVAILABLE INDEX TYPES:
                1. 'documentation' - Documentation, setup guides, installation instructions, configuration, README files, tutorials, getting started guides
                2. 'code' - Source code, function implementations, class definitions, code location, how code works, algorithms
                3. 'pr' - Pull requests, why features were added, design decisions, code review discussions, feature rationale
                4. 'commit' - Commit history, when changes were made, who made changes, file modification history, timeline
                5. 'email' — Email messages, Gmail inbox, threads, subjects, senders, recipients, attachments, message bodies, mailbox searches
                6. 'issue' – Bug discussions, crashes, exceptions, debugging, regression, troubleshooting, tickets
                7. 'impact_analysis' - Questions about breaking changes, dependencies, callers, usages, impact of modifications, inheritance, class hierarchy
                8. 'traceability' - Questions about history, authorship, who changed code, evolution, timeline of changes, and linking users to code.
                9. 'multi' - Questions that clearly need information from multiple index types
                

                EXAMPLES:
                - "how to install" → documentation
                - "show me the authentication function" → code
                - "what calls the login function?" → impact_analysis
                - "why was this feature added" → pr
                - "when was chatbot.py modified" → commit
                - "search inbox for onboarding mail" → email
                - "why is login crashing" → issue
                - "how does authentication work and why was it added" → multi

                USER QUERY: "{query}"

                Respond with ONLY a valid JSON object in this exact format:
                {{"index_type": "documentation|code|pr|commit|email|issue|impact_analysis|traceability|multi", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}

                Do not include any other text, only the JSON object."""
                            
            # Call LLM with structured output
            result_text = self._call_llm_client(prompt, max_tokens=150)
            if result_text is None:
                logger.warning("LLM client call failed, falling back to keyword")
                return self.keyword_route(query)
            
            # Parse JSON response
            result_json = self._parse_llm_json_response(result_text)
            if result_json is None:
                # Try to extract index type from text if JSON parsing fails
                logger.warning("Failed to parse JSON response, attempting text extraction")
                result_lower = result_text.lower()
                for valid_type in ['documentation', 'code', 'pr', 'commit', 'multi']:
                    if f'"index_type": "{valid_type}"' in result_lower or f'index_type": "{valid_type}' in result_lower:
                        logger.info(f"LLM route (extracted): '{query[:50]}...' → '{valid_type}'")
                        return valid_type
                
                logger.warning(f"Could not extract index type from: {result_text}, falling back to keyword")
                return self.keyword_route(query)
            
            index_type = result_json.get('index_type', '').lower().strip()
            confidence = result_json.get('confidence', 0.5)
            reasoning = result_json.get('reasoning', '')
            
            # Validate index type
            valid_types = [t for t in VALID_INDEX_TYPES if t not in ['direct_id', 'pr_issue_tutorial', 'pr_issue_coding_question', 'random_pr_generator']]
            if index_type in valid_types:
                logger.info(f"LLM route: '{query[:50]}...' → '{index_type}' (confidence: {confidence:.2f}, reasoning: {reasoning})")
                return index_type
            else:
                logger.warning(f"LLM returned invalid type: '{index_type}', falling back to keyword")
                return self.keyword_route(query)
                
        except Exception as e:
            logger.error(f"LLM routing failed: {e}, falling back to keyword")
            import traceback
            logger.debug(traceback.format_exc())
            return self.keyword_route(query)
    
    def route_with_confidence(self, query: str) -> Tuple[str, float]:
        """
        Route query and return confidence score.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (index_type, confidence_score)
        """
        if self.routing_method == "keyword":
            return self._keyword_route_with_confidence(query)
        elif self.routing_method == "llm":
            return self._llm_route_with_confidence(query)
        else:
            # For embedding method, use keyword as confidence baseline
            index_type = self.route(query)
            confidence = 0.8 if index_type != 'multi' else 0.6
            return (index_type, confidence)
    
    def _llm_route_with_confidence(self, query: str) -> Tuple[str, float]:
        """
        LLM routing with confidence score extraction.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (index_type, confidence_score)
        """
        if self.llm_client is None:
            logger.warning("LLM client not set, falling back to keyword routing")
            return self._keyword_route_with_confidence(query)
        
        try:
            # Use the same prompt as llm_route but extract confidence
            prompt = f"""Analyze the following user query and determine which index type would best contain the answer.

                AVAILABLE INDEX TYPES:
                1. 'documentation' - Documentation, setup guides, installation instructions, configuration, README files, tutorials
                2. 'code' - Source code, function implementations, class definitions, code location, how code works
                3. 'pr' - Pull requests, why features were added, design decisions, code review discussions
                4. 'commit' - Commit history, when changes were made, who made changes, file modification history
                5. 'email' — Email messages, Gmail inbox, subjects, senders, recipients, threads, attachments, message body, mailbox searches
                6. 'issue' — Bug discussions, crashes, exceptions, debugging, regression, troubleshooting, tickets
                7. 'impact_analysis' - Questions about breaking changes, dependencies, callers, usages, impact of modifications, inheritance, class hierarchy
                8. 'traceability' - Questions about history, authorship, who changed code, evolution.
                9. 'multi' - Questions that clearly need information from multiple index types

                USER QUERY: "{query}"

                Respond with ONLY a valid JSON object:
                {{"index_type": "documentation|code|pr|commit|email|issue|impact_analysis|traceability|multi", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

            result_text = self._call_llm_client(prompt, max_tokens=150)
            if result_text is None:
                return self._keyword_route_with_confidence(query)
            
            # Parse JSON
            result_json = self._parse_llm_json_response(result_text)
            if result_json is None:
                logger.warning("Failed to parse LLM confidence response, using default confidence")
                # Try to get index type from llm_route
                index_type = self.llm_route(query)
                confidence = 0.75 if index_type != 'multi' else 0.6
                return (index_type, confidence)
            
            index_type = result_json.get('index_type', '').lower().strip()
            confidence = float(result_json.get('confidence', 0.7))
            reasoning = result_json.get('reasoning', '')
            
            # Validate
            valid_types = [t for t in VALID_INDEX_TYPES if t not in ['direct_id', 'pr_issue_tutorial', 'pr_issue_coding_question', 'random_pr_generator']]
            if index_type in valid_types:
                # Clamp confidence to valid range
                confidence = max(0.0, min(1.0, confidence))
                logger.info(f"LLM route (with confidence): '{query[:50]}...' → '{index_type}' ({confidence:.2f}) - {reasoning}")
                return (index_type, confidence)
            else:
                logger.warning(f"LLM returned invalid type: '{index_type}', falling back")
                return self._keyword_route_with_confidence(query)
                
        except Exception as e:
            logger.error(f"LLM confidence routing failed: {e}, falling back to keyword")
            return self._keyword_route_with_confidence(query)
    
    def _keyword_route_with_confidence(self, query: str) -> Tuple[str, float]:
        """
        Keyword routing with confidence score.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (index_type, confidence_score)
        """
        query_lower = query.lower()
        scores = self._initialize_scores()
        
        # Count matches
        for keyword, index_type in self.keyword_lookup.items():
            if keyword in query_lower:
                scores[index_type] += 1

        if any(p in query_lower for p in ['breaks', 'impact', 'who uses', 'callers', 'dependency']):
            scores['impact_analysis'] += IMPACT_ANALYSIS_BOOST
        
        max_score = max(scores.values())
        total_score = sum(scores.values())
        
        if total_score == 0:
            return ('code', DEFAULT_CONFIDENCE)
        
        best_index = max(scores.items(), key=lambda x: x[1])[0]
        confidence = min(max_score / max(total_score, 1), 1.0)
        
        # Check for multi-query
        high_scores = [idx for idx, score in scores.items() if score >= max_score * MULTI_QUERY_THRESHOLD]
        if len(high_scores) > 1:
            return ('multi', confidence * HIGH_CONFIDENCE_MULTI)
        
        return (best_index, confidence)
    
    def route_top3_indexes(self, query: str) -> List[Tuple[str, float]]:
        """
        Route query to TOP-3 most relevant indexes with confidence scores.
        
        Args:
            query: User query string
            
        Returns:
            List of (index_type, confidence) tuples, sorted by confidence (descending)
        """
        if self.routing_method == "llm":
            return self._llm_route_top3(query)
        elif self.routing_method == "keyword":
            return self._keyword_route_top3(query)
        else:
            # Fallback: use keyword routing
            return self._keyword_route_top3(query)
    
    def _llm_route_top3(self, query: str) -> List[Tuple[str, float]]:
        """
        Use LLM to determine TOP-3 indexes with confidence scores.
        
        Args:
            query: User query string
            
        Returns:
            List of (index_type, confidence) tuples, sorted by confidence (descending)
        """
        if self.llm_client is None:
            logger.warning("LLM client not set, falling back to keyword routing")
            return self._keyword_route_top3(query)
        
        try:
            prompt = f"""Analyze the following user query and determine the TOP-3 most relevant index types that would contain the answer, ranked by relevance.

                AVAILABLE INDEX TYPES:
                1. 'documentation' - Documentation, setup guides, installation instructions, configuration, README files, tutorials, getting started guides
                2. 'code' - Source code, function implementations, class definitions, code location, how code works, algorithms
                3. 'pr' - Pull requests, why features were added, design decisions, code review discussions, feature rationale
                4. 'commit' - Commit history, when changes were made, who made changes, file modification history, timeline
                5. 'issue' — Bug discussions, crashes, exceptions, debugging, regression, troubleshooting, tickets
                6. 'email' - Email messages (Gmail), subjects, senders, recipients, bodies, attachments, threads, inbox/search
                7. 'impact_analysis' - Questions about breaking changes, dependencies, callers, usages, impact of modifications, inheritance, class hierarchy
                8. 'traceability' - Questions about history, authorship, and evolution.
                9. 'multi' - Questions that clearly need information from multiple index types

                USER QUERY: "{query}"

                Respond with ONLY a valid JSON object in this exact format:
                {{
                    "top3_indexes": [
                        {{"index_type": "code", "confidence": 0.9, "reasoning": "query asks about code implementation"}},
                        {{"index_type": "documentation", "confidence": 0.7, "reasoning": "may need documentation context"}},
                        {{"index_type": "email", "confidence": 0.5, "reasoning": "could reference email/thread content"}}
                    ]
                }}

                Return exactly 3 indexes, sorted by confidence (highest first). Do not include any other text."""

            result_text = self._call_llm_client(prompt, max_tokens=300)
            if result_text is None:
                return self._keyword_route_top3(query)
            
            # Parse JSON
            result_json = self._parse_llm_json_response(result_text)
            if result_json is None:
                logger.warning("Failed to parse LLM TOP-3 response, falling back to keyword")
                return self._keyword_route_top3(query)
            
            top3_list = result_json.get('top3_indexes', [])
            
            if len(top3_list) < 3:
                logger.warning(f"LLM returned {len(top3_list)} indexes, expected 3. Falling back to keyword.")
                return self._keyword_route_top3(query)
            
            # Extract and validate
            valid_types = [t for t in VALID_INDEX_TYPES if t not in ['direct_id', 'pr_issue_tutorial', 'pr_issue_coding_question', 'random_pr_generator']]
            top3_results = []
            for item in top3_list[:3]:
                idx_type = item.get('index_type', '').lower().strip()
                confidence = float(item.get('confidence', 0.5))
                confidence = max(0.0, min(1.0, confidence))
                
                if idx_type in valid_types:
                    top3_results.append((idx_type, confidence))
            
            if len(top3_results) < 3:
                logger.warning(f"Only {len(top3_results)} valid indexes from LLM, filling with keyword routing")
                keyword_top3 = self._keyword_route_top3(query)
                # Merge and deduplicate
                seen = set()
                merged = []
                for idx, conf in top3_results + keyword_top3:
                    if idx not in seen:
                        seen.add(idx)
                        merged.append((idx, conf))
                        if len(merged) >= 3:
                            break
                return merged[:3]
            
            # Sort by confidence (descending)
            top3_results.sort(key=lambda x: x[1], reverse=True)
            logger.info(f"LLM TOP-3 route: {top3_results}")
            return top3_results[:3]
                
        except Exception as e:
            logger.error(f"LLM TOP-3 routing failed: {e}, falling back to keyword")
            return self._keyword_route_top3(query)
    
    def _keyword_route_top3(self, query: str) -> List[Tuple[str, float]]:
        """
        Keyword-based routing to TOP-3 indexes with confidence scores.
        
        Args:
            query: User query string
            
        Returns:
            List of (index_type, confidence) tuples, sorted by confidence (descending)
        """
        query_lower = query.lower()
        scores = self._initialize_scores()
        
        # Count keyword matches
        for keyword, index_type in self.keyword_lookup.items():
            if keyword in query_lower:
                scores[index_type] += 1.0

        if any(p in query_lower for p in ['breaks', 'impact', 'callers', 'dependency']):
            scores['impact_analysis'] += IMPACT_ANALYSIS_BOOST
        
        # Normalize scores to confidence (0.0-1.0)
        max_score = max(scores.values()) if scores.values() else 1.0
        total_score = sum(scores.values())
        
        if total_score == 0:
            # Default: code, documentation, pr with decreasing confidence
            return [
                ('code', DEFAULT_TOP3_CONFIDENCES[0]), 
                ('documentation', DEFAULT_TOP3_CONFIDENCES[1]), 
                ('pr', DEFAULT_TOP3_CONFIDENCES[2])
            ]
        
        # Convert scores to confidence scores
        confidences = {}
        for idx_type, score in scores.items():
            if max_score > 0:
                confidences[idx_type] = min(score / max(max_score, 1), 1.0)
            else:
                confidences[idx_type] = 0.3
        
        # Sort by confidence and return TOP-3
        sorted_indexes = sorted(confidences.items(), key=lambda x: x[1], reverse=True)
        top3 = sorted_indexes[:3]
        
        # Ensure we have exactly 3 (fill with defaults if needed)
        if len(top3) < 3:
            default_indexes = ['code', 'documentation', 'pr','issue', 'email']
            seen = {idx for idx, _ in top3}
            for idx in default_indexes:
                if len(top3) >= 3:
                    break
                if idx not in seen:
                    top3.append((idx, 0.2))
        
        logger.info(f"Keyword TOP-3 route: {top3}")
        return top3[:3]


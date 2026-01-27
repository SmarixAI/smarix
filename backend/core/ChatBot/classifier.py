# classifier.py
import re
import time
from typing import List, Dict, Any, Optional, Iterator
from .query_type import QueryType

# Constants for classification
GREETING_WORDS = ['hi', 'hello', 'hellow', 'hey', 'greetings', 'howdy', 'sup']

GREETING_PATTERNS = [
    r'^(hi+|hello+|hey+)\s*(there|chatbot|bot|assistant)[\?\.!]*$',
    r'^(what\'s up|whats up|sup|howdy)[\?\.!]*$',
    r'^(good\s+(morning|afternoon|evening))[\?\.!]*$',
    r'^(how\s+are\s+you|how\s+do\s+you\s+do)[\?\.!]*$',
    r'^(introduce\s+yourself|who\s+are\s+you|what\s+can\s+you\s+do)[\?\.!]*$',
    r'^help[\?\.!]*$',
    r'^start[\?\.!]*$',
]

QUESTION_GENERATION_PATTERNS = [
    r"generate\s+(questions?|mcqs?|quiz)",
    r"create\s+(questions?|mcqs?|quiz)",
    r"make\s+(questions?|mcqs?|quiz)",
    r"give\s+me\s+(questions?|mcqs?|quiz)",
    r"(questions?|mcqs?|quiz)\s+(on|about|for)",
    r"test\s+my\s+knowledge",
    r"assess\s+(my\s+)?understanding",
    r"prepare\s+(questions?|quiz)",
    r"subjective\s+questions?",
    r"code\s+based\s+questions?",
    r"multiple\s+choice\s+questions?",
    r"coding\s+question\s+based?"
]

PR_ISSUE_PATTERNS = [
    'pr #', 'pr#', 'pull request #', 'issue #', 'issue#',
    'from pr', 'from issue', 'based on pr', 'based on issue',
    'using pr', 'using issue'
]

TUTORIAL_INTENT_PATTERNS = [
    'tutorial', 'guide', 'walkthrough', 'step by step', 'teach',
    'show me how', 'explain how', 'learn', 'guide me through'
]

QUESTION_INTENT_PATTERNS = [
    'question', 'challenge', 'practice', 'exercise', 'problem',
    'coding question', 'coding challenge', 'practice problem',
    'quiz', 'test', 'assessment', 'task'
]

RANDOM_PR_PATTERNS = [
    r'random\s+pr',
    r'random\s+pull\s+request',
    r'generate\s+random\s+pr',
    r'pick\s+random\s+pr',
    r'select\s+random\s+pr',
    r'choose\s+random\s+pr',
    r'find\s+random\s+pr',
    r'get\s+random\s+pr',
    r'show\s+random\s+pr',
    r'give\s+me\s+random\s+pr',
    r'any\s+random\s+pr',
    r'suggest\s+pr',
    r'random\s+merged\s+pr',
]

METRICS_KEYWORDS = [
    'repo metric', 'repository metric', 'show me metric',
    'lines of code', 'loc', 'total lines', 'code lines',
    'how many lines', 'size of codebase', 'number of functions',
    'number of classes', 'function count', 'class count',
    'code metric', 'complexity', 'code quality', 'code statistics',
    'statistics', 'code stats'
]

TECH_STACK_KEYWORDS = [
    'tech stack', 'technology', 'technologies used', 'framework',
    'frameworks', 'what language', 'programming language',
    'built with', 'uses what', 'database', 'tools used',
    'dependencies', 'libraries'
]

STRUCTURE_KEYWORDS = [
    'codebase structure', 'project structure', 'folder structure',
    'directory structure', 'file organization', 'how is code organized',
    'repo structure', 'repository structure', 'modules', 'components',
    'file hierarchy', 'directory tree', 'code structure', 'show me.*structure',
    'diagram.*structure', 'structure.*diagram'
]

FLOW_KEYWORDS = [
    'flow', 'diagram', 'sequence', 'process flow', 'architecture',
    'how does it work', 'how does', 'explain the flow', 'data flow',
    'workflow', 'pipeline', 'system design', 'architecture.*service',
    'service.*architecture', 'architecture.*flow', 'flow.*architecture'
]

IMPACT_KEYWORDS = [
    'what breaks', 'impact of', 'if i change', 'who uses', 'callers of',
    'dependencies', 'depend on', 'relies on', 'used by', 'who calls',
    'change impact', 'consequences of changing', 'call graph', 'hierarchy',
    'inheritance'
]

TRACEABILITY_KEYWORDS = [
    'who changed', 'who modified', 'who updated', 'who wrote',
    'who created', 'author of', 'creator of', 'history of',
    'evolution of', 'timeline of', 'changes to', 'past versions',
    'who is the expert', 'who knows about'
]

STOP_WORDS = {
    'how', 'do', 'i', 'the', 'a', 'an', 'is', 'are', 'what', 'where',
    'when', 'who', 'which', 'this', 'that', 'can', 'does', 'to', 'in',
    'on', 'for', 'me', 'you', 'it', 'of', 'and', 'or', 'but', 'show', 'me',
    'about', 'tell', 'first', 'last', 'oldest', 'newest', 'latest'
}

# LLM Configuration Constants
LLM_TEMPERATURE_LOW = 0.1  # For classification tasks
LLM_TEMPERATURE_MEDIUM = 0.3  # For rewriting/optimization tasks
LLM_MAX_TOKENS_SHORT = 10  # For yes/no responses
LLM_MAX_TOKENS_MEDIUM = 50  # For category names
LLM_MAX_TOKENS_STANDARD = 150  # For query optimization
LLM_MAX_TOKENS_LONG = 200  # For query rewriting

# Streaming and validation constants
STREAMING_DELAY = 0.02  # Delay between lines in streaming (seconds)
QUERY_LENGTH_MULTIPLIER_THRESHOLD = 3  # Max length multiplier for rewritten queries
WORD_OVERLAP_THRESHOLD = 0.3  # Minimum word overlap for rewritten queries
SHORT_QUERY_MAX_WORDS = 2  # Max words for short query detection
SHORT_QUERY_MAX_LENGTH = 20  # Max characters for short query detection

# Simple queries that shouldn't be rewritten
SIMPLE_QUERIES = ['help', 'start', 'hi', 'hello', 'hey']


class ClassifierMixin:

    def _call_llm_client(
        self, 
        prompt: str, 
        system_message: str = None,
        temperature: float = LLM_TEMPERATURE_LOW,
        max_tokens: int = LLM_MAX_TOKENS_MEDIUM
    ) -> Optional[str]:
        """
        Unified LLM client call handler supporting OpenAI and Anthropic.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            temperature: Temperature for generation
            max_tokens: Maximum tokens in response
            
        Returns:
            Response text or None if failed
        """
        if not hasattr(self, 'provider') or self.provider not in ['openai', 'anthropic']:
            return None
        
        if not hasattr(self, 'client') or not self.client:
            return None
        
        try:
            if self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message or "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content.strip()
                
            elif self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_message or "You are a helpful assistant.",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
            
            return None
                
        except Exception as e:
            self.logger.error(f"LLM client call failed: {e}")
            return None

    def is_greeting(self, query: str) -> bool:
        """
        Use LLM to detect if the query is a greeting.
        Falls back to regex-based detection if LLM is not available.
        """
        query = query.strip()
        if not query:
            return False

        # Try LLM-based detection first if available
        greeting_prompt = f"""Determine if the following user message is a greeting or introduction.

        A greeting is:
        - A simple hello, hi, hey, or similar salutation (including variations like "hii", "hiii", "heyyy")
        - Asking "how are you", "what's up", "howdy", etc.
        - Asking the assistant to introduce itself ("who are you", "what can you do", "introduce yourself")
        - A request for help to get started ("help", "start")
        - Time-based greetings ("good morning", "good afternoon", "good evening")

        NOT a greeting:
        - Questions about code, functions, files, or technical topics
        - Requests for specific information or explanations
        - Commands or queries that require codebase search

        User message: "{query}"

        Respond with ONLY "yes" if it's a greeting, or "no" if it's not. No other text."""

        result = self._call_llm_client(
            greeting_prompt,
            system_message="You are a helpful assistant that classifies user messages. Respond with only 'yes' or 'no'.",
            temperature=LLM_TEMPERATURE_LOW,
            max_tokens=LLM_MAX_TOKENS_SHORT
        )

        if result:
            is_greeting = result.lower().startswith('yes')
            if is_greeting:
                self.logger.info(f"GREETING DETECTION | LLM detected greeting: '{query}'")
            return is_greeting

        # Fallback to regex-based detection
        query_lower = query.lower()

        # Remove punctuation for easier matching
        query_clean = re.sub(r'[^\w\s]', '', query_lower).strip()

        # Normalize by collapsing repeated consecutive letters (e.g., "hii" -> "hi", "hiii" -> "hi")
        # This handles variations like "hii", "hiii", "heyyy", etc.
        normalized = re.sub(r'(.)\1+', r'\1', query_clean)

        # Check if normalized query starts with a greeting word
        for word in GREETING_WORDS:
            if normalized.startswith(word):
                # Check if it's just the greeting word
                remaining = normalized[len(word):].strip()
                if not remaining:
                    return True
                # Check for "hi there", "hello bot", etc.
                if remaining in ['there', 'chatbot', 'bot', 'assistant']:
                    return True

        # Also check original query with patterns (handles punctuation)
        for pattern in GREETING_PATTERNS:
            if re.match(pattern, query_lower):
                return True

        return False

    def is_question_generation_query(self, query: str) -> bool:
        """
        Detect if the query is requesting question generation (quiz, MCQs, assessments).
        """
        query_lower = query.lower().strip()

        for pattern in QUESTION_GENERATION_PATTERNS:
            if re.search(pattern, query_lower):
                return True

        return False

    def is_pr_issue_tutorial_query(self, query: str) -> bool:
        """
        Detect if the query is requesting a tutorial based on a PR/issue.
        """
        query_lower = query.lower().strip()

        # Must have both: PR/issue reference AND tutorial/guide keywords
        has_pr_issue = any(pattern in query_lower for pattern in PR_ISSUE_PATTERNS)
        has_tutorial_intent = any(pattern in query_lower for pattern in TUTORIAL_INTENT_PATTERNS)

        return has_pr_issue and has_tutorial_intent

    def is_pr_issue_coding_question_query(self, query: str) -> bool:
        """
        Detect if the query is requesting a coding question/challenge based on a PR/issue.
        Handles both specific PR references and general random PR requests.
        """
        query_lower = query.lower().strip()

        has_question_intent = any(pattern in query_lower for pattern in QUESTION_INTENT_PATTERNS)

        # Extended PR/issue patterns including random PR requests
        extended_pr_issue_patterns = PR_ISSUE_PATTERNS + [
            'random pr', 'random pull request', 'random issue',
            'any pr', 'any pull request', 'any issue',
            'a pr', 'a pull request', 'an issue',
            'easy pr', 'medium pr', 'hard pr',
            'easy pull request', 'medium pull request', 'hard pull request',
            'easy difficulty pr', 'medium difficulty pr', 'hard difficulty pr',
            'inspired by', 'based on a', 'from a'
        ]
        has_pr_issue = any(pattern in query_lower for pattern in extended_pr_issue_patterns)

        combined_patterns = [
            'generate a coding question',
            'create a coding question',
            'generate coding question',
            'create coding question',
            'generate a challenge',
            'create a challenge',
            'coding challenge based on',
            'coding question based on',
            'practice problem from',
            'exercise from'
        ]

        has_combined = any(pattern in query_lower for pattern in combined_patterns)

        return (has_pr_issue and has_question_intent) or has_combined

    def generate_greeting_response_streaming(self) -> Iterator[str]:
        repo_name = self.repo_info.get('name', 'this repository')
        total_chunks = self.repo_info.get('total_chunks', 0)

        greeting = f"""Hello! I'm your AI-powered codebase assistant.

## What I Can Help You With

I have indexed **{total_chunks:,} code chunks** and can help you with:

### Code Architecture & Flow
- **Architecture diagrams**: "What is the architecture of the notification service?"
- **Flow explanations**: "Explain the authentication flow with a diagram"
- **Component interactions**: "How do services communicate?"

### Code Search & Understanding
- **Find code**: "Where is the login functionality?"
- **Understand implementations**: "How does the task manager work?"
- **Class/function details**: "Show me the TaskService class implementation"

### Issues & Pull Requests
- **Specific queries**: "Tell me about issue #123" or "Show me PR #45"
- **Browse history**: "What is the first issue?" or "Show me the latest PR"
- **Search by topic**: "Show me notification-related issues"

### Repository Insights
- **Metrics**: "Show me repository metrics"
- **Tech stack**: "What technologies are used?"
- **Structure**: "Show me the repository structure"

### Development Guidance
- **How-to guides**: "How do I add a new feature?"
- **Troubleshooting**: "How to fix authentication errors?"
- **Best practices**: "How is error handling implemented?"

### Learning & Practice
- **Tutorials**: "Create a tutorial from PR #45" or "Guide me through issue #23"
- **Coding questions**: "Generate a coding challenge from issue #67"
"""

        if self.gmail_db:
            try:
                gmail_count = self.gmail_db.index.ntotal
                greeting += f"\nI also have access to **{gmail_count} related emails** for additional context.\n"
            except Exception:
                greeting += "\nI also have access to related emails for additional context.\n"

        greeting += """
## Example Questions

- "What is the architecture of the authentication service?"
- "Show me the first issue"
- "Where is the notification logic implemented?"
- "Tell me about PR #28"
- "What tech stack is used?"
- "How does the profile switching work?"
- "Create a tutorial from PR #45"
- "Generate a coding question based on issue #23"

Feel free to ask me anything about the codebase!"""

        self.logger.info("GREETING | Generated greeting response")

        lines = greeting.split('\n')
        for line in lines:
            yield line + '\n'
            # small delay to make streaming more natural (adjustable)
            time.sleep(STREAMING_DELAY)

    def expand_query(self, query: str) -> str:
        query_lower = query.lower().strip()

        expansions = {
            r'^architecture\s*$': 'What is the architecture of the codebase?',
            r'^architecture\s+of\s+(\w+)$': 'What is the architecture and flow of the \\1 service?',
            r'^(\w+)\s+architecture$': 'What is the architecture and flow of the \\1 service?',
            r'^repo\s+structure\s*$': 'Show me the repository structure with a diagram',
            r'^code\s+structure\s*$': 'Show me the code structure with a diagram',
            r'^structure\s*$': 'Show me the repository structure with a diagram',
            r'^diagram\s+of\s+(.+)$': 'Can you show me a diagram of \\1?',
            r'^tech\s+stack\s*$': 'What tech stack is used in this repository?',
            r'^metrics\s*$': 'Show me the repository metrics',
            r'^flow\s+of\s+(\w+)$': 'Explain the flow and architecture of \\1 with a diagram',
            r'^(\w+)\s+flow$': 'Explain the flow and architecture of \\1 with a diagram',
        }

        for pattern, replacement in expansions.items():
            match = re.match(pattern, query_lower)
            if match:
                if match.groups():
                    expanded = re.sub(pattern, replacement, query_lower)
                else:
                    expanded = replacement

                if self.verbose:
                    print(f"Expanded query: '{query}' -> '{expanded}'")
                return expanded

        return query

    def detect_chronological_query(self, query: str) -> Optional[Dict[str, Any]]:
        query_lower = query.lower()

        patterns = [
            (r'(first|oldest|earliest)\s+(issue|pr|pull\s*request)', 'first'),
            (r'(last|latest|newest|recent)\s+(issue|pr|pull\s*request)', 'last'),
            (r'(issue|pr|pull\s*request)\s+(first|oldest|earliest)', 'first'),
            (r'(issue|pr|pull\s*request)\s+(last|latest|newest|recent)', 'last'),
            (r'tell\s+me\s+about\s+(first|oldest)\s+(issue|pr)', 'first'),
            (r'tell\s+me\s+about\s+(last|latest|newest)\s+(issue|pr)', 'last'),
            (r'what\s+is\s+the\s+(first|oldest)\s+(issue|pr)', 'first'),
            (r'what\s+is\s+the\s+(last|latest|newest)\s+(issue|pr)', 'last'),
        ]

        for pattern, order in patterns:
            match = re.search(pattern, query_lower)
            if match:
                entity_type = 'issue' if 'issue' in match.group().lower() else 'pr'
                return {
                    'type': entity_type,
                    'order': order
                }

        return None

    def extract_entity_from_query(self, query: str, query_type: str) -> Optional[Dict[str, Any]]:
        query_lower = query.lower()

        if query_type == QueryType.ISSUE_SPECIFIC:
            match = re.search(r'issue\s*#?\s*(\d+)', query_lower)
            if match:
                return {'type': 'issue', 'number': int(match.group(1))}

        elif query_type == QueryType.PR_SPECIFIC:
            match = re.search(
                r'(?:pr|pull\s*request)\s*#?\s*\(?\s*(\d+)\s*\)?',
                query_lower
            )
            if match:
                return {'type': 'pr', 'number': int(match.group(1))}

        elif query_type == QueryType.COMMIT_SPECIFIC:
            match = re.search(r'commit\s+([a-f0-9]{7,40})', query_lower)
            if match:
                return {'type': 'commit', 'sha': match.group(1)}

        # NEW: Extract PR/Issue for tutorial and coding question types
        elif query_type in [QueryType.PR_ISSUE_TUTORIAL, QueryType.PR_ISSUE_CODING_QUESTION]:
            # Try to find PR number first
            pr_match = re.search(r'(?:pr|pull\s*request)\s*#?\s*(\d+)', query_lower)
            if pr_match:
                return {'type': 'pr', 'number': int(pr_match.group(1))}

            # Try to find issue number
            issue_match = re.search(r'issue\s*#?\s*(\d+)', query_lower)
            if issue_match:
                return {'type': 'issue', 'number': int(issue_match.group(1))}

        return None

    def extract_keywords(self, query: str) -> List[str]:
        stop_words = STOP_WORDS

        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return list(dict.fromkeys(keywords))

    def generate_multi_queries(self, original_query: str, query_type: str) -> List[str]:
        """
        Generate multiple optimized versions of the user query for better retrieval
        """
        multi_query_prompt = f"""You are a query optimization expert. Given a user's question about a codebase, generate 1 optimized version of the query that will retrieve the most relevant information.

        ORIGINAL QUERY: "{original_query}"
        QUERY TYPE: {query_type}

        GUIDELINES:
        1. Keep the core intent of the original query
        2. Rephrase with more specific technical terms
        3. Add relevant context keywords
        4. Make query more semantic search-friendly

        Generate 1 optimized query variation (single line, no numbering).

        OPTIMIZED QUERY:"""

        queries_text = self._call_llm_client(
            multi_query_prompt,
            system_message="You are a query optimization expert. Generate 1 optimized query variation.",
            temperature=LLM_TEMPERATURE_MEDIUM,
            max_tokens=LLM_MAX_TOKENS_STANDARD
        )

        try:
            if not queries_text:
                self.logger.info("MULTI-QUERY | Skipped (provider not OpenAI/Anthropic or call failed)")
                return [original_query]

            # Extract single query (handle both single line and multi-line responses)
            generated_queries = [q.strip() for q in queries_text.split('\n') if q.strip()]
            generated_queries = [re.sub(r'^\d+[\.\)]\s*', '', q) for q in generated_queries]
            generated_queries = [q for q in generated_queries if len(q) > 10]

            # Take first valid query, or use original if none found
            if generated_queries:
                optimized_query = generated_queries[0]
            else:
                optimized_query = original_query

            # Return only 2 queries: original + 1 optimized
            all_queries = [original_query, optimized_query]

            self.logger.info(f"MULTI-QUERY | Generated {len(all_queries)} query variations")
            for i, q in enumerate(all_queries, 1):
                self.logger.info(f"QUERY {i} | {q}")

            return all_queries

        except Exception as e:
            self.logger.error(f"MULTI-QUERY | Error generating queries: {e}")
            return [original_query]

    def llm_classify_query(self, query: str) -> str:
        classification_prompt = f"""Analyze this user query and classify it into the most appropriate category.

        USER QUERY: "{query}"

        AVAILABLE CATEGORIES:
        1. flow_architecture - Questions about system architecture, flows, diagrams, how services work together
        2. issue_specific - Questions about GitHub issues (with or without issue number)
        3. pr_specific - Questions about pull requests or code reviews
        4. commit_specific - Questions about specific commits or code changes
        5. how_to - Questions asking how to do something, step-by-step guides
        6. conceptual - Questions asking what something is, explanations, definitions
        7. troubleshooting - Questions about bugs, errors, fixes, problems
        8. FILE_LOOKUP - Questions asking where file is located, finding file
        9. repository_metrics - Questions about code statistics, lines of code, metrics
        10. tech_stack - Questions about technologies, frameworks, languages used
        11. code_structure - Questions about repository structure, organization
        12. question_generation - Requests to generate questions, quiz, MCQs, assessments
        13. pr_issue_tutorial - Requests for tutorials based on specific PRs or issues
        14. pr_issue_coding_question - Requests for coding questions/challenges based on PRs or issues
        15. random_pr_generator - Requests to randomly select/generate a PR with code changes
        16. general - Questions that don't fit above categories or are too vague
        17. impact_analysis - Questions about dependencies, what breaks if code changes, callers/callees, class hierarchy
        18. traceability - Questions about history, authorship, who changed code, evolution, timeline of changes, and linking users to code.

        Respond with ONLY the category name, nothing else.

        CATEGORY:"""

        try:
            category_text = self._call_llm_client(
                classification_prompt,
                system_message="You are a query classification expert. Respond with only the category name.",
                temperature=LLM_TEMPERATURE_LOW,
                max_tokens=LLM_MAX_TOKENS_MEDIUM
            )

            if not category_text:
                self.logger.info("LLM CLASSIFICATION | Skipped (provider not OpenAI/Anthropic or call failed)")
                return QueryType.GENERAL

            category = category_text.lower()

            valid_categories = [
                QueryType.FLOW_ARCHITECTURE,
                QueryType.ISSUE_SPECIFIC,
                QueryType.PR_SPECIFIC,
                QueryType.COMMIT_SPECIFIC,
                QueryType.HOW_TO,
                QueryType.CONCEPTUAL,
                QueryType.TROUBLESHOOTING,
                QueryType.FILE_LOOKUP,
                QueryType.REPOSITORY_METRICS,
                QueryType.TECH_STACK,
                QueryType.CODE_STRUCTURE,
                QueryType.QUESTION_GENERATION,
                QueryType.PR_ISSUE_TUTORIAL,
                QueryType.PR_ISSUE_CODING_QUESTION,
                QueryType.RANDOM_PR_GENERATOR,
                QueryType.IMPACT_ANALYSIS,
                QueryType.GENERAL,
                QueryType.TRACEABILITY
            ]

            if category in valid_categories:
                self.logger.info(f"LLM CLASSIFICATION | Success: {category}")
                return category
            else:
                self.logger.warning(f"LLM CLASSIFICATION | Invalid category '{category}', using GENERAL")
                return QueryType.GENERAL

        except Exception as e:
            self.logger.error(f"LLM CLASSIFICATION | Error: {e}")
            return QueryType.GENERAL

    def classify_query(self, query: str) -> str:
        query_lower = query.lower()

        if self.is_greeting(query):
            self.logger.info("CLASSIFICATION | Rule-based: GREETING")
            return QueryType.GREETING

        if self.is_random_pr_generator_query(query):
            self.logger.info("CLASSIFICATION | Rule-based: RANDOM_PR_GENERATOR")
            return QueryType.RANDOM_PR_GENERATOR

        if self.is_pr_issue_tutorial_query(query):
            self.logger.info("CLASSIFICATION | Rule-based: PR_ISSUE_TUTORIAL")
            return QueryType.PR_ISSUE_TUTORIAL

        if self.is_pr_issue_coding_question_query(query):
            self.logger.info("CLASSIFICATION | Rule-based: PR_ISSUE_CODING_QUESTION")
            return QueryType.PR_ISSUE_CODING_QUESTION

        if self.is_question_generation_query(query):
            self.logger.info("CLASSIFICATION | Rule-based: QUESTION_GENERATION")
            return QueryType.QUESTION_GENERATION

        if any(kw in query_lower for kw in METRICS_KEYWORDS):
            self.logger.info("CLASSIFICATION | Rule-based: REPOSITORY_METRICS")
            return QueryType.REPOSITORY_METRICS

        if any(kw in query_lower for kw in TECH_STACK_KEYWORDS):
            self.logger.info("CLASSIFICATION | Rule-based: TECH_STACK")
            return QueryType.TECH_STACK

        if any(re.search(kw, query_lower) for kw in STRUCTURE_KEYWORDS):
            self.logger.info("CLASSIFICATION | Rule-based: CODE_STRUCTURE")
            return QueryType.CODE_STRUCTURE

        if re.search(r'(issue|bug|ticket|report)\s*#?\s*(\d+)', query_lower):
            self.logger.info("CLASSIFICATION | Rule-based: ISSUE_SPECIFIC")
            return QueryType.ISSUE_SPECIFIC

        if re.search(r'(pr|pull\s*request|merge\s*request|mr|review|code\s*review)\s*#?\s*(\d+)', query_lower):
            self.logger.info("CLASSIFICATION | Rule-based: PR_SPECIFIC")
            return QueryType.PR_SPECIFIC

        if re.search(r'commit\s+[a-f0-9]{7,40}', query_lower):
            self.logger.info("CLASSIFICATION | Rule-based: COMMIT_SPECIFIC")
            return QueryType.COMMIT_SPECIFIC

        if any(re.search(kw, query_lower) for kw in FLOW_KEYWORDS):
            self.logger.info("CLASSIFICATION | Rule-based: FLOW_ARCHITECTURE")
            return QueryType.FLOW_ARCHITECTURE

        if any(kw in query_lower for kw in ['how do i', 'how to', 'how can i', 'steps to', 'guide to']):
            self.logger.info("CLASSIFICATION | Rule-based: HOW_TO")
            return QueryType.HOW_TO

        if any(kw in query_lower for kw in ['what is', 'what does', 'what are', 'explain', 'describe', 'define']):
            self.logger.info("CLASSIFICATION | Rule-based: CONCEPTUAL")
            return QueryType.CONCEPTUAL

        if any(kw in query_lower for kw in ['error', 'bug', 'fix', 'problem', 'debug', 'troubleshoot', 'not working']):
            self.logger.info("CLASSIFICATION | Rule-based: TROUBLESHOOTING")
            return QueryType.TROUBLESHOOTING

        # Enhanced file query detection - check for file-related patterns
        file_query_patterns = [
            'where is', 'where can i find', 'locate', 'find', 'which file',
            'show me', 'tell me about', 'what is in', 'what\'s in',
            'file', 'code in', 'implementation of', 'definition of',
            # File extensions
            r'\.(py|js|ts|dart|java|go|rs|cpp|c|h|hpp|md|txt|json|yaml|yml|xml|html|css|scss|less|vue|jsx|tsx|kt|swift|rb|php)',
            # Path patterns
            r'[\w\-_/\\]+\.(py|js|ts|dart|java|go|rs|cpp|c|h|hpp|md|txt|json|yaml|yml)',
            r'[\w\-_/\\]+/[\w\-_/\\]+',
        ]
        
        # Check for file path patterns
        has_file_path = any(re.search(pattern, query_lower) for pattern in file_query_patterns[4:])
        has_file_keywords = any(kw in query_lower for kw in file_query_patterns[:4])
        
        if has_file_path or has_file_keywords:
            self.logger.info("CLASSIFICATION | Rule-based: FILE_LOOKUP (file query detected)")
            return QueryType.FILE_LOOKUP
        
        if any(kw in query_lower for kw in IMPACT_KEYWORDS):
            self.logger.info("CLASSIFICATION | Rule-based: IMPACT_ANALYSIS")
            return QueryType.IMPACT_ANALYSIS
        
        if any(kw in query_lower for kw in TRACEABILITY_KEYWORDS):
            self.logger.info("CLASSIFICATION | Rule-based: TRACEABILITY")
            return QueryType.TRACEABILITY

        self.logger.info("CLASSIFICATION | No rule matched, using LLM classification")
        llm_category = self.llm_classify_query(query)
        return llm_category

    def is_random_pr_generator_query(self, query: str) -> bool:
        """
        Detect if the query is requesting a random PR generation.
        """
        query_lower = query.lower().strip()

        for pattern in RANDOM_PR_PATTERNS:
            if re.search(pattern, query_lower):
                return True

        return False

    def rewrite_query_with_llm(self, query: str) -> str:
        """
        Use LLM to rewrite/improve the user's query for better retrieval.
        Makes the query clearer, more specific, and better suited for semantic search.
        """
        try:
            # Skip rewriting for greetings - they should be handled separately
            if self.is_greeting(query):
                return query

            # Skip rewriting for Random PR Generator queries
            if self.is_random_pr_generator_query(query):
                self.logger.info("QUERY REWRITE | Skipped (Random PR generator query)")
                return query

            # Skip rewriting for tutorial generation queries
            if self.is_pr_issue_tutorial_query(query):
                self.logger.info("QUERY REWRITE | Skipped (PR/Issue tutorial query)")
                return query

            # Skip rewriting for coding question generation queries
            if self.is_pr_issue_coding_question_query(query):
                self.logger.info("QUERY REWRITE | Skipped (PR/Issue coding question query)")
                return query

            # Skip rewriting for question generation
            if self.is_question_generation_query(query):
                self.logger.info("QUERY REWRITE | Skipped (question generation query)")
                return query

            # Skip rewriting for very short queries that are already clear
            # This prevents over-rewriting simple queries
            words = query.strip().split()
            if len(words) <= SHORT_QUERY_MAX_WORDS and len(query.strip()) <= SHORT_QUERY_MAX_LENGTH:
                # Only rewrite if it seems unclear or needs expansion
                # Simple queries like "how to", "where is" might benefit, but "hi", "help" shouldn't
                if query.lower().strip() in SIMPLE_QUERIES:
                    return query

            if self.provider not in ['openai', 'anthropic']:
                # Fallback to simple expansion if LLM not available
                return self.expand_query(query)

            rewrite_prompt = f"""Rewrite the following user question to make it clearer, more specific, and better suited for searching a codebase. 

                IMPORTANT: Keep the original intent and meaning EXACTLY. Only make minor improvements:
                1. Make it slightly more explicit if needed (but don't change the core question)
                2. Add relevant technical terms ONLY if they're clearly missing and would help search
                3. Clarify ambiguous terms ONLY if necessary
                4. Keep it concise (1-2 sentences max)
                5. Preserve ALL specific file names, function names, or technical terms mentioned
                6. DO NOT add examples or change the question into something different
                7. If the question is already clear, return it as-is

                Original question: "{query}"

                Rewritten question (respond with ONLY the rewritten question, no explanations):"""

            rewritten = self._call_llm_client(
                rewrite_prompt,
                system_message="You are a helpful assistant that rewrites questions to be clearer and more searchable.",
                temperature=LLM_TEMPERATURE_MEDIUM,
                max_tokens=LLM_MAX_TOKENS_LONG
            )

            if not rewritten:
                return self.expand_query(query)

            # Clean up the response (remove quotes if present)
            rewritten = rewritten.strip('"').strip("'").strip()

            if rewritten and rewritten != query:
                # Validate that the rewritten query is not too different from the original
                # Check if it's more than threshold longer (likely added too much)
                if len(rewritten) > len(query) * QUERY_LENGTH_MULTIPLIER_THRESHOLD:
                    self.logger.warning(
                        f"QUERY REWRITE | Rewritten query too long, using original. Original: {len(query)} chars, Rewritten: {len(rewritten)} chars")
                    return query

                # Check word overlap - if less than threshold of original words are in rewritten, it's too different
                original_words = set(query.lower().split())
                rewritten_words = set(rewritten.lower().split())
                if original_words and rewritten_words:
                    overlap = len(original_words & rewritten_words) / len(original_words)
                    if overlap < WORD_OVERLAP_THRESHOLD:
                        self.logger.warning(
                            f"QUERY REWRITE | Rewritten query too different (overlap: {overlap:.2f}), using original")
                        return query

                # Log rewrite internals at debug level to avoid duplicate INFO-level entries
                # The top-level chat pipeline will emit one INFO-level 'QUERY REWRITE' entry.
                self.logger.debug(f"QUERY REWRITE | Original: '{query}' -> Rewritten: '{rewritten}'")
                return rewritten
            else:
                return query

        except Exception as e:
            self.logger.warning(f"QUERY REWRITE | Failed to rewrite query: {e}, using original")
            return self.expand_query(query) 
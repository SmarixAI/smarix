"""
Metadata Enricher with Hierarchical Context
Adds rich context and semantic metadata to chunks for better retrieval
"""

from typing import Dict, List, Any, Set, Optional
import re
from collections import defaultdict
from datetime import datetime


class MetadataEnricher:
    """
    Enriches chunks with:
    - Hierarchical context (local -> file -> module -> system)
    - Semantic tags (onboarding/offboarding/technical/domain)
    - Entity extraction (functions, classes, APIs, people)
    - Execution context and flow
    - Relationship mapping
    - Potential Q&A patterns
    - Search keywords
    """
    
    def __init__(self, repo_data: Dict[str, Any]):
        self.repo_data = repo_data
        self.metadata = repo_data.get('metadata', {})
        
        self.file_index = self._build_file_index()
        self.expert_index = self._build_expert_index()
        self.api_index = self._build_api_index()
        self.tech_stack = self._extract_tech_stack()
        self.file_modules = self._build_module_map()
        
        self.onboarding_keywords = {
            'setup', 'install', 'configure', 'getting started', 'quick start',
            'prerequisites', 'requirements', 'environment', 'dependencies',
            'build', 'run', 'deploy', 'test', 'development'
        }
        
        self.offboarding_keywords = {
            'todo', 'fixme', 'hack', 'workaround', 'gotcha', 'careful',
            'warning', 'note', 'important', 'attention', 'decided', 'because',
            'reason', 'why', 'business', 'domain', 'debt', 'refactor'
        }
        
        self.technical_keywords = {
            'algorithm', 'optimization', 'performance', 'security', 'scalability',
            'architecture', 'design pattern', 'implementation', 'complexity',
            'efficiency', 'caching', 'threading', 'async', 'sync'
        }
    
    def enrich_chunk(self, chunk: 'Chunk') -> Dict[str, Any]:
        """
        Enrich a chunk with comprehensive metadata including hierarchical context
        
        Returns enriched metadata dictionary
        """
        enriched = {
            **chunk.metadata,
            'chunk_id': chunk.chunk_id,
            'chunk_type': chunk.chunk_type.value,  # Standard field
            'type': chunk.chunk_type.value,  # Alias for backward compat
            'importance_score': chunk.importance_score,
            'tokens': chunk.tokens,
            
            # NEW: Hierarchical context (critical for architectural understanding)
            'hierarchical_context': self._build_hierarchical_context(chunk),
            
            # NEW: Execution context
            'execution_context': self._extract_execution_context(chunk),
            
            # NEW: Usage examples and patterns
            'usage_patterns': self._extract_usage_patterns(chunk),
            
            # NEW: Potential questions this chunk answers
            'potential_questions': self._generate_potential_questions(chunk),
            
            # Existing enrichments (enhanced)
            'semantic_tags': self._extract_semantic_tags(chunk),
            'category': self._categorize_content(chunk),
            'user_intent': self._infer_user_intent(chunk),
            
            'entities': self._extract_entities(chunk),
            'mentioned_files': self._extract_file_references(chunk),
            'mentioned_people': self._extract_people(chunk),
            'mentioned_apis': self._extract_api_references(chunk),
            
            'related_chunks': self._find_related_chunks(chunk),
            'keywords': self._extract_keywords(chunk),
            'tech_stack': self._identify_tech_in_chunk(chunk),
            
            # NEW: Architectural role
            'architectural_role': self._determine_architectural_role(chunk),
            'code_patterns': self._detect_code_patterns(chunk),
            
            'timestamp': self._extract_timestamp(chunk),
            'recency_score': self._calculate_recency_score(chunk),
            
            'search_terms': self._generate_search_terms(chunk),
            'question_patterns': self._generate_question_patterns(chunk)
        }
        
        return enriched
    
    # ========== NEW: HIERARCHICAL CONTEXT ==========
    
    def _build_hierarchical_context(self, chunk: 'Chunk') -> Dict[str, Any]:
        """
        Build multi-level hierarchical context
        This is CRITICAL for LLM to understand both code AND architecture
        """
        context = {
            'local': {},      # Function/class level
            'file': {},       # File level
            'module': {},     # Module/package level
            'system': {}      # System/architecture level
        }
        
        # LOCAL CONTEXT: What is this specific chunk?
        if chunk.chunk_type.value == 'function':
            context['local'] = {
                'type': 'function',
                'name': chunk.metadata.get('function_name'),
                'purpose': chunk.metadata.get('purpose', ''),
                'params': chunk.metadata.get('params', []),
                'returns': chunk.metadata.get('returns', ''),
                'complexity': chunk.metadata.get('complexity', 0),
                'is_entry_point': chunk.metadata.get('is_entry_point', False),
                'calls': chunk.metadata.get('calls_functions', [])
            }
        elif chunk.chunk_type.value == 'method':
            context['local'] = {
                'type': 'method',
                'name': chunk.metadata.get('method_name'),
                'class': chunk.metadata.get('class_name'),
                'full_name': chunk.metadata.get('full_name'),
                'method_type': chunk.metadata.get('method_type'),
                'purpose': chunk.metadata.get('purpose', '')
            }
        elif chunk.chunk_type.value == 'class':
            context['local'] = {
                'type': 'class',
                'name': chunk.metadata.get('class_name'),
                'methods': chunk.metadata.get('methods', []),
                'attributes': chunk.metadata.get('attributes', []),
                'inheritance': chunk.metadata.get('bases', []),
                'purpose': chunk.metadata.get('purpose', '')
            }
        elif chunk.chunk_type.value == 'file_overview':
            context['local'] = {
                'type': 'file_overview',
                'contains': chunk.metadata.get('contains', {})
            }
        
        # FILE CONTEXT: What file is this in and what's its role?
        from utils.path_normalizer import normalize_path, extract_filename, extract_directory
        file_path_raw = chunk.metadata.get('file_path', '')
        if file_path_raw:
            # Normalize path for consistent access
            file_path = normalize_path(file_path_raw, '') or file_path_raw
            context['file'] = {
                'path': file_path,
                'name': extract_filename(file_path) or file_path.split('/')[-1] if '/' in file_path else file_path,
                'directory': extract_directory(file_path) or '/'.join(file_path.split('/')[:-1]) if '/' in file_path else '',
                'language': chunk.metadata.get('language', 'unknown'),
                'role': self._infer_file_role_from_path(file_path),
                'dependencies': self._get_file_dependencies(file_path),
                'expert': self.expert_index.get(file_path, 'unknown')
            }
        
        # MODULE CONTEXT: What module/package is this part of?
        module_name = self._get_module_name(file_path)
        context['module'] = {
            'name': module_name,
            'type': self._classify_module_type(file_path),
            'related_files': self._find_related_files(file_path)[:5],
            'purpose': self._infer_module_purpose(file_path)
        }
        
        # SYSTEM CONTEXT: How does this fit in the overall architecture?
        context['system'] = {
            'architecture_layer': self._determine_architecture_layer(file_path),
            'design_patterns': self._detect_code_patterns(chunk),
            'tech_stack': self._identify_tech_in_chunk(chunk),
            'is_core': self._is_core_component(file_path),
            'api_exposure': self._check_api_exposure(chunk)
        }
        
        return context
    
    # ========== NEW: EXECUTION CONTEXT ==========
    
    def _extract_execution_context(self, chunk: 'Chunk') -> Dict[str, Any]:
        """Extract how the code is executed and used"""
        context = {
            'entry_points': [],
            'prerequisites': [],
            'side_effects': [],
            'error_handling': False,
            'async_behavior': False
        }
        
        content_lower = chunk.content.lower()
        
        # Entry points
        if chunk.metadata.get('is_entry_point'):
            context['entry_points'].append(chunk.metadata.get('function_name'))
        
        if 'if __name__ == "__main__"' in chunk.content:
            context['entry_points'].append('__main__')
        
        # Prerequisites
        if chunk.metadata.get('params'):
            context['prerequisites'].extend([f"param: {p}" for p in chunk.metadata['params']])
        
        if 'environment' in content_lower or 'config' in content_lower:
            context['prerequisites'].append('configuration required')
        
        # Side effects
        if any(word in content_lower for word in ['write', 'delete', 'update', 'create', 'save']):
            context['side_effects'].append('modifies state')
        
        if 'database' in content_lower or 'db' in content_lower:
            context['side_effects'].append('database interaction')
        
        if 'api' in content_lower or 'request' in content_lower:
            context['side_effects'].append('external API call')
        
        # Error handling
        if any(word in content_lower for word in ['try', 'except', 'catch', 'error']):
            context['error_handling'] = True
        
        # Async behavior
        if chunk.metadata.get('is_async') or 'async' in content_lower or 'await' in content_lower:
            context['async_behavior'] = True
        
        return context
    
    # ========== NEW: USAGE PATTERNS ==========
    
    def _extract_usage_patterns(self, chunk: 'Chunk') -> Dict[str, Any]:
        """Extract usage patterns and examples"""
        patterns = {
            'how_to_call': '',
            'common_use_cases': [],
            'parameters_example': {},
            'related_usage': []
        }
        
        # For functions
        if chunk.chunk_type.value in ['function', 'method']:
            func_name = chunk.metadata.get('function_name') or chunk.metadata.get('method_name')
            params = chunk.metadata.get('params', [])
            
            if func_name:
                if params:
                    patterns['how_to_call'] = f"{func_name}({', '.join(params)})"
                else:
                    patterns['how_to_call'] = f"{func_name}()"
                
                # Extract from docstring if available
                if '```' in chunk.content:
                    # Extract code examples
                    code_blocks = re.findall(r'``````', chunk.content, re.DOTALL)
                    if code_blocks:
                        patterns['common_use_cases'] = code_blocks[:2]
        
        return patterns
    
    # ========== NEW: POTENTIAL QUESTIONS ==========
    
    def _generate_potential_questions(self, chunk: 'Chunk') -> List[str]:
        """
        Generate specific questions this chunk can answer
        This helps with retrieval matching
        """
        questions = []
        
        # Function/Method questions
        if chunk.chunk_type.value == 'function':
            func_name = chunk.metadata.get('function_name', '')
            if func_name:
                questions.extend([
                    f"What does {func_name} do?",
                    f"How do I use {func_name}?",
                    f"What parameters does {func_name} accept?",
                    f"What does {func_name} return?",
                    f"How does {func_name} work?",
                    f"Where is {func_name} defined?"
                ])
                
                # Specific to purpose
                purpose = chunk.metadata.get('purpose', '').lower()
                if 'authenticate' in purpose or 'auth' in func_name.lower():
                    questions.append("How do I authenticate?")
                    questions.append("What is the authentication flow?")
                
                if 'database' in purpose or 'db' in func_name.lower():
                    questions.append("How do I connect to the database?")
                    questions.append("How do I query the database?")
        
        elif chunk.chunk_type.value == 'method':
            class_name = chunk.metadata.get('class_name', '')
            method_name = chunk.metadata.get('method_name', '')
            if class_name and method_name:
                questions.extend([
                    f"How do I use {class_name}.{method_name}?",
                    f"What does {class_name}.{method_name} do?",
                    f"How do I call {method_name} on {class_name}?"
                ])
        
        elif chunk.chunk_type.value == 'class':
            class_name = chunk.metadata.get('class_name', '')
            if class_name:
                questions.extend([
                    f"What is {class_name}?",
                    f"How do I create a {class_name} instance?",
                    f"What methods does {class_name} have?",
                    f"What is {class_name} used for?",
                    f"How do I use {class_name}?"
                ])
        
        elif chunk.chunk_type.value == 'file_overview':
            from utils.path_normalizer import normalize_path, extract_filename
            file_path_raw = chunk.metadata.get('file_path', '')
            if file_path_raw:
                file_path = normalize_path(file_path_raw, '') or file_path_raw
                file_name = extract_filename(file_path) or file_path.split('/')[-1] if '/' in file_path else file_path
                questions.extend([
                    f"What is in {file_name}?",
                    f"What does {file_name} do?",
                    f"Where is {file_name}?"
                ])
        
        # Domain-specific questions
        content_lower = chunk.content.lower()
        
        if 'setup' in content_lower or 'install' in content_lower:
            questions.extend([
                "How do I set up the development environment?",
                "How do I install dependencies?",
                "What are the setup steps?"
            ])
        
        if 'authentication' in content_lower or 'login' in content_lower:
            questions.extend([
                "How do I authenticate API calls?",
                "What authentication method is used?",
                "How does login work?"
            ])
        
        if 'api' in content_lower and 'endpoint' in content_lower:
            questions.extend([
                "What API endpoints are available?",
                "How do I call the API?",
                "What is the API structure?"
            ])
        
        if 'payment' in content_lower or 'checkout' in content_lower:
            questions.extend([
                "How does payment processing work?",
                "How do I implement checkout?"
            ])
        
        if 'environment' in content_lower and 'variable' in content_lower:
            questions.extend([
                "What environment variables are needed?",
                "How do I configure environment variables?"
            ])
        
        return list(set(questions))[:10]  # Limit to 10 unique questions
    
    # ========== NEW: ARCHITECTURAL ANALYSIS ==========
    
    def _determine_architectural_role(self, chunk: 'Chunk') -> str:
        """Determine the architectural role of this chunk"""
        file_path = chunk.metadata.get('file_path', '').lower()
        content_lower = chunk.content.lower()
        
        # API Layer
        if any(pattern in file_path for pattern in ['api', 'endpoint', 'route', 'controller']):
            return 'API Layer'
        if any(word in content_lower for word in ['@app.route', '@api', 'fastapi', 'flask']):
            return 'API Layer'
        
        # Data Layer
        if any(pattern in file_path for pattern in ['model', 'schema', 'database', 'repository']):
            return 'Data Layer'
        if any(word in content_lower for word in ['sqlalchemy', 'database', 'query', 'orm']):
            return 'Data Layer'
        
        # Business Logic
        if any(pattern in file_path for pattern in ['service', 'business', 'logic', 'handler']):
            return 'Business Logic'
        
        # Presentation/View
        if any(pattern in file_path for pattern in ['view', 'template', 'ui', 'frontend']):
            return 'Presentation Layer'
        
        # Infrastructure
        if any(pattern in file_path for pattern in ['config', 'settings', 'infrastructure', 'deployment']):
            return 'Infrastructure'
        
        # Testing
        if 'test' in file_path:
            return 'Testing'
        
        # Utilities
        if any(pattern in file_path for pattern in ['util', 'helper', 'common']):
            return 'Utilities'
        
        return 'General'
    
    def _detect_code_patterns(self, chunk: 'Chunk') -> List[str]:
        """Detect design patterns and code patterns"""
        patterns = []
        content_lower = chunk.content.lower()
        
        # Design patterns
        if 'singleton' in content_lower:
            patterns.append('Singleton Pattern')
        if 'factory' in content_lower:
            patterns.append('Factory Pattern')
        if 'decorator' in content_lower and '@' in chunk.content:
            patterns.append('Decorator Pattern')
        if 'observer' in content_lower or 'subscribe' in content_lower:
            patterns.append('Observer Pattern')
        if 'strategy' in content_lower:
            patterns.append('Strategy Pattern')
        
        # Architectural patterns
        if 'middleware' in content_lower:
            patterns.append('Middleware')
        if 'dependency injection' in content_lower:
            patterns.append('Dependency Injection')
        if 'repository' in content_lower:
            patterns.append('Repository Pattern')
        
        # Code patterns
        if chunk.metadata.get('is_async'):
            patterns.append('Async/Await')
        if 'context manager' in content_lower or 'with ' in chunk.content:
            patterns.append('Context Manager')
        
        return patterns
    
    def _infer_file_role_from_path(self, file_path: str) -> str:
        """Infer file role from path"""
        path_lower = file_path.lower()
        
        if 'test' in path_lower:
            return 'Test File'
        elif any(word in path_lower for word in ['config', 'settings']):
            return 'Configuration'
        elif any(word in path_lower for word in ['model', 'schema']):
            return 'Data Model'
        elif any(word in path_lower for word in ['api', 'endpoint', 'route']):
            return 'API Handler'
        elif any(word in path_lower for word in ['service', 'business']):
            return 'Business Logic'
        elif any(word in path_lower for word in ['util', 'helper']):
            return 'Utility'
        elif any(word in path_lower for word in ['view', 'template']):
            return 'View/Template'
        
        return 'General'
    
    def _is_core_component(self, file_path: str) -> bool:
        """Check if this is a core/critical component"""
        # Check if in main source directory (not tests, docs, etc.)
        if any(word in file_path.lower() for word in ['test', 'doc', 'example', 'demo']):
            return False
        
        # Check if it's a main entry point
        if 'main' in file_path.lower() or '__init__' in file_path:
            return True
        
        # Check if it's in core directories
        if any(word in file_path for word in ['core', 'app', 'src', 'lib']):
            return True
        
        return False
    
    def _check_api_exposure(self, chunk: 'Chunk') -> str:
        """Check if this code exposes an API"""
        content = chunk.content
        
        # HTTP endpoints
        if any(word in content for word in ['@app.route', '@api', 'app.get', 'app.post']):
            return 'HTTP API'
        
        # GraphQL
        if 'graphql' in content.lower():
            return 'GraphQL API'
        
        # Public methods/functions
        if chunk.chunk_type.value in ['function', 'method']:
            if not chunk.metadata.get('is_private', False):
                return 'Public API'
        
        return 'Internal'
    
    # ========== ENHANCED EXISTING METHODS ==========
    
    def _extract_semantic_tags(self, chunk: 'Chunk') -> List[str]:
        """Extract semantic tags for the chunk"""
        tags = []
        content_lower = chunk.content.lower()
        
        # Onboarding tags
        onboarding_count = sum(1 for kw in self.onboarding_keywords if kw in content_lower)
        if onboarding_count >= 2:
            tags.append('onboarding')
        
        # Offboarding tags
        offboarding_count = sum(1 for kw in self.offboarding_keywords if kw in content_lower)
        if offboarding_count >= 2:
            tags.append('offboarding')
        
        # Technical tags
        technical_count = sum(1 for kw in self.technical_keywords if kw in content_lower)
        if technical_count >= 1:
            tags.append('technical')
        
        # Specific tags based on chunk type
        if chunk.chunk_type.value in ['function', 'method']:
            tags.append('executable_code')
            if chunk.metadata.get('has_docstring'):
                tags.append('documented')
            if chunk.metadata.get('complexity', 0) > 5:
                tags.append('complex')
        
        elif chunk.chunk_type.value == 'class':
            tags.append('class_definition')
            tags.append('object_oriented')
        
        elif chunk.chunk_type.value == 'file_overview':
            tags.append('overview')
            tags.append('architecture')
        
        elif chunk.chunk_type.value == 'documentation':
            if chunk.metadata.get('is_setup'):
                tags.append('setup_guide')
            if chunk.metadata.get('is_api_doc'):
                tags.append('api_documentation')
        
        elif chunk.chunk_type.value == 'issue':
            if chunk.metadata.get('is_solved'):
                tags.append('resolved_issue')
            if 'bug' in chunk.metadata.get('labels', []):
                tags.append('bug_report')
        
        # NEW: Context-specific tags
        if chunk.metadata.get('is_entry_point'):
            tags.append('entry_point')
        
        if chunk.metadata.get('is_async'):
            tags.append('asynchronous')
        
        return list(set(tags))
    
    def _categorize_content(self, chunk: 'Chunk') -> str:
        """Categorize chunk into main category"""
        content_lower = chunk.content.lower()
        
        # Category scoring
        categories = {
            'setup_configuration': 0,
            'code_implementation': 0,
            'api_documentation': 0,
            'troubleshooting': 0,
            'architecture': 0,
            'business_logic': 0,
            'knowledge_transfer': 0
        }
        
        # Setup/Configuration
        if any(kw in content_lower for kw in ['setup', 'install', 'configure', 'environment']):
            categories['setup_configuration'] += 3
        
        # Code Implementation
        if chunk.chunk_type.value in ['function', 'method', 'class', 'code']:
            categories['code_implementation'] += 3
        if any(kw in content_lower for kw in ['function', 'class', 'method', 'implement']):
            categories['code_implementation'] += 2
        
        # API
        if any(kw in content_lower for kw in ['endpoint', 'api', 'request', 'response']):
            categories['api_documentation'] += 3
        
        # Troubleshooting
        if any(kw in content_lower for kw in ['error', 'fix', 'bug', 'issue', 'problem']):
            categories['troubleshooting'] += 3
        
        # Architecture
        if any(kw in content_lower for kw in ['architecture', 'design', 'structure', 'pattern']):
            categories['architecture'] += 3
        if chunk.chunk_type.value == 'file_overview':
            categories['architecture'] += 2
        
        # Business Logic
        if any(kw in content_lower for kw in ['business', 'requirement', 'user', 'customer']):
            categories['business_logic'] += 2
        
        # Knowledge Transfer
        if any(kw in content_lower for kw in ['because', 'reason', 'why', 'gotcha', 'important']):
            categories['knowledge_transfer'] += 2
        
        return max(categories.items(), key=lambda x: x[1])[0] if max(categories.values()) > 0 else 'general'
    
    def _infer_user_intent(self, chunk: 'Chunk') -> List[str]:
        """Infer what kind of questions this chunk can answer"""
        intents = []
        content_lower = chunk.content.lower()
        
        # "How to" questions
        if any(kw in content_lower for kw in ['setup', 'install', 'configure', 'run', 'deploy']):
            intents.append('how_to')
        
        # "What is" questions
        if chunk.chunk_type.value in ['class', 'function', 'method', 'file_overview']:
            intents.append('what_is')
        
        # "Where is" questions
        if chunk.chunk_type.value in ['function', 'method', 'class']:
            intents.append('where_is')
        
        # "Why" questions
        if any(kw in content_lower for kw in ['because', 'reason', 'decided', 'chosen']):
            intents.append('why')
        
        # "Who" questions
        if chunk.chunk_type.value in ['issue', 'pull_request', 'commit']:
            intents.append('who')
        
        # "When" questions
        if chunk.metadata.get('created_at') or chunk.metadata.get('timestamp'):
            intents.append('when')
        
        return intents
    
    # [Keep all existing methods: _extract_entities, _extract_file_references, etc.]
    # (copying the rest of your original methods here...)
    
    def _extract_entities(self, chunk: 'Chunk') -> Dict[str, List[str]]:
        """Extract named entities from chunk"""
        entities = {
            'functions': [],
            'classes': [],
            'variables': [],
            'modules': [],
            'technologies': []
        }
        
        content = chunk.content
        
        # Extract from metadata first (more accurate)
        if chunk.metadata.get('function_name'):
            entities['functions'].append(chunk.metadata['function_name'])
        if chunk.metadata.get('class_name'):
            entities['classes'].append(chunk.metadata['class_name'])
        if chunk.metadata.get('calls_functions'):
            entities['functions'].extend(chunk.metadata['calls_functions'])
        
        # Extract function names
        function_patterns = [
            r'def\s+(\w+)',  # Python
            r'function\s+(\w+)',  # JavaScript
            r'func\s+(\w+)',  # Go
            r'(\w+)\s*\([^)]*\)\s*{',  # C/Java style
        ]
        for pattern in function_patterns:
            entities['functions'].extend(re.findall(pattern, content))
        
        # Extract class names
        class_patterns = [
            r'class\s+(\w+)',
            r'interface\s+(\w+)',
            r'struct\s+(\w+)'
        ]
        for pattern in class_patterns:
            entities['classes'].extend(re.findall(pattern, content))
        
        # Extract module/import names
        import_patterns = [
            r'import\s+(\w+)',
            r'from\s+(\w+)\s+import',
            r'require\([\'"]([^\'"]+)[\'"]\)'
        ]
        for pattern in import_patterns:
            entities['modules'].extend(re.findall(pattern, content))
        
        # Extract technology mentions
        for tech in self.tech_stack:
            if tech.lower() in content.lower():
                entities['technologies'].append(tech)
        
        # Deduplicate and limit
        for key in entities:
            entities[key] = list(set(entities[key]))[:10]
        
        return entities
    
    def _extract_file_references(self, chunk: 'Chunk') -> List[str]:
        """Extract references to other files"""
        file_refs = []
        content = chunk.content
        
        # Look for file path patterns
        file_patterns = [
            r'[\w\/]+\.\w{2,4}',  # path/to/file.ext
            r'`([^`]+\.\w+)`',  # `filename.ext`
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, content)
            file_refs.extend(matches)
        
        # Check against known files
        known_files = []
        for ref in file_refs:
            if ref in self.file_index:
                known_files.append(ref)
        
        return list(set(known_files))[:10]
    
    def _extract_people(self, chunk: 'Chunk') -> List[str]:
        """Extract mentions of people (authors, contributors)"""
        people = []
        
        # From metadata
        if chunk.chunk_type.value in ['issue', 'pull_request']:
            user = chunk.metadata.get('user', {}) or chunk.metadata.get('author', {})
            if isinstance(user, dict):
                login = user.get('login')
                if login:
                    people.append(login)
        
        elif chunk.chunk_type.value == 'commit':
            author = chunk.metadata.get('author', {})
            if isinstance(author, dict):
                name = author.get('name')
                if name:
                    people.append(name)
        
        # Extract mentions
        mentions = re.findall(r'@(\w+)', chunk.content)
        people.extend(mentions)
        
        return list(set(people))[:5]
    
    def _extract_api_references(self, chunk: 'Chunk') -> List[str]:
        """Extract API endpoint references"""
        api_refs = []
        content = chunk.content
        
        # HTTP method patterns
        http_patterns = [
            r'(GET|POST|PUT|DELETE|PATCH)\s+/[\w/{}:-]+',
            r'@app\.route\([\'"]([^\'"]+)[\'"]',
            r'app\.(get|post|put|delete)\([\'"]([^\'"]+)[\'"]',
        ]
        
        for pattern in http_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    api_refs.append(' '.join(match))
                else:
                    api_refs.append(match)
        
        # Check against known APIs
        for api in self.api_index:
            if api in content:
                api_refs.append(api)
        
        return list(set(api_refs))[:10]
    
    def _find_related_chunks(self, chunk: 'Chunk') -> List[str]:
        """Find IDs of related chunks"""
        related = []
        
        # Parent-child relationship
        if chunk.parent_id:
            related.append(chunk.parent_id)
        
        # Issue-PR-Commit relationships
        if chunk.chunk_type.value == 'issue':
            for pr in chunk.metadata.get('referenced_prs', []):
                related.append(f"pr_{pr}")
        
        elif chunk.chunk_type.value == 'pull_request':
            for issue in chunk.metadata.get('linked_issues', []):
                related.append(f"issue_{issue}")
            for file in chunk.metadata.get('changed_files', [])[:5]:
                related.append(f"code_{file}")
        
        elif chunk.chunk_type.value == 'commit':
            for issue in chunk.metadata.get('linked_issues', []):
                related.append(f"issue_{issue}")
            for pr in chunk.metadata.get('linked_prs', []):
                related.append(f"pr_{pr}")
        
        return list(set(related))[:20]
    
    def _extract_keywords(self, chunk: 'Chunk') -> List[str]:
        """Extract important keywords for search"""
        keywords = set()
        content_lower = chunk.content.lower()
        
        # Add semantic tag keywords
        keywords.update(self.onboarding_keywords & set(content_lower.split()))
        keywords.update(self.offboarding_keywords & set(content_lower.split()))
        keywords.update(self.technical_keywords & set(content_lower.split()))
        
        # Add entities
        for entity_list in self._extract_entities(chunk).values():
            keywords.update(entity_list)
        
        # Add tech stack
        keywords.update(self._identify_tech_in_chunk(chunk))
        
        # Add metadata keywords
        if chunk.metadata.get('language'):
            keywords.add(chunk.metadata['language'])
        
        if chunk.metadata.get('labels'):
            keywords.update(chunk.metadata['labels'])
        
        # Add from hierarchical context
        if chunk.metadata.get('function_name'):
            keywords.add(chunk.metadata['function_name'])
        if chunk.metadata.get('class_name'):
            keywords.add(chunk.metadata['class_name'])
        
        # Filter short keywords
        keywords = {k for k in keywords if len(k) > 2}
        return sorted(list(keywords))[:30]
    
    def _identify_tech_in_chunk(self, chunk: 'Chunk') -> List[str]:
        """Identify technologies mentioned in chunk"""
        techs = []
        content_lower = chunk.content.lower()
        
        for tech in self.tech_stack:
            if tech.lower() in content_lower:
                techs.append(tech)
        
        return techs
    
    def _extract_timestamp(self, chunk: 'Chunk') -> Optional[str]:
        """Extract or infer timestamp"""
        for field in ['created_at', 'updated_at', 'timestamp']:
            if chunk.metadata.get(field):
                return chunk.metadata[field]
        return None
    
    def _calculate_recency_score(self, chunk: 'Chunk') -> float:
        """Calculate recency score (1.0 = very recent, 0.0 = old)"""
        timestamp = self._extract_timestamp(chunk)
        if not timestamp:
            return 0.5
        
        try:
            if 'T' in timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(timestamp, '%Y-%m-%d')
            
            days_ago = (datetime.now() - dt.replace(tzinfo=None)).days
            
            if days_ago < 30:
                return 1.0
            elif days_ago < 180:
                return 0.8
            elif days_ago < 365:
                return 0.5
            else:
                return 0.2
        except:
            return 0.5
    
    def _generate_search_terms(self, chunk: 'Chunk') -> List[str]:
        """Generate search terms optimized for retrieval"""
        terms = set()
        
        # Add chunk type
        terms.add(chunk.chunk_type.value)
        
        # Add category
        category = self._categorize_content(chunk)
        terms.add(category)
        
        # Add semantic tags
        terms.update(self._extract_semantic_tags(chunk))
        
        # Add file path components
        from utils.path_normalizer import normalize_path
        file_path_raw = chunk.metadata.get('file_path', '')
        if file_path_raw:
            file_path = normalize_path(file_path_raw, '') or file_path_raw
            parts = file_path.split('/')
            terms.update(parts)
        
        # Add title/header
        for field in ['title', 'section_header', 'function_name', 'class_name', 'method_name']:
            if chunk.metadata.get(field):
                value = chunk.metadata[field]
                if isinstance(value, str):
                    terms.update(value.lower().split())
        
        # Add keywords
        terms.update(self._extract_keywords(chunk))
        
        return sorted(list(terms))[:50]
    
    def _generate_question_patterns(self, chunk: 'Chunk') -> List[str]:
        """Generate question patterns this chunk can answer"""
        patterns = []
        
        # Based on user intent
        intents = self._infer_user_intent(chunk)
        
        if 'how_to' in intents:
            patterns.extend(["how to", "how do i", "how can i"])
        
        if 'what_is' in intents:
            patterns.extend(["what is", "what does", "explain"])
        
        if 'where_is' in intents:
            patterns.extend(["where is", "where can i find", "location of"])
        
        if 'why' in intents:
            patterns.extend(["why", "reason for", "purpose of"])
        
        if 'who' in intents:
            patterns.extend(["who", "author", "contributor"])
        
        # Specific patterns based on chunk type
        if chunk.chunk_type.value in ['function', 'method']:
            patterns.extend(["function definition", "how does function work", "function usage"])
        
        if chunk.chunk_type.value == 'class':
            patterns.extend(["class structure", "class implementation", "class methods"])
        
        if chunk.chunk_type.value == 'file_overview':
            patterns.extend(["file overview", "file structure", "what's in file"])
        
        if chunk.chunk_type.value == 'documentation':
            if chunk.metadata.get('is_setup'):
                patterns.extend(["setup instructions", "installation guide", "getting started"])
            if chunk.metadata.get('is_api_doc'):
                patterns.extend(["api documentation", "endpoint details", "api usage"])
        
        return list(set(patterns))
    
    # ========== HELPER INDEX BUILDERS ==========
    
    def _build_file_index(self) -> Set[str]:
        """Build index of all files in repository"""
        files = set()
        for file_data in self.repo_data.get('code_files', []):
            if file_data.get('path'):
                files.add(file_data['path'])
        for file_data in self.repo_data.get('documentation', []):
            if file_data.get('path'):
                files.add(file_data['path'])
        return files
    
    def _build_expert_index(self) -> Dict[str, str]:
        """Build index of file ownership"""
        expert_map = {}
        dev_summary = self.repo_data.get('developer_summary', {})
        ownership = dev_summary.get('ownership_map', {})
        
        for file_path, expert in ownership.items():
            expert_map[file_path] = expert
        
        return expert_map
    
    def _build_api_index(self) -> Set[str]:
        """Build index of API endpoints"""
        apis = set()
        
        # From architecture data
        architecture = self.repo_data.get('architecture', {})
        for endpoint in architecture.get('api_endpoints', []):
            if endpoint.get('path'):
                apis.add(endpoint['path'])
        
        # From onboarding data
        onboarding = self.repo_data.get('onboarding', {})
        for api_doc in onboarding.get('api_documentation', []):
            if api_doc.get('endpoint'):
                apis.add(api_doc['endpoint'])
        
        return apis
    
    def _extract_tech_stack(self) -> List[str]:
        """Extract technology stack from repository data"""
        tech_stack = set()
        
        # From metadata
        metadata = self.repo_data.get('metadata', {})
        if metadata.get('language'):
            tech_stack.add(metadata['language'])
        
        tech_stack.update(metadata.get('topics', []))
        tech_stack.update(self.repo_data.get('technology_stack', []))
        
        # From architecture
        architecture = self.repo_data.get('architecture', {})
        tech_stack.update(architecture.get('frameworks', {}).keys())
        
        return sorted(list(tech_stack))
    
    def _build_module_map(self) -> Dict[str, List[str]]:
        """Build map of modules to files"""
        module_map = defaultdict(list)
        
        for file_path in self.file_index:
            module = self._get_module_name(file_path)
            module_map[module].append(file_path)
        
        return dict(module_map)
    
    def _get_module_name(self, file_path: str) -> str:
        """Extract module name from file path"""
        if not file_path:
            return 'unknown'
        
        parts = file_path.split('/')
        if len(parts) > 1:
            return parts[0]
        return 'root'
    
    def _classify_module_type(self, file_path: str) -> str:
        """Classify module type"""
        module = self._get_module_name(file_path).lower()
        
        if 'test' in module:
            return 'testing'
        elif module in ['api', 'routes', 'endpoints']:
            return 'api'
        elif module in ['models', 'schema', 'database']:
            return 'data'
        elif module in ['services', 'business']:
            return 'business_logic'
        elif module in ['utils', 'helpers', 'common']:
            return 'utilities'
        elif module in ['config', 'settings']:
            return 'configuration'
        
        return 'feature'
    
    def _find_related_files(self, file_path: str) -> List[str]:
        """Find files related to this one"""
        module = self._get_module_name(file_path)
        return self.file_modules.get(module, [])
    
    def _infer_module_purpose(self, file_path: str) -> str:
        """Infer the purpose of the module"""
        module = self._get_module_name(file_path).lower()
        
        purpose_map = {
            'api': 'Handles HTTP API requests and responses',
            'models': 'Defines data models and database schemas',
            'services': 'Contains business logic and services',
            'utils': 'Provides utility functions and helpers',
            'config': 'Manages application configuration',
            'tests': 'Contains test suites',
            'auth': 'Handles authentication and authorization',
            'middleware': 'Defines middleware components',
            'routes': 'Defines application routes'
        }
        
        return purpose_map.get(module, f'Module: {module}')
    
    def _determine_architecture_layer(self, file_path: str) -> str:
        """Determine which architecture layer this belongs to"""
        path_lower = file_path.lower()
        
        # Presentation layer
        if any(word in path_lower for word in ['view', 'template', 'ui', 'frontend']):
            return 'Presentation'
        
        # API/Controller layer
        if any(word in path_lower for word in ['api', 'controller', 'route', 'endpoint']):
            return 'API/Controller'
        
        # Business logic layer
        if any(word in path_lower for word in ['service', 'business', 'logic', 'handler']):
            return 'Business Logic'
        
        # Data access layer
        if any(word in path_lower for word in ['model', 'repository', 'database', 'dao']):
            return 'Data Access'
        
        # Infrastructure layer
        if any(word in path_lower for word in ['config', 'infrastructure', 'deployment']):
            return 'Infrastructure'
        
        return 'General'
    
    def _get_file_dependencies(self, file_path: str) -> List[str]:
        """Get dependencies for a file (simplified)"""
        # This would ideally parse imports from the actual file
        # For now, return empty or implement basic logic
        return []

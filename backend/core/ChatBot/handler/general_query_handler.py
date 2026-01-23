"""
General query handling module for the RAG Chatbot.
Handles all general queries and the main retrieval/response flow.
"""

import re
from typing import Dict, Any, Optional, Iterator, List
from ..query_type import QueryType


class GeneralQueryHandler:
    """Handler for all general query operations and the main retrieval flow."""
    
    def __init__(self, chatbot):
        """
        Initialize General Query handler with reference to chatbot instance.
        
        Args:
            chatbot: The RAGChatbot instance to access shared methods and attributes
        """
        self.chatbot = chatbot
    
    def handle_general_query(
        self,
        query: str,
        expanded_query: str,
        query_type: str,
        entity: Optional[Dict[str, Any]],
        keywords: List[str],
        active_session_id: str,
        role: Optional[str] = None,
        schema_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle general query processing - the main retrieval and response flow.
        
        Args:
            query: Original user query
            expanded_query: Expanded/rewritten query
            query_type: Detected query type
            entity: Optional entity extracted from query
            keywords: Extracted keywords from query
            active_session_id: Current session ID
            role: Optional role parameter
            
        Returns:
            Response dict with answer and metadata
        """
        # Handle metrics queries
        metrics_context = None
        if query_type in [QueryType.REPOSITORY_METRICS, QueryType.TECH_STACK, QueryType.CODE_STRUCTURE]:
            if self.chatbot.repo_metrics:
                metrics_context = self.chatbot.build_metrics_context()
                self.chatbot.logger.info("METRICS | Using repository metrics context")
                if self.chatbot.verbose:
                    print("Including metrics context")
            
            # For CODE_STRUCTURE queries, ALWAYS retrieve from VectorDB as well
            # This ensures we get structure info even if metrics don't have it
            if query_type == QueryType.CODE_STRUCTURE:
                self.chatbot.logger.info("CODE_STRUCTURE | Retrieving from VectorDB (supplementing with metrics if available)")
                github_results, gmail_results, context, email_context = self._retrieve_and_build_context(
                    expanded_query, query_type, entity, keywords
                )
                # Check for ambiguity (CODE_STRUCTURE shouldn't have this, but just in case)
                if len(github_results) == 1 and github_results[0].get("__ambiguous__"):
                    return self._handle_ambiguity_response(query, query_type, active_session_id, schema_name, github_results[0])
            elif query_type in [QueryType.REPOSITORY_METRICS, QueryType.TECH_STACK]:
                # For other metrics queries, skip VectorDB retrieval and use only metrics_context
                if not self.chatbot.repo_metrics:
                    return self._handle_metrics_error(query, query_type, active_session_id)
                context = ""
                email_context = ""
                github_results = []
                gmail_results = []
            else:
                # Fallback for other query types
                github_results, gmail_results, context, email_context = self._retrieve_and_build_context(
                    expanded_query, query_type, entity, keywords
                )
                # Check for ambiguity
                if query_type == QueryType.CODE_LOCATION:
                    if len(github_results) == 1 and github_results[0].get("__ambiguous__"):
                        return self._handle_ambiguity_response(query, query_type, active_session_id, schema_name, github_results[0])
                    elif github_results and any(r.get("_ambiguous_filename") for r in github_results):
                        ambiguous_chunks = [r for r in github_results if r.get("_ambiguous_filename")]
                        if ambiguous_chunks:
                            return self._handle_ambiguity_response(query, query_type, active_session_id, schema_name, ambiguous_chunks[0])
        else:
            # Regular retrieval flow
            github_results, gmail_results, context, email_context = self._retrieve_and_build_context(
                expanded_query, query_type, entity, keywords
            )

        # 🚨 CRITICAL: Check for ambiguity BEFORE any context building or LLM calls
        if query_type == QueryType.CODE_LOCATION:
            # Check for special __ambiguous__ format (fast path)
            if len(github_results) == 1 and github_results[0].get("__ambiguous__"):
                self.chatbot.logger.warning(
                    f"AMBIGUITY_DETECTED | Found __ambiguous__ format in handle_general_query, returning early"
                )
                return self._handle_ambiguity_response(query, query_type, active_session_id, schema_name, github_results[0])
            # Check for _ambiguous_filename flag in chunks
            elif github_results and any(r.get("_ambiguous_filename") for r in github_results):
                ambiguous_chunks = [r for r in github_results if r.get("_ambiguous_filename")]
                if ambiguous_chunks:
                    self.chatbot.logger.warning(
                        f"AMBIGUITY_DETECTED | Found {len(ambiguous_chunks)} chunks with _ambiguous_filename flag, returning early"
                    )
                    return self._handle_ambiguity_response(query, query_type, active_session_id, schema_name, ambiguous_chunks[0])

        # Log context length for debugging
        if context:
            self.chatbot.logger.info(f"CONTEXT | Built context: {len(context)} characters from {len(github_results)} chunks")
        else:
            self.chatbot.logger.warning(f"CONTEXT | Empty context - no information available to answer query")

        # Generate response
        system_prompt = self.chatbot.get_dynamic_system_prompt(query_type, expanded_query, role=role)
        user_prompt = self.chatbot.build_user_prompt(
            expanded_query, context, email_context, query_type, entity, metrics_context
        )

        if self.chatbot.verbose:
            print("Generating response...")

        self.chatbot.logger.info("LLM GENERATION | Started")
        answer = self.chatbot.call_llm(system_prompt, user_prompt)
        self.chatbot.logger.info(f"LLM GENERATION | Completed, Length: {len(answer)} chars")

        self.chatbot.logger.info("VERIFICATION | Starting response verification")
        refined_answer = self.chatbot.verify_and_refine_response(answer, query, query_type)

        # Build sources and emails
        sources = self._build_sources(github_results)
        emails = self._build_emails(gmail_results)

        self.chatbot.history.append({'role': 'user', 'content': query})
        self.chatbot.history.append({'role': 'assistant', 'content': refined_answer})

        # Calculate context quality
        if metrics_context:
            context_quality = 1.0
        elif github_results and len(github_results) > 0:
            top_score = max((r.get('score', 0) for r in github_results), default=0.0)
            context_quality = min(top_score, 1.0)
        else:
            context_quality = 0.0

        self.chatbot.logger.info(
            f"RESPONSE COMPLETE | Quality: {context_quality:.2f}, Sources: {len(sources)}, Emails: {len(emails)}")
        self.chatbot.logger.info("=" * 80)

        # Save conversation
        try:
            self.chatbot.conversation_store.add_message(active_session_id, "user", query, schema_name=schema_name, tokens_used=0)
            self.chatbot.conversation_store.add_message(active_session_id, "assistant", refined_answer, schema_name=schema_name, tokens_used=0)
            self.chatbot.logger.info(f"CONVERSATION_STORE | Saved main response to session {active_session_id[:8]}...")
        except Exception as e:
            self.chatbot.logger.error(f"CONVERSATION_STORE | Failed to save main response: {e}")

        result = {
            'answer': refined_answer,
            'sources': sources,
            'chunks_retrieved': len(github_results) if github_results else 0,
            'query_type': query_type,
            'context_quality': context_quality,
            'emails': emails,
            'has_diagram': bool(re.search(r'```mermaid', str(refined_answer or ''))),
            'related_knowledge': None,
            'is_metrics_query': query_type in [
                QueryType.REPOSITORY_METRICS,
                QueryType.TECH_STACK,
                QueryType.CODE_STRUCTURE
            ]
        }

        self._update_caches(query, result, active_session_id)

        return result
    
    def handle_general_query_stream(
        self,
        query: str,
        expanded_query: str,
        query_type: str,
        entity: Optional[Dict[str, Any]],
        keywords: List[str],
        role: Optional[str] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Handle general query processing in streaming mode.
        
        Args:
            query: Original user query
            expanded_query: Expanded/rewritten query
            query_type: Detected query type
            entity: Optional entity extracted from query
            keywords: Extracted keywords from query
            role: Optional role parameter
            
        Yields:
            Streaming response chunks and final complete response
        """
        yield {'type': 'status', 'content': 'Searching codebase...'}

        # Handle metrics queries
        metrics_context = None
        if query_type in [QueryType.REPOSITORY_METRICS, QueryType.TECH_STACK, QueryType.CODE_STRUCTURE]:
            if self.chatbot.repo_metrics:
                metrics_context = self.chatbot.build_metrics_context()
                yield {'type': 'status', 'content': 'Loading repository metrics...'}
            
            # For CODE_STRUCTURE queries, ALWAYS retrieve from VectorDB as well
            # This ensures we get structure info even if metrics don't have it
            if query_type == QueryType.CODE_STRUCTURE:
                self.chatbot.logger.info("CODE_STRUCTURE | Retrieving from VectorDB (supplementing with metrics if available)")
                yield {'type': 'status', 'content': 'Searching repository structure...'}
                github_results, gmail_results, context, email_context = self._retrieve_and_build_context_stream(
                    expanded_query, query_type, entity, keywords
                )
            elif query_type in [QueryType.REPOSITORY_METRICS, QueryType.TECH_STACK]:
                # For other metrics queries, skip VectorDB retrieval and use only metrics_context
                if not self.chatbot.repo_metrics:
                    yield {
                        'type': 'complete',
                        'content': {
                            'answer': (f"Repository metrics are not available for {getattr(self.chatbot, 'repo_owner', 'unknown')}/{getattr(self.chatbot, 'repo_name', 'unknown')}.\n\n"
                                       f"To enable metrics-based queries, ensure techstack.json exists at:\n"
                                       f"  data/DataProcessing/{getattr(self.chatbot, 'repo_owner', 'unknown')}/{getattr(self.chatbot, 'repo_name', 'unknown')}/techstack.json\n\n"
                                       f"This file is automatically generated when you run data processing."),
                            'sources': [],
                            'chunks_retrieved': 0,
                            'query_type': query_type,
                            'context_quality': 0.0,
                            'has_diagram': False,
                            'emails': [],
                            'is_metrics_query': True
                        }
                    }
                    return
                context = ""
                email_context = ""
                github_results = []
                gmail_results = []
            else:
                # Fallback for other query types
                github_results, gmail_results, context, email_context = self._retrieve_and_build_context_stream(
                    expanded_query, query_type, entity, keywords
                )
        else:
            # Regular retrieval flow
            github_results, gmail_results, context, email_context = self._retrieve_and_build_context_stream(
                expanded_query, query_type, entity, keywords
            )

        if github_results:
            yield {'type': 'status', 'content': f'Found {len(github_results)} relevant code chunks'}

        if gmail_results:
            yield {'type': 'status', 'content': f'Found {len(gmail_results)} related emails'}

        system_prompt = self.chatbot.get_dynamic_system_prompt(query_type, expanded_query, role=role)
        user_prompt = self.chatbot.build_user_prompt(
            expanded_query, context, email_context, query_type, entity, metrics_context
        )

        yield {'type': 'status', 'content': 'Generating response...'}

        full_answer = ""
        buffer = ""
        for chunk in self.chatbot.call_llm_stream(system_prompt, user_prompt):
            full_answer += chunk
            buffer += chunk

            if '\n' in buffer or len(buffer) > 150:
                yield {'type': 'chunk', 'content': buffer}
                buffer = ""

        if buffer:
            yield {'type': 'chunk', 'content': buffer}

        self.chatbot.logger.info(f"LLM GENERATION | Completed streaming, Length: {len(full_answer)} chars")

        yield {'type': 'status', 'content': 'Verifying response...'}
        refined_answer = self.chatbot.verify_and_refine_response(full_answer, query, query_type)

        if refined_answer != full_answer:
            yield {'type': 'status', 'content': 'Response refined'}

        sources = self._build_sources(github_results)
        emails = self._build_emails(gmail_results)

        self.chatbot.history.append({'role': 'user', 'content': query})
        self.chatbot.history.append({'role': 'assistant', 'content': refined_answer})

        if metrics_context:
            context_quality = 1.0
        elif github_results and len(github_results) > 0:
            top_score = max((r.get('score', 0) for r in github_results), default=0.0)
            context_quality = min(top_score, 1.0)
        else:
            context_quality = 0.0

        self.chatbot.logger.info(f"RESPONSE COMPLETE | Quality: {context_quality:.2f}")
        self.chatbot.logger.info("=" * 80)

        yield {
            'type': 'complete',
            'content': {
                'answer': refined_answer,
                'sources': sources,
                'chunks_retrieved': len(github_results) if github_results else 0,
                'query_type': query_type,
                'context_quality': context_quality,
                'emails': emails,
                'has_diagram': bool(re.search(r'```mermaid', str(refined_answer or ''))),
                'related_knowledge': None,
                'is_metrics_query': query_type in [
                    QueryType.REPOSITORY_METRICS,
                    QueryType.TECH_STACK,
                    QueryType.CODE_STRUCTURE
                ]
            }
        }
    
    def _retrieve_and_build_context(
        self,
        expanded_query: str,
        query_type: str,
        entity: Optional[Dict[str, Any]],
        keywords: List[str]
    ) -> tuple:
        """Retrieve results and build context."""
        # Retrieval (multi-query optional)
        if self.chatbot.enable_multi_query and query_type not in [QueryType.REPOSITORY_METRICS, QueryType.TECH_STACK,
                                                                  QueryType.CODE_STRUCTURE]:
            self.chatbot.logger.info("MULTI-QUERY | Generating optimized query variations")
            queries = self.chatbot.generate_multi_queries(expanded_query, query_type)

            github_results = self.chatbot.retrieve_with_multi_query(
                queries, query_type, entity, keywords
            )
        else:
            query_embedding = self.chatbot.get_query_embedding(expanded_query)
            github_results = self.chatbot.retrieve_github_first(
                query_embedding, query_type, entity, keywords, query_text=expanded_query
            )

        self.chatbot.logger.info(f"RETRIEVAL | Retrieved {len(github_results)} chunks from GitHub")
        
        # 🚨 CRITICAL: Check for ambiguity BEFORE any further processing
        is_ambiguous = False
        if query_type == QueryType.CODE_LOCATION:
            # Check for special __ambiguous__ format (fast path)
            if len(github_results) == 1 and github_results[0].get("__ambiguous__"):
                self.chatbot.logger.warning(
                    f"AMBIGUITY_DETECTED | Found __ambiguous__ format, skipping Gmail retrieval and context building"
                )
                is_ambiguous = True
            # Check for _ambiguous_filename flag in chunks
            elif any(r.get("_ambiguous_filename") for r in github_results):
                ambiguous_chunks = [r for r in github_results if r.get("_ambiguous_filename")]
                first = ambiguous_chunks[0]
                all_paths = first.get("_all_matching_paths", [])
                if all_paths:
                    self.chatbot.logger.warning(
                        f"AMBIGUITY_DETECTED | Found {len(ambiguous_chunks)} chunks with _ambiguous_filename flag, "
                        f"{len(all_paths)} paths, skipping Gmail retrieval and context building"
                    )
                    is_ambiguous = True
        
        # Log chunks (only if not ambiguous)
        if not is_ambiguous:
            from utils.metadata_normalizer import MetadataNormalizer
            for i, result in enumerate(github_results[:5], 1):
                # Use metadata normalizer for unified access
                meta_norm = MetadataNormalizer(result.get('metadata', {}), result)
                file_path = meta_norm.get_file_path('N/A')
                chunk_type = meta_norm.get_chunk_type('N/A')
                self.chatbot.logger.info(
                    f"CHUNK {i} | File: {file_path}, Score: {result.get('score', 0):.4f}, Type: {chunk_type}")

            if self.chatbot.verbose:
                print(f"GitHub: {len(github_results)} chunks")

            # Gmail correlated retrieval (only if not ambiguous)
            query_embedding = self.chatbot.get_query_embedding(expanded_query)
            gmail_results = self.chatbot.retrieve_gmail_correlated(
                github_results, query_embedding, keywords
            )
        else:
            # Skip Gmail retrieval for ambiguous queries
            gmail_results = []

        if not is_ambiguous:
            if gmail_results:
                self.chatbot.logger.info(f"EMAIL RETRIEVAL | Found {len(gmail_results)} correlated emails")

            if self.chatbot.verbose:
                print(f"Gmail: {len(gmail_results)} emails")

            # Log context quality warnings
            if not github_results:
                self.chatbot.logger.warning(f"RETRIEVAL | No results retrieved for query type: {query_type}")
                self.chatbot.logger.warning(f"RETRIEVAL | Consider checking if the routed index has content")
            elif len(github_results) < 3:
                self.chatbot.logger.warning(f"RETRIEVAL | Only {len(github_results)} results retrieved, may be insufficient")

            context = self.chatbot.build_context_from_chunks(github_results, query_type) if github_results else ""
            email_context = self.chatbot.build_email_context(gmail_results) if gmail_results else ""
        else:
            # Skip context building for ambiguous queries - response handler will handle it
            context = ""
            email_context = ""
        
        return github_results, gmail_results, context, email_context
    
    def _retrieve_and_build_context_stream(
        self,
        expanded_query: str,
        query_type: str,
        entity: Optional[Dict[str, Any]],
        keywords: List[str]
    ) -> tuple:
        """Retrieve results and build context for streaming."""
        if self.chatbot.enable_multi_query and query_type not in [QueryType.REPOSITORY_METRICS, QueryType.TECH_STACK,
                                                                  QueryType.CODE_STRUCTURE]:
            queries = self.chatbot.generate_multi_queries(expanded_query, query_type)
            github_results = self.chatbot.retrieve_with_multi_query(
                queries, query_type, entity, keywords
            )
        else:
            query_embedding = self.chatbot.get_query_embedding(expanded_query)
            github_results = self.chatbot.retrieve_github_first(
                query_embedding, query_type, entity, keywords, query_text=expanded_query
            )

        query_embedding = self.chatbot.get_query_embedding(expanded_query)
        gmail_results = self.chatbot.retrieve_gmail_correlated(
            github_results, query_embedding, keywords
        )

        context = self.chatbot.build_context_from_chunks(github_results, query_type) if github_results else ""
        email_context = self.chatbot.build_email_context(gmail_results) if gmail_results else ""
        
        return github_results, gmail_results, context, email_context
    
    def _handle_ambiguity_response(
        self,
        query: str,
        query_type: str,
        active_session_id: str,
        schema_name: Optional[str] = None,
        ambiguous_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle ambiguity response when multiple files with same name are found.
        
        Args:
            query: Original user query
            query_type: Query type (should be CODE_LOCATION)
            active_session_id: Current session ID
            schema_name: Optional schema name
            
        Returns:
            Response dict with ambiguity message
        """
        # Extract ambiguity info from provided result or retrieve it
        if ambiguous_result:
            if ambiguous_result.get("__ambiguous__"):
                filename = ambiguous_result.get("filename", "unknown")
                paths = ambiguous_result.get("paths", [])
            elif ambiguous_result.get("_ambiguous_filename"):
                from utils.path_normalizer import extract_filename
                filename = extract_filename(ambiguous_result.get("metadata", {}).get("file_path", ""))
                paths = ambiguous_result.get("_all_matching_paths", [])
            else:
                filename = "unknown"
                paths = []
        else:
            # Fallback: retrieve again (shouldn't happen but just in case)
            query_embedding = self.chatbot.get_query_embedding(query)
            github_results = self.chatbot.retrieve_github_first(
                query_embedding, query_type, None, [], query_text=query
            )
            
            # Extract ambiguity info
            if len(github_results) == 1 and github_results[0].get("__ambiguous__"):
                ambiguity_info = github_results[0]
                filename = ambiguity_info.get("filename", "unknown")
                paths = ambiguity_info.get("paths", [])
            else:
            # Fallback: try to detect from chunks
            ambiguous_chunks = [r for r in github_results if r.get("_ambiguous_filename")]
            if ambiguous_chunks:
                first = ambiguous_chunks[0]
                from utils.path_normalizer import extract_filename
                filename = extract_filename(first.get("metadata", {}).get("file_path", ""))
                paths = first.get("_all_matching_paths", [])
            else:
                # Last resort: detect from file paths
                from utils.metadata_normalizer import MetadataNormalizer
                from utils.path_normalizer import normalize_path, extract_filename
                filename_to_paths = {}
                for result in github_results:
                    meta_norm = MetadataNormalizer(result.get('metadata', {}), result)
                    file_path = meta_norm.get_file_path('')
                    if file_path:
                        normalized_path = normalize_path(file_path, '')
                        if normalized_path:
                            fn = extract_filename(normalized_path)
                            if fn:
                                fn_lower = fn.lower()
                                if fn_lower not in filename_to_paths:
                                    filename_to_paths[fn_lower] = set()
                                filename_to_paths[fn_lower].add(normalized_path)
                
                # Get first ambiguous filename
                for fn_lower, path_set in filename_to_paths.items():
                    if len(path_set) > 1:
                        filename = fn_lower
                        paths = sorted(path_set)
                        break
                else:
                    filename = "unknown"
                    paths = []
        
        answer = (
            f"Multiple files named `{filename}` were found:\n\n"
            + "\n".join(f"- {p}" for p in paths)
            + "\n\nPlease specify which file you're referring to by providing the full path."
        )
        
        self.chatbot.logger.warning(
            f"AMBIGUITY_RESPONSE | Returning ambiguity message for '{filename}' with {len(paths)} paths"
        )
        
        # Save conversation
        try:
            self.chatbot.conversation_store.add_message(active_session_id, "user", query, schema_name=schema_name, tokens_used=0)
            self.chatbot.conversation_store.add_message(active_session_id, "assistant", answer, schema_name=schema_name, tokens_used=0)
            self.chatbot.logger.info(f"CONVERSATION_STORE | Saved ambiguity response to session {active_session_id[:8]}...")
        except Exception as e:
            self.chatbot.logger.error(f"CONVERSATION_STORE | Failed to save ambiguity response: {e}")
        
        return {
            'answer': answer,
            'sources': [],
            'chunks_retrieved': 0,
            'query_type': query_type,
            'context_quality': 0.0,
            'emails': [],
            'has_diagram': False,
            'related_knowledge': None,
            'is_metrics_query': False,
            'is_ambiguous': True
        }
    
    def _handle_metrics_error(
        self,
        query: str,
        query_type: str,
        active_session_id: str,
        schema_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle metrics query when metrics are not available."""
        repo_owner = getattr(self.chatbot, 'repo_owner', 'unknown')
        repo_name = getattr(self.chatbot, 'repo_name', 'unknown')
        repo_path = f"{repo_owner}/{repo_name}" if repo_owner != 'unknown' and repo_name != 'unknown' else "current repository"
        
        error_msg = (
            f"Repository metrics are not available for {repo_path}.\n\n"
            f"To enable metrics-based queries, ensure techstack.json exists at:\n"
            f"  data/DataProcessing/{repo_owner}/{repo_name}/techstack.json\n\n"
            f"This file is automatically generated when you run data processing."
        )
        
        try:
            self.chatbot.conversation_store.add_message(active_session_id, "user", query, schema_name=schema_name, tokens_used=0)
            self.chatbot.conversation_store.add_message(
                active_session_id, "assistant",
                error_msg,
                schema_name=schema_name,
                tokens_used=0
            )
            self.chatbot.logger.info(f"CONVERSATION_STORE | Saved metrics error to session {active_session_id[:8]}...")
        except Exception as e:
            self.chatbot.logger.error(f"CONVERSATION_STORE | Failed to save metrics error: {e}")
        
        result = {
            'answer': error_msg,
            'sources': [],
            'chunks_retrieved': 0,
            'query_type': query_type,
            'context_quality': 0.0,
            'has_diagram': False,
            'emails': [],
            'is_metrics_query': True
        }

        self._update_caches(query, result, active_session_id)

        return result
    
    def _build_sources(self, github_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build sources list from GitHub results."""
        from utils.metadata_normalizer import MetadataNormalizer
        sources = []
        if github_results:
            for i, result in enumerate(github_results[:5], 1):
                # Use metadata normalizer for unified access
                meta_norm = MetadataNormalizer(result.get('metadata', {}), result)
                sources.append({
                    'rank': i,
                    'file': meta_norm.get_file_path('unknown'),
                    'type': meta_norm.get_chunk_type('unknown'),
                    'score': result.get('score', 0.0),
                    'chunk_id': result.get('chunk_id', '') or meta_norm.get('chunk_id', '')
                })
        return sources
    
    def _build_emails(self, gmail_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build emails list from Gmail results."""
        emails = []
        for email in gmail_results:
            metadata = email.get('metadata', {})
            emails.append({
                'subject': metadata.get('subject', ''),
                'from': metadata.get('from', ''),
                'date': metadata.get('date', ''),
                'relevance': email.get('relevance_score', 0)
            })
        return emails
    
    def _update_caches(self, query: str, result: Dict[str, Any], active_session_id: str):
        """Update semantic and response caches."""
        self.chatbot.cache_handler.update_caches(query, result, active_session_id)


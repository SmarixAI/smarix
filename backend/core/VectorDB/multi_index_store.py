"""
Multi-Index Vector Store
Manages separate FAISS indices for different data types with intelligent routing
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging
import re
import tempfile

from core.VectorDB.vector_db.faiss_db import FAISSVectorDB

logger = logging.getLogger(__name__)

# Import S3 manager
try:
    from utils.s3 import s3_manager
    S3_BUCKET = "smarix-data-apsouth1"
except ImportError:
    s3_manager = None
    S3_BUCKET = None


class MultiIndexVectorStore:
    """
    Manages multiple FAISS indices for different content types.
    Dynamically detects available indices from the directory structure.
    """
    
    # Base types - can be extended dynamically
    BASE_INDEX_TYPES = [
        "code",
        "commit",
        "pr",
        "issue",
        "documentation",
        "email",
        "email_attachment",
        "repo_metrics",
        "repository_overview",
        "onboarding",
        "offboarding",
        "analyzed_file",
        "workflow",
        "tech_stack_summary",
        "graph_nodes",  # Graph nodes index (stored in 'graph' folder)
        "all"
    ]
    
    def __init__(self, base_dir: str, dimension: int = 384, index_type: str = "flat", metric: str = "cosine"):
        """
        Initialize multi-index store.
        
        Args:
            base_dir: Base directory for storing indices (can be local path or S3 path like s3://bucket/path)
            dimension: Embedding dimension
            index_type: FAISS index type ('flat', 'ivf', 'hnsw')
            metric: Distance metric ('cosine', 'l2', 'ip')
        """
        # Check if base_dir is an S3 path
        self.is_s3_path = isinstance(base_dir, str) and base_dir.startswith("s3://")
        
        if self.is_s3_path:
            # Parse S3 path: s3://bucket/path/to/vectordb
            match = re.match(r"s3://([^/]+)/(.+)", base_dir)
            if match:
                self.s3_bucket = match.group(1)
                self.s3_prefix = match.group(2).rstrip("/")
            else:
                raise ValueError(f"Invalid S3 path format: {base_dir}")
            self.base_dir = None  # Not a local path
        else:
            self.base_dir = Path(base_dir)
            self.s3_bucket = None
            self.s3_prefix = None
            # Create base directory structure for local paths
            self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        
        # Dynamically discover available index types
        self.available_index_types = self._discover_index_types()
        
        # Initialize indices dictionary with discovered types
        self.indices: Dict[str, Optional[FAISSVectorDB]] = {
            idx_type: None for idx_type in self.available_index_types
        }
        
        # Index directories (for local) or S3 prefixes (for S3)
        if self.is_s3_path:
            self.index_dirs = {
                idx_type: f"{self.s3_prefix}/{idx_type}"
                for idx_type in self.available_index_types
            }
        else:
            self.index_dirs = {
                idx_type: self.base_dir / idx_type
                for idx_type in self.available_index_types
            }
        
        logger.info(f"Initialized MultiIndexVectorStore at {base_dir} (S3: {self.is_s3_path})")
        logger.info(f"Available index types: {self.available_index_types}")
    
    def _discover_index_types(self) -> List[str]:
        """
        Dynamically discover available index types from directory structure (local or S3).
        Returns base types + any additional types found in the directory.
        Handles special mapping: 'graph' folder -> 'graph_nodes' index type.
        """
        discovered_types = set(self.BASE_INDEX_TYPES)
        
        if self.is_s3_path:
            # Discover from S3
            if s3_manager is None:
                logger.warning("S3 manager not available, using base types only")
                return sorted(list(discovered_types))
            
            try:
                # List objects in S3 prefix
                response = s3_manager.s3.list_objects_v2(
                    Bucket=self.s3_bucket,
                    Prefix=self.s3_prefix + "/",
                    Delimiter="/"
                )
                
                # Check CommonPrefixes for subdirectories (index types)
                if "CommonPrefixes" in response:
                    for prefix_info in response["CommonPrefixes"]:
                        prefix = prefix_info["Prefix"]
                        # Extract index type from prefix: VectorDB/owner/repo/type/
                        parts = prefix.rstrip("/").split("/")
                        if len(parts) > 0:
                            index_type = parts[-1]
                            
                            # Special handling: 'graph' folder maps to 'graph_nodes' index type
                            if index_type == "graph":
                                # Check if graph_nodes index exists
                                graph_prefix = f"{prefix}graph_nodes/"
                                graph_response = s3_manager.s3.list_objects_v2(
                                    Bucket=self.s3_bucket,
                                    Prefix=graph_prefix,
                                    MaxKeys=5
                                )
                                if "Contents" in graph_response:
                                    has_index = any("faiss.index" in obj["Key"] for obj in graph_response["Contents"])
                                    if has_index:
                                        discovered_types.add("graph_nodes")
                            else:
                                # Check if this prefix has faiss.index
                                type_response = s3_manager.s3.list_objects_v2(
                                    Bucket=self.s3_bucket,
                                    Prefix=prefix,
                                    MaxKeys=5
                                )
                                if "Contents" in type_response:
                                    has_index = any("faiss.index" in obj["Key"] for obj in type_response["Contents"])
                                    if has_index:
                                        discovered_types.add(index_type)
            except Exception as e:
                logger.warning(f"Failed to discover index types from S3: {e}")
        else:
            # Discover from local filesystem
            if self.base_dir.exists():
                for item in self.base_dir.iterdir():
                    if item.is_dir():
                        # Special handling: 'graph' folder maps to 'graph_nodes' index type
                        if item.name == "graph":
                            # Check if graph_nodes index exists in the graph folder
                            graph_index_dir = item / "graph_nodes"
                            if (graph_index_dir / "faiss.index").exists() or (graph_index_dir / "config.json").exists():
                                discovered_types.add("graph_nodes")
                        else:
                            # Check if it looks like an index directory
                            if (item / "faiss.index").exists() or (item / "config.json").exists():
                                discovered_types.add(item.name)
        
        return sorted(list(discovered_types))
    
    @property
    def INDEX_TYPES(self):
        """Property for backward compatibility"""
        return self.available_index_types
    
    def index_by_type(self, 
                     content_type: str,
                     chunks: List[Dict[str, Any]],
                     embeddings: np.ndarray,
                     metadata: List[Dict[str, Any]]) -> bool:
        """
        Index chunks into the appropriate index by content type.
        
        Args:
            content_type: Type of content (e.g., 'issue', 'pr', 'code')
            chunks: List of chunk dictionaries
            embeddings: Numpy array of embeddings (n_chunks, dimension)
            metadata: List of metadata dictionaries
            
        Returns:
            True if successful
        """
        # Add new content type if not already known
        if content_type not in self.available_index_types:
            logger.info(f"Adding new index type: {content_type}")
            self.available_index_types.append(content_type)
            self.indices[content_type] = None
            self.index_dirs[content_type] = self.base_dir / content_type
        
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} != {self.dimension}")
        
        # Extract chunk IDs
        chunk_ids = [chunk.get('chunk_id', f"{content_type}_{i}") for i, chunk in enumerate(chunks)]
        
        # Create or load index
        if self.indices[content_type] is None:
            self.indices[content_type] = FAISSVectorDB(
                dimension=self.dimension,
                index_type=self.index_type,
                metric=self.metric
            )
        
        # Add embeddings
        self.indices[content_type].add_embeddings(embeddings, chunk_ids, metadata)
        
        logger.info(f"Indexed {len(chunks)} chunks into '{content_type}' index")
        
        # Also add to all index (skip if content_type is already 'all')
        if content_type != 'all':
            self._add_to_all(embeddings, chunk_ids, metadata, content_type)
        
        return True
    
    def _add_to_all(self,
                    embeddings: np.ndarray,
                    chunk_ids: List[str],
                    metadata: List[Dict[str, Any]],
                    source_type: str):
        """Add embeddings to all index"""
        if 'all' not in self.indices:
            self.indices['all'] = None
            self.index_dirs['all'] = self.base_dir / 'all'
        
        if self.indices['all'] is None:
            self.indices['all'] = FAISSVectorDB(
                dimension=self.dimension,
                index_type=self.index_type,
                metric=self.metric
            )
        
        # Add source type to metadata
        enriched_metadata = []
        for meta in metadata:
            enriched = meta.copy()
            enriched['source_index'] = source_type
            enriched_metadata.append(enriched)
        
        self.indices['all'].add_embeddings(embeddings, chunk_ids, enriched_metadata)
    
    def search_by_type(self,
                      query_embedding: np.ndarray,
                      index_type: str,
                      top_k: int = 5,
                      filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search in a specific index type.
        
        Args:
            query_embedding: Query embedding vector
            index_type: Type to search (e.g., 'issue', 'pr', 'code')
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of search results with scores
        """
        if index_type not in self.available_index_types:
            logger.warning(f"Unknown index type: {index_type}. Available: {self.available_index_types}")
            return []
        
        if self.indices[index_type] is None:
            logger.warning(f"Index '{index_type}' not loaded. Returning empty results.")
            return []
        
        # Search in the specified index
        results = self.indices[index_type].search(query_embedding, top_k=top_k, filters=filters)
        
        # Add index type to results
        for result in results:
            result['index_type'] = index_type
        
        return results
    
    def search_all(self,
                   query_embedding: np.ndarray,
                   top_k: int = 10,
                   filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search in all index (fallback for low-confidence results).
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of search results with scores
        """
        if 'all' not in self.indices or self.indices['all'] is None:
            logger.warning("'all' index not loaded. Returning empty results.")
            return []
        
        results = self.indices['all'].search(query_embedding, top_k=top_k, filters=filters)
        
        # Add index type
        for result in results:
            result['index_type'] = result.get('metadata', {}).get('source_index', 'all')
        
        return results
    
    def search_multi(self,
                    query_embedding: np.ndarray,
                    index_types: List[str],
                    top_k_per_index: int = 3,
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search across multiple indices and merge results.
        
        Args:
            query_embedding: Query embedding vector
            index_types: List of index types to search
            top_k_per_index: Results per index
            filters: Optional metadata filters
            
        Returns:
            Merged and deduplicated results sorted by score
        """
        all_results = []
        
        for index_type in index_types:
            if index_type in self.available_index_types:
                results = self.search_by_type(query_embedding, index_type, top_k_per_index, filters)
                all_results.extend(results)
        
        # Deduplicate by chunk_id
        seen_ids = set()
        unique_results = []
        for result in all_results:
            chunk_id = result.get('chunk_id', '')
            if chunk_id and chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_results.append(result)
        
        # Sort by score (descending for cosine/IP, ascending for L2)
        reverse_sort = self.metric in ['cosine', 'ip']
        unique_results.sort(key=lambda x: x.get('score', 0.0), reverse=reverse_sort)
        
        return unique_results
    
    def save(self, base_path: Optional[str] = None):
        """
        Save all indices to disk.
        
        Args:
            base_path: Optional override for base directory
        """
        save_dir = Path(base_path) if base_path else self.base_dir
        
        saved_count = 0
        for index_type, index_db in self.indices.items():
            if index_db is not None:
                index_dir = save_dir / index_type
                index_dir.mkdir(parents=True, exist_ok=True)
                
                # Save FAISS index
                index_db.save(str(index_dir))
                
                # Save config
                config = {
                    'dimension': self.dimension,
                    'index_type': self.index_type,
                    'metric': self.metric,
                    'index_name': index_type
                }
                
                config_path = index_dir / 'config.json'
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                logger.info(f"Saved '{index_type}' index to {index_dir}")
                saved_count += 1
        
        logger.info(f"Saved {saved_count} indices to {save_dir}")
    
    def load(self, base_path: Optional[str] = None):
        """
        Load all indices from disk or S3.
        
        Args:
            base_path: Optional override for base directory (can be local path or S3 path)
        """
        # Determine if we're loading from S3
        is_s3 = False
        if base_path:
            is_s3 = isinstance(base_path, str) and base_path.startswith("s3://")
            if is_s3:
                match = re.match(r"s3://([^/]+)/(.+)", base_path)
                if match:
                    s3_bucket = match.group(1)
                    s3_prefix = match.group(2).rstrip("/")
                else:
                    raise ValueError(f"Invalid S3 path format: {base_path}")
            else:
                load_dir = Path(base_path)
        else:
            is_s3 = self.is_s3_path
            if is_s3:
                s3_bucket = self.s3_bucket
                s3_prefix = self.s3_prefix
            else:
                load_dir = self.base_dir
        
        # Rediscover index types in case new ones were added
        if base_path:
            if is_s3:
                self.is_s3_path = True
                self.s3_bucket = s3_bucket
                self.s3_prefix = s3_prefix
                self.base_dir = None
            else:
                self.is_s3_path = False
                self.base_dir = load_dir
                self.s3_bucket = None
                self.s3_prefix = None
        self.available_index_types = self._discover_index_types()
        
        loaded_count = 0
        for index_type in self.available_index_types:
            # Special handling: 'graph_nodes' index is stored in 'graph/graph_nodes' folder
            if index_type == "graph_nodes":
                if is_s3:
                    index_s3_prefix = f"{s3_prefix}/graph/graph_nodes"
                else:
                    index_dir = load_dir / "graph" / "graph_nodes"
            else:
                if is_s3:
                    index_s3_prefix = f"{s3_prefix}/{index_type}"
                else:
                    index_dir = load_dir / index_type
            
            if is_s3:
                # Check if index files exist in S3
                if s3_manager is None:
                    logger.error("S3 manager not available, cannot load from S3")
                    continue
                index_s3_key = f"{index_s3_prefix}/faiss.index"
                if not s3_manager.key_exists(index_s3_key):
                    logger.debug(f"Index file not found in S3: {index_s3_key}")
                    continue
            else:
                if not index_dir.exists():
                    logger.debug(f"Index directory not found: {index_dir}")
                    continue
                
                # Check if index files exist
                index_file = index_dir / 'faiss.index'
                if not index_file.exists():
                    logger.warning(f"Index file not found: {index_file}")
                    continue
            
            try:
                # Load FAISS index (from S3 or local)
                if is_s3:
                    loaded_db = FAISSVectorDB.load_from_s3(s3_bucket, index_s3_prefix)
                else:
                    loaded_db = FAISSVectorDB.load(str(index_dir))
                
                logger.debug(f"Loaded index '{index_type}' with {len(loaded_db.metadata)} metadata entries")
                
                if len(loaded_db.metadata) > 0:
                    logger.debug(f"Sample metadata from '{index_type}': {loaded_db.metadata[0]}")
                
                self.indices[index_type] = loaded_db
                
                # Update dimension from loaded index
                if loaded_count == 0:  # Use first loaded index to set dimension
                    if is_s3:
                        if s3_manager is not None:
                            config_s3_key = f"{index_s3_prefix}/config.json"
                            if s3_manager.key_exists(config_s3_key):
                                config = s3_manager.download_json(config_s3_key)
                            detected_dim = config.get('dimension') or config.get('vector_dimension')
                            if detected_dim:
                                self.dimension = detected_dim
                                self.index_type = config.get('index_type', self.index_type)
                                self.metric = config.get('metric', self.metric)
                                logger.info(f"Detected dimension: {self.dimension} from '{index_type}' index")
                    else:
                        config_path = index_dir / 'config.json'
                        if config_path.exists():
                            with open(config_path, 'r') as f:
                                config = json.load(f)
                                detected_dim = config.get('dimension') or config.get('vector_dimension')
                                if detected_dim:
                                    self.dimension = detected_dim
                                    self.index_type = config.get('index_type', self.index_type)
                                    self.metric = config.get('metric', self.metric)
                                    logger.info(f"Detected dimension: {self.dimension} from '{index_type}' index")
                
                location_str = f"s3://{s3_bucket}/{index_s3_prefix}" if is_s3 else str(index_dir)
                logger.info(f"Loaded '{index_type}' index from {location_str} ({loaded_db.index.ntotal} vectors, dim: {loaded_db.dimension})")
                loaded_count += 1
                
            except Exception as e:
                logger.error(f"Failed to load '{index_type}' index: {e}")
                import traceback
                logger.debug(f"Traceback for '{index_type}': {traceback.format_exc()}")
                self.indices[index_type] = None
        
        location_str = f"s3://{s3_bucket}/{s3_prefix}" if is_s3 else str(load_dir)
        logger.info(f"Loaded {loaded_count}/{len(self.available_index_types)} indices from {location_str}")
        
        # Log which indices failed to load for debugging
        failed_indices = [
            idx_type for idx_type in self.available_index_types
            if self.indices.get(idx_type) is None
        ]
        if failed_indices:
            logger.warning(
                f"Failed to load {len(failed_indices)} indices: {failed_indices}. "
                f"These indices will not be available for retrieval."
            )
        else:
            logger.info(f"All {loaded_count} available indices loaded successfully")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics for all indices"""
        stats = {
            'total_indices': 0,
            'total_vectors': 0,
            'available_types': self.available_index_types,
            'by_index': {}
        }
        
        for index_type, index_db in self.indices.items():
            if index_db is not None:
                try:
                    index_stats = index_db.get_statistics()
                    stats['by_index'][index_type] = index_stats
                    stats['total_vectors'] += index_stats.get('total_vectors', 0)
                    stats['total_indices'] += 1
                except Exception as e:
                    logger.warning(f"Failed to get stats for '{index_type}': {e}")
                    stats['by_index'][index_type] = {'error': str(e)}
        
        return stats
    
    def optimize(self):
        """Optimize all indices"""
        optimized_count = 0
        for index_type, index_db in self.indices.items():
            if index_db is not None:
                try:
                    index_db.optimize()
                    logger.info(f"Optimized '{index_type}' index")
                    optimized_count += 1
                except Exception as e:
                    logger.warning(f"Failed to optimize '{index_type}': {e}")
        
        logger.info(f"Optimized {optimized_count} indices")


    def find(self, where: Dict[str, Any], top_k: int = 5, index: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Direct metadata lookup.
        If index is provided → search ONLY that index (faster, deterministic lookup)
        If index is None → search across all indices.
        """
        results = []

        index_targets = (
            {index: self.indices.get(index)} if index else self.indices
        )

        for index_type, index_db in index_targets.items():
            if index_db is None:
                continue

            for chunk_id, meta in zip(index_db.chunk_ids, index_db.metadata):
                match = True
                for key, value in where.items():
                    meta_value = meta.get(key)

                    if isinstance(meta_value, list):
                        if value not in meta_value:
                            match = False
                            break
                    elif str(meta_value) != str(value):   # 🔥 normalize numeric/string mismatches
                        match = False
                        break

                if match:
                    results.append({
                        "chunk_id": chunk_id,
                        "metadata": meta,
                        "content": meta.get("content") or "",
                        "score": 1.0,
                        "index_type": index_type
                    })

                if len(results) >= top_k:
                    return results

        return results
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a chunk (metadata + content) by chunk_id across all loaded indices.
        Used by hybrid lexical retrieval.
        """
        for index_type, index_db in self.indices.items():
            if index_db is None:
                continue

            try:
                for cid, meta in zip(index_db.chunk_ids, index_db.metadata):
                    if cid == chunk_id:
                        return {
                            "chunk_id": cid,
                            "metadata": meta,
                            "content": meta.get("content") or "",
                            "score": 0.0,
                            "index_type": index_type
                        }
            except Exception:
                continue

        return None

    

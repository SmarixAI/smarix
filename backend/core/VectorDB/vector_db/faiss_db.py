"""
FAISS Vector Database with Enhanced Metadata Filtering
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Callable
import numpy as np


class FAISSVectorDB:
    """
    Enhanced FAISS-based vector database
    - Fast similarity search
    - Rich metadata filtering
    - Hierarchical context support
    - Persistent storage
    """
    
    def __init__(self, 
                 dimension: int,
                 index_type: str = "flat",
                 metric: str = "cosine"):
        """
        Args:
            dimension: Embedding dimension
            index_type: 'flat' (exact), 'ivf' (fast), 'hnsw' (balanced)
            metric: 'cosine', 'l2', 'ip' (inner product)
        """
        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        
        self.index = None
        self.metadata = []
        self.chunk_ids = []
        
        self._initialize_faiss()
        self._create_index()
    
    def _initialize_faiss(self):
        """Initialize FAISS library"""
        try:
            import faiss
            self.faiss = faiss
            print(f"✅ FAISS initialized (version: {faiss.__version__})")
        except ImportError:
            raise ImportError(
                "FAISS not installed. Install with:\n"
                "  CPU: pip install faiss-cpu\n"
                "  GPU: pip install faiss-gpu"
            )
    
    def _create_index(self):
        """Create FAISS index based on type"""
        
        if self.index_type == "flat":
            if self.metric == "cosine":
                self.index = self.faiss.IndexFlatIP(self.dimension)
            elif self.metric == "l2":
                self.index = self.faiss.IndexFlatL2(self.dimension)
            else:
                self.index = self.faiss.IndexFlatIP(self.dimension)
        
        elif self.index_type == "ivf":
            nlist = 100
            quantizer = self.faiss.IndexFlatIP(self.dimension)
            self.index = self.faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
        
        elif self.index_type == "hnsw":
            M = 32
            self.index = self.faiss.IndexHNSWFlat(self.dimension, M)
        
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")
        
        print(f"✅ Created {self.index_type} index (metric: {self.metric})")
    
    def add_embeddings(self, 
                       embeddings: np.ndarray,
                       chunk_ids: List[str],
                       metadata: List[Dict[str, Any]]):
        """Add embeddings with rich metadata to the index"""
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} != index dimension {self.dimension}")
        
        # Normalize for cosine similarity
        if self.metric == "cosine":
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / (norms + 1e-8)  # Avoid division by zero
        
        embeddings = embeddings.astype('float32')
        
        # Train index if needed
        if self.index_type == "ivf" and not self.index.is_trained:
            print(f"🔄 Training IVF index...")
            self.index.train(embeddings)
        
        # Add to index
        self.index.add(embeddings)
        
        # Store metadata
        self.chunk_ids.extend(chunk_ids)
        self.metadata.extend(metadata)
        
        print(f"✅ Added {len(embeddings)} embeddings to index")
        print(f"   Total vectors: {self.index.ntotal}")
    
    def search(self, 
          query_embedding: np.ndarray,
          top_k: int = 5,
          filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors with optional metadata filters
        DYNAMICALLY handles dimension mismatches between query and index
        """
        if self.index.ntotal == 0:
            return []
        
        print(f"🔍 Search debug: query_shape={query_embedding.shape}, expected_dim={self.dimension}")
        
        # STEP 1: Ensure correct shape (batch of 1)
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        elif query_embedding.shape[0] != 1:
            query_embedding = query_embedding[0:1]  # Take first if batch
        
        original_query_dim = query_embedding.shape[1]
        
        # STEP 2: DYNAMIC DIMENSION HANDLING (KEY FIX!)
        if original_query_dim != self.dimension:
            print(f"⚠️  Dimension mismatch: {original_query_dim} -> {self.dimension}")
            
            if original_query_dim < self.dimension:
                # PAD: Add zeros to match index dimension
                pad_width = self.dimension - original_query_dim
                query_embedding = np.pad(
                    query_embedding, 
                    ((0, 0), (0, pad_width)), 
                    mode='constant',
                    constant_values=0
                )
                print(f"   🔄 Padded with {pad_width} zeros")
                
            else:
                # TRUNCATE: Cut to match index dimension
                query_embedding = query_embedding[:, :self.dimension]
                print(f"   🔄 Truncated to {self.dimension} dims")
        
        # STEP 3: Normalize for cosine similarity
        if self.metric == "cosine":
            norm = np.linalg.norm(query_embedding, axis=1, keepdims=True)
            query_embedding = query_embedding / (norm + 1e-8)
        
        # STEP 4: Ensure float32 dtype
        query_embedding = query_embedding.astype('float32')
        
        print(f"✅ Final query shape: {query_embedding.shape}")
        
        # STEP 5: Configure search parameters
        search_k = top_k * 3 if filters else top_k
        
        if self.index_type == "ivf":
            self.index.nprobe = 10
        
        # STEP 6: SAFE FAISS SEARCH (dimension now matches!)
        distances, indices = self.index.search(query_embedding, search_k)
        
        # STEP 7: Process results with filtering
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1 or idx >= len(self.chunk_ids):
                continue
            
            metadata = self.metadata[idx]
            # Try multiple fields for content
            content = metadata.get('full_content') or metadata.get('content') or ''
            
            result = {
                'chunk_id': self.chunk_ids[idx],
                'score': float(dist),
                'metadata': metadata,
                'content': content
            }
            
            # Apply metadata filters if provided
            if filters:
                match = True
                for key, value in filters.items():
                    meta_value = result['metadata'].get(key)
                    
                    # Handle list values (e.g., tags)
                    if isinstance(meta_value, list):
                        if not isinstance(value, list) and value not in meta_value:
                            match = False
                            break
                    elif meta_value != value:
                        match = False
                        break
                
                if not match:
                    continue
            
            results.append(result)
            
            # Stop once we have enough results
            if len(results) >= top_k:
                break
        
        print(f"✅ Found {len(results)} results (requested: {top_k})")
        return results


    def similarity_search_with_score(self,
                                     query: str,  # Not used directly, needs embedding
                                     k: int = 5,
                                     filter: Optional[Dict] = None,
                                     **kwargs) -> List[Tuple[Any, float]]:
        """
        NEW: LangChain-style interface for compatibility
        Note: This is called by hybrid retriever with pre-computed embedding
        """
        # This method signature is for compatibility
        # The actual search uses search() or search_by_metadata()
        return []
    
    def search_by_metadata(self,
                          query_embedding: np.ndarray,
                          filters: Dict[str, Any],
                          top_k: int = 5) -> List[Dict[str, Any]]:
        """
        NEW: Enhanced search with metadata filters
        
        Args:
            query_embedding: Query vector
            filters: Dict of metadata filters
            top_k: Number of results
        
        Examples:
            filters = {'chunk_type': 'function'}
            filters = {'language': 'python', 'category': 'api_documentation'}
            filters = {'semantic_tags': ['onboarding']}  # Match any tag in list
        """
        def filter_func(result):
            meta = result['metadata']
            
            for key, value in filters.items():
                meta_value = meta.get(key)
                
                # Handle list filters (e.g., semantic_tags)
                if isinstance(meta_value, list):
                    if isinstance(value, list):
                        # Check if any filter value is in metadata list
                        if not any(v in meta_value for v in value):
                            return False
                    else:
                        # Check if single value is in metadata list
                        if value not in meta_value:
                            return False
                
                # Handle list of acceptable values
                elif isinstance(value, list):
                    if meta_value not in value:
                        return False
                
                # Exact match
                else:
                    if meta_value != value:
                        return False
            
            return True
        
        return self.search(query_embedding, top_k=top_k, filter_func=filter_func)
    
    def get_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific chunk by ID"""
        try:
            idx = self.chunk_ids.index(chunk_id)
            return {
                'chunk_id': chunk_id,
                'metadata': self.metadata[idx],
                'content': self.metadata[idx].get('content', '')
            }
        except ValueError:
            return None
    
    def get_by_ids(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """NEW: Get multiple chunks by IDs"""
        results = []
        for chunk_id in chunk_ids:
            chunk = self.get_by_id(chunk_id)
            if chunk:
                results.append(chunk)
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics with hierarchical context info"""
        stats = {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'index_type': self.index_type,
            'metric': self.metric,
            'is_trained': self.index.is_trained if hasattr(self.index, 'is_trained') else True
        }
        
        # Metadata statistics
        if self.metadata:
            chunk_types = {}
            categories = {}
            importance_scores = []
            has_hierarchical = 0
            
            for meta in self.metadata:
                # Chunk types
                chunk_type = meta.get('chunk_type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                
                # Categories
                category = meta.get('category', 'unknown')
                categories[category] = categories.get(category, 0) + 1
                
                # Importance
                importance_scores.append(meta.get('importance_score', 1.0))
                
                # NEW: Hierarchical context
                if meta.get('hierarchical_context'):
                    has_hierarchical += 1
            
            stats['chunk_types'] = chunk_types
            stats['categories'] = categories
            stats['avg_importance'] = np.mean(importance_scores) if importance_scores else 0
            stats['has_hierarchical_context'] = has_hierarchical
        
        return stats
    
    def save(self, save_dir: str):
        """Save index and metadata to disk"""
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_path = save_dir / "faiss.index"
        self.faiss.write_index(self.index, str(index_path))
        
        # Save metadata
        metadata_path = save_dir / "metadata.pkl"
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'chunk_ids': self.chunk_ids,
                'metadata': self.metadata,
                'dimension': self.dimension,
                'index_type': self.index_type,
                'metric': self.metric
            }, f)
        
        # Save config as JSON
        config_path = save_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump({
                'dimension': self.dimension,
                'index_type': self.index_type,
                'metric': self.metric,
                'total_vectors': self.index.ntotal
            }, f, indent=2)
        
        print(f"\n💾 Saved vector database:")
        print(f"   Index: {index_path}")
        print(f"   Metadata: {metadata_path}")
        print(f"   Config: {config_path}")
    
    @classmethod
    def load(cls, load_dir: str) -> 'FAISSVectorDB':
        load_dir = Path(load_dir)

        # Load raw metadata
        metadata_path = load_dir / "metadata.pkl"
        with open(metadata_path, 'rb') as f:
            data = pickle.load(f)

        # ---- FIX 0: Handle legacy format (direct list instead of dict) ----
        if isinstance(data, list):
            # Old format: metadata was saved as a list directly
            metadata_list = data
            
            # Load config to get dimension/index_type/metric
            config_path = load_dir / "config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                dimension = config.get('dimension') or config.get('vector_dimension', 384)
                index_type = config.get('index_type', 'flat')
                metric = config.get('metric', 'cosine')
            else:
                dimension = 384
                index_type = 'flat'
                metric = 'cosine'
            
            # Build FAISS DB with legacy data
            db = cls(
                dimension=dimension,
                index_type=index_type,
                metric=metric
            )
            
            # Load FAISS index
            index_path = load_dir / "faiss.index"
            db.index = db.faiss.read_index(str(index_path))
            
            # Restore metadata
            db.metadata = metadata_list
            db.chunk_ids = [m.get("chunk_id", str(i)) for i, m in enumerate(metadata_list)]
            
            print(f"⚡ Loaded vector DB @ {load_dir} ({db.index.ntotal} vectors) [legacy format]")
            return db
        
        # ---- New format: data is a dict ----
        # FIX 1: Convert new format → expected flat format
        normalized = []
        for entry in data["metadata"]:
            if isinstance(entry, dict) and "id" in entry and "metadata" in entry:
                flat = entry["metadata"].copy()
                flat["chunk_id"] = entry["id"]
                normalized.append(flat)
            else:
                normalized.append(entry)

        data["metadata"] = normalized

        # ---- FIX 2: chunk_ids must match metadata ----
        if "chunk_ids" not in data or len(data["chunk_ids"]) != len(data["metadata"]):
            data["chunk_ids"] = [m.get("chunk_id", str(i)) for i, m in enumerate(data["metadata"])]

        # Build FAISS DB
        db = cls(
            dimension=data['dimension'],
            index_type=data['index_type'],
            metric=data['metric']
        )

        # Load FAISS index
        index_path = load_dir / "faiss.index"
        db.index = db.faiss.read_index(str(index_path))

        # Restore metadata
        db.metadata = data["metadata"]
        db.chunk_ids = data["chunk_ids"]

        print(f"⚡ Loaded vector DB @ {load_dir} ({db.index.ntotal} vectors)")
        return db

    
    def optimize(self):
        """Optimize index for faster search"""
        if self.index_type == "ivf":
            if not self.index.is_trained and self.index.ntotal > 0:
                print("🔄 Optimizing IVF index...")
                print("   Note: For better performance, recreate index with more training data")
        
        elif self.index_type == "hnsw":
            pass  # Already optimized
        
        print("✅ Index optimized")
    
    def clear(self):
        """Clear all data from index"""
        self.index.reset()
        self.chunk_ids = []
        self.metadata = []
        print("✅ Index cleared")

    def find(self, where: Dict[str, Any], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Direct metadata lookup without vector similarity.
        Used for queries like 'Issue #64', 'PR #21', etc.
        """
        results = []

        for chunk_id, meta in zip(self.chunk_ids, self.metadata):
            match = True
            for key, value in where.items():
                meta_value = meta.get(key)

                # match list values
                if isinstance(meta_value, list):
                    if isinstance(value, list):
                        if not any(v in meta_value for v in value):
                            match = False
                            break
                    else:
                        if value not in meta_value:
                            match = False
                            break

                # exact match
                elif meta_value != value:
                    match = False
                    break

            if match:
                content = meta.get('full_content') or meta.get('content') or ''
                results.append({
                    "chunk_id": chunk_id,
                    "metadata": meta,
                    "content": content,
                    "score": 1.0  # manual lookup, treat as strongest match
                })

            if len(results) >= top_k:
                break

        return results


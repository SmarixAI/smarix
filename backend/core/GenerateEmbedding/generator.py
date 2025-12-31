"""
Embedding Generator
Generates vector embeddings for chunks with rich contextual text
"""

import os
import json
import time
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from tqdm import tqdm
import numpy as np
from dotenv import load_dotenv
load_dotenv()


class EmbeddingGenerator:
    """
    Supports multiple embedding providers with context-enriched text:
    - OpenAI (text-embedding-3-small, text-embedding-3-large)
    - Sentence-Transformers (local, free)
    - Cohere
    - HuggingFace
    """
    
    def __init__(self, 
                 provider: str = "sentence-transformers",
                 model: str = "all-MiniLM-L6-v2",
                 batch_size: int = 32,
                 cache_dir: str = "./embeddings_cache"):
        """
        Args:
            provider: 'openai', 'sentence-transformers', 'cohere', 'huggingface'
            model: Model name specific to provider
            batch_size: Number of texts to embed at once
            cache_dir: Directory to cache embeddings
        """
        self.provider = provider.lower()
        self.model = model
        self.batch_size = batch_size
        self.cache_dir = Path(cache_dir)
        # Ensure the full directory tree exists (parents=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.embedding_model = None
        self.dimension = 0
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model based on provider"""
        
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "sentence-transformers":
            self._init_sentence_transformers()
        elif self.provider == "cohere":
            self._init_cohere()
        elif self.provider == "huggingface":
            self._init_huggingface()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    
    def _init_openai(self):
        """Initialize OpenAI embeddings"""
        try:
            import openai
            from openai import OpenAI
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            self.embedding_model = OpenAI(api_key=api_key)
            
            dimensions_map = {
                'text-embedding-ada-002': 1536,
                'text-embedding-3-small': 1536,
                'text-embedding-3-large': 3072
            }
            self.dimension = dimensions_map.get(self.model, 1536)
            
            print(f"✅ Initialized OpenAI embeddings: {self.model} (dim: {self.dimension})")
            
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        except Exception as e:
            raise Exception(f"Failed to initialize OpenAI: {e}")
    
    def _init_sentence_transformers(self):
        """Initialize Sentence-Transformers (local, free)"""
        try:
            from sentence_transformers import SentenceTransformer
            
            print(f"📥 Loading Sentence-Transformer model: {self.model}...")
            self.embedding_model = SentenceTransformer(self.model)
            self.dimension = self.embedding_model.get_sentence_embedding_dimension()
            
            print(f"✅ Initialized Sentence-Transformers: {self.model} (dim: {self.dimension})")
            
        except ImportError:
            raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
        except Exception as e:
            raise Exception(f"Failed to initialize Sentence-Transformers: {e}")
    
    def _init_cohere(self):
        """Initialize Cohere embeddings"""
        try:
            import cohere
            
            api_key = os.getenv('COHERE_API_KEY')
            if not api_key:
                raise ValueError("COHERE_API_KEY environment variable not set")
            
            self.embedding_model = cohere.Client(api_key)
            self.dimension = 4096
            
            print(f"✅ Initialized Cohere embeddings: {self.model} (dim: {self.dimension})")
            
        except ImportError:
            raise ImportError("cohere package not installed. Run: pip install cohere")
        except Exception as e:
            raise Exception(f"Failed to initialize Cohere: {e}")
    
    def _init_huggingface(self):
        """Initialize HuggingFace embeddings"""
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            print(f"📥 Loading HuggingFace model: {self.model}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model)
            self.embedding_model = AutoModel.from_pretrained(self.model)
            
            self.dimension = self.embedding_model.config.hidden_size
            
            print(f"✅ Initialized HuggingFace: {self.model} (dim: {self.dimension})")
            
        except ImportError:
            raise ImportError("transformers not installed. Run: pip install transformers torch")
        except Exception as e:
            raise Exception(f"Failed to initialize HuggingFace: {e}")
    
    def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate embeddings for all chunks with RICH CONTEXTUAL TEXT
        
        Args:
            chunks: List of chunk dictionaries with 'content' and metadata
        
        Returns:
            Dictionary with embeddings, metadata, and statistics
        """
        print(f"\n🔮 Generating embeddings for {len(chunks)} chunks...")
        print(f"   Provider: {self.provider}")
        print(f"   Model: {self.model}")
        print(f"   Dimension: {self.dimension}")
        print(f"   Batch size: {self.batch_size}\n")
        
        # NEW: Prepare ENRICHED texts for embedding
        texts = []
        chunk_ids = []
        metadata_list = []
        metadata_hashes = []
        empty_count = 0
        
        print(f"📝 Creating rich contextual text for embeddings...")
        
        for i, chunk in enumerate(chunks):
            # CRITICAL: Create rich text that includes code + context
            enriched_text = self._create_enriched_text(chunk)
            
            if not enriched_text or len(enriched_text.strip()) < 10:
                empty_count += 1
                if empty_count <= 3:  # Show first 3
                    print(f"   ⚠️  Chunk {i}: Empty or too short content")
                continue
            
            chunk_ids.append(chunk.get('chunk_id', f"chunk_{len(texts)}"))
            texts.append(enriched_text)
            
            # Store important metadata
            metadata_list.append({
                'chunk_id': chunk.get('chunk_id'),
                'chunk_type': chunk.get('chunk_type'),
                'category': chunk.get('category'),
                'importance_score': chunk.get('importance_score', 1.0),
                'file_path': chunk.get('file_path'),
                'function_name': chunk.get('function_name', ''),
                'class_name': chunk.get('class_name', ''),
                'semantic_tags': chunk.get('semantic_tags', []),
                'keywords': chunk.get('keywords', [])[:10],
                'language': chunk.get('language', ''),
                'content': chunk.get('content', '')  # Store original content
            })
            # compute a small metadata hash to detect metadata-only changes
            meta_for_hash = {
                'file_path': chunk.get('file_path'),
                'language': chunk.get('language'),
                'filename': chunk.get('filename'),
                'directory': chunk.get('directory')
            }
            try:
                mh = hashlib.md5(json.dumps(meta_for_hash, sort_keys=True).encode('utf-8')).hexdigest()
            except Exception:
                mh = ''
            metadata_hashes.append(mh)
        
        if empty_count > 0:
            print(f"   ⚠️  Skipped {empty_count} chunks with empty/short content\n")
        
        print(f"✅ Prepared {len(texts)} enriched texts for embedding")
        
        # Show sample
        if len(texts) > 0:
            sample_length = len(texts[0])
            print(f"   📏 Sample text length: {sample_length} chars")
            if sample_length < 50:
                print(f"   ⚠️  WARNING: Text seems very short!")
                print(f"   Preview: {texts[0][:200]}")
        print()
        
        # Check cache
        # attach metadata hashes to self temporarily so _check_cache can access them
        setattr(self, '_provided_metadata_hashes', metadata_hashes)
        embeddings = self._check_cache(chunk_ids)
        # remove the temporary attribute
        if hasattr(self, '_provided_metadata_hashes'):
            delattr(self, '_provided_metadata_hashes')
        cached_count = len([e for e in embeddings if e is not None])
        
        if cached_count > 0:
            print(f"📦 Found {cached_count} cached embeddings")
        
        # Generate missing embeddings
        missing_indices = [i for i, e in enumerate(embeddings) if e is None]
        
        if missing_indices:
            print(f"🔄 Generating {len(missing_indices)} new embeddings...")
            
            missing_texts = [texts[i] for i in missing_indices]
            missing_ids = [chunk_ids[i] for i in missing_indices]
            
            new_embeddings = self._generate_batch_embeddings(missing_texts)
            
            # Cache new embeddings (store with metadata hashes)
            missing_hashes = [metadata_hashes[i] for i in missing_indices]
            self._cache_embeddings(missing_ids, new_embeddings, missing_hashes)
            
            # Insert into results
            for idx, embedding in zip(missing_indices, new_embeddings):
                embeddings[idx] = embedding
        
        # Create output structure
        result = {
            'embeddings': embeddings,
            'chunk_ids': chunk_ids,
            'metadata': metadata_list,
            'config': {
                'provider': self.provider,
                'model': self.model,
                'dimension': self.dimension,
                'total_chunks': len(chunks),
                'embedded_chunks': len([e for e in embeddings if e is not None]),
                'skipped_chunks': empty_count
            },
            'statistics': self._compute_statistics(embeddings)
        }
        
        print(f"\n✅ Embedding generation complete!")
        print(f"   Total embeddings: {len(embeddings)}")
        print(f"   Dimension: {self.dimension}")
        print(f"   Cached: {cached_count}")
        print(f"   Newly generated: {len(missing_indices)}")
        
        return result
    
    def _create_enriched_text(self, chunk: Dict[str, Any]) -> str:
        """
        NEW: Create rich contextual text for embedding
        Combines code with metadata for better semantic search
        """
        parts = []
        
        # 1. File and location context
        file_path = chunk.get('file_path', '')
        if file_path:
            parts.append(f"File: {file_path}")
        
        # 2. Code element identification
        chunk_type = chunk.get('chunk_type', '')
        if chunk_type:
            parts.append(f"Type: {chunk_type}")
        
        # Function/Class/Method name
        if chunk.get('function_name'):
            parts.append(f"Function: {chunk['function_name']}")
        elif chunk.get('class_name'):
            parts.append(f"Class: {chunk['class_name']}")
            if chunk.get('method_name'):
                parts.append(f"Method: {chunk['method_name']}")
        
        # 3. Purpose/Description (NEW - critical for understanding)
        hierarchical = chunk.get('hierarchical_context', {})
        if hierarchical:
            local_ctx = hierarchical.get('local', {})
            purpose = local_ctx.get('purpose', '')
            if purpose:
                parts.append(f"Purpose: {purpose}")
        
        # 4. Language
        language = chunk.get('language', '')
        if language:
            parts.append(f"Language: {language}")
        
        # 5. Semantic tags and keywords
        semantic_tags = chunk.get('semantic_tags', [])
        if semantic_tags:
            parts.append(f"Tags: {', '.join(semantic_tags[:5])}")
        
        keywords = chunk.get('keywords', [])
        if keywords:
            parts.append(f"Keywords: {', '.join(keywords[:5])}")
        
        # 6. THE ACTUAL CODE (MOST IMPORTANT)
        content = chunk.get('content', '')
        if content:
            # Truncate if too long (embedding models have token limits)
            max_content_length = 6000  # ~1500 tokens
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            parts.append(f"\nCode:\n{content}")
        
        # Combine all parts
        enriched_text = "\n".join(parts)
        
        return enriched_text
    
    def _generate_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings in batches with progress tracking"""
        all_embeddings = []
        
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        for i in tqdm(range(0, len(texts), self.batch_size), 
                     desc="Embedding batches", 
                     total=total_batches,
                     unit="batch"):
            batch = texts[i:i + self.batch_size]
            
            try:
                if self.provider == "openai":
                    batch_embeddings = self._embed_openai(batch)
                elif self.provider == "sentence-transformers":
                    batch_embeddings = self._embed_sentence_transformers(batch)
                elif self.provider == "cohere":
                    batch_embeddings = self._embed_cohere(batch)
                elif self.provider == "huggingface":
                    batch_embeddings = self._embed_huggingface(batch)
                
                all_embeddings.extend(batch_embeddings)
                
                # Rate limiting for API providers
                if self.provider in ["openai", "cohere"]:
                    time.sleep(0.05)  # 50ms between batches
                
            except Exception as e:
                print(f"\n⚠️  Error embedding batch {i//self.batch_size}: {e}")
                # Add zero vectors for failed batch
                all_embeddings.extend([np.zeros(self.dimension, dtype=np.float32) for _ in batch])
        
        return all_embeddings
    
    def _embed_openai(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using OpenAI"""
        # Truncate texts to fit token limit
        max_tokens = 8000
        truncated_texts = [t[:max_tokens*4] for t in texts]  # ~4 chars per token
        
        response = self.embedding_model.embeddings.create(
            input=truncated_texts,
            model=self.model
        )
        
        embeddings = [np.array(item.embedding, dtype=np.float32) for item in response.data]
        return embeddings
    
    def _embed_sentence_transformers(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using Sentence-Transformers"""
        embeddings = self.embedding_model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=self.batch_size
        )
        return [emb.astype(np.float32) for emb in embeddings]
    
    def _embed_cohere(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using Cohere"""
        response = self.embedding_model.embed(
            texts=texts,
            model=self.model,
            input_type="search_document"
        )
        
        embeddings = [np.array(emb, dtype=np.float32) for emb in response.embeddings]
        return embeddings
    
    def _embed_huggingface(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using HuggingFace"""
        import torch
        
        # Tokenize
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.embedding_model(**encoded)
            # Mean pooling
            embeddings = outputs.last_hidden_state.mean(dim=1)
        
        return [emb.numpy().astype(np.float32) for emb in embeddings]
    
    def _check_cache(self, chunk_ids: List[str]) -> List[Optional[np.ndarray]]:
        """Check cache for existing embeddings"""
        cache_file = self.cache_dir / f"{self.provider}_{self.model.replace('/', '_')}.json"
        
        embeddings = [None] * len(chunk_ids)
        
        if not cache_file.exists():
            return embeddings
        
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)

            for i, chunk_id in enumerate(chunk_ids):
                if chunk_id in cache:
                    entry = cache[chunk_id]
                    # new cache format: {chunk_id: {"vector": [...], "metadata_hash": "..."}}
                    if isinstance(entry, dict) and 'vector' in entry and 'metadata_hash' in entry and isinstance(entry['vector'], list):
                        # compare metadata hash provided by caller (attached to self by generate_embeddings)
                        provided_hashes = getattr(self, '_provided_metadata_hashes', None)
                        if provided_hashes:
                            expected = provided_hashes[i]
                            if expected and entry.get('metadata_hash') == expected:
                                embeddings[i] = np.array(entry['vector'], dtype=np.float32)
                            else:
                                embeddings[i] = None
                        else:
                            # no metadata hashes provided -> accept cached vector
                            embeddings[i] = np.array(entry['vector'], dtype=np.float32)
                    elif isinstance(entry, list):
                        # old format: direct vector list
                        provided_hashes = getattr(self, '_provided_metadata_hashes', None)
                        if provided_hashes:
                            # caller provided metadata hashes -> treat old-format cache as stale
                            embeddings[i] = None
                        else:
                            embeddings[i] = np.array(entry, dtype=np.float32)
        
        except Exception as e:
            print(f"⚠️  Error loading cache: {e}")
        
        return embeddings
    
    def _cache_embeddings(self, chunk_ids: List[str], embeddings: List[np.ndarray], metadata_hashes: List[str] = None):
        """Cache embeddings to disk"""
        cache_file = self.cache_dir / f"{self.provider}_{self.model.replace('/', '_')}.json"
        
        # Load existing cache
        cache = {}
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
            except:
                pass
        
        # Add new embeddings
        if metadata_hashes and len(metadata_hashes) == len(chunk_ids):
            for chunk_id, embedding, mh in zip(chunk_ids, embeddings, metadata_hashes):
                cache[chunk_id] = {
                    'vector': embedding.tolist(),
                    'metadata_hash': mh
                }
        else:
            for chunk_id, embedding in zip(chunk_ids, embeddings):
                cache[chunk_id] = embedding.tolist()
        
        # Save cache
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            print(f"⚠️  Error saving cache: {e}")
    
    def _compute_statistics(self, embeddings: List[np.ndarray]) -> Dict[str, Any]:
        """Compute statistics about embeddings"""
        valid_embeddings = [e for e in embeddings if e is not None and e.size > 0]
        
        if not valid_embeddings:
            return {}
        
        embeddings_array = np.stack(valid_embeddings)
        
        return {
            'count': len(valid_embeddings),
            'dimension': self.dimension,
            'mean_norm': float(np.mean(np.linalg.norm(embeddings_array, axis=1))),
            'std_norm': float(np.std(np.linalg.norm(embeddings_array, axis=1))),
            'min_value': float(embeddings_array.min()),
            'max_value': float(embeddings_array.max()),
            'mean_value': float(embeddings_array.mean()),
            'sparsity': float((embeddings_array == 0).sum() / embeddings_array.size)
        }
    
    def save_embeddings(self, result: Dict[str, Any], output_path: str):
        """Save embeddings to disk in multiple formats"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        valid_vectors = []
        valid_records = []

        for embedding, meta in zip(result['embeddings'], result['metadata']):
            if embedding is None:
                continue  # skip failed / empty chunks
            
            valid_vectors.append(embedding)
            valid_records.append({
                "vector": embedding.tolist(),  # vector values
                **meta                         # flatten metadata on top
            })

        # Save .npy
        np.save(output_path.with_suffix('.npy'), np.stack(valid_vectors))

        # Save JSON
        with open(output_path.with_suffix('.json'), 'w', encoding='utf-8') as f:
            json.dump(valid_records, f, indent=2)

        print(f"\n💾 Saved embeddings:")
        print(f"   Vectors: {output_path.with_suffix('.npy')}")
        print(f"   Metadata: {output_path.with_suffix('.json')}")
        print(f"   Total saved records: {len(valid_records)}")

"""
Main Data Processor
Orchestrates chunking, metadata enrichment, and knowledge graph building
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from .chunker import IntelligentChunker, Chunk, ChunkType
from .metadata_enricher import MetadataEnricher
from .knowledge_graph import KnowledgeGraphBuilder
from .relationship_mapper import RelationshipMapper
from .mermaid_generator import MermaidGenerator


class DataProcessor:
    """
    Main processor that:
    1. Loads collected repository data
    2. Chunks content intelligently
    3. Enriches with metadata
    4. Builds knowledge graph
    5. Creates relationship mappings
    6. Outputs processed data for embeddings
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        enable_parallel: bool = True,
        max_workers: int = 4,
    ):
        """
        Args:
            chunk_size: Target chunk size in tokens
            overlap: Overlap between chunks
            enable_parallel: Use parallel processing
            max_workers: Number of parallel workers
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers

        self.chunker = None
        self.enricher = None
        self.graph_builder = None
        self.relationship_mapper = None

        self.raw_data = {}

        self.chunks = []
        self.enriched_chunks = []
        self.knowledge_graph = {}
        self.relationships = {}
        self.diagrams = {}
        self.stats = {}

    def process_repository(
        self, input_file: str, output_dir: str = "./processed"
    ) -> Dict[str, Any]:
        """
        Main processing pipeline

        Args:
            input_file: Path to collected JSON data
            output_dir: Output directory for processed data

        Returns:
            Processing statistics and results
        """
        print(f"\n{'='*70}")
        print(f"🚀 DATA PROCESSING PIPELINE - STEP 2")
        print(f"{'='*70}\n")

        # Load data
        print("📥 Step 1/6: Loading repository data...")
        repo_data = self._load_data(input_file)
        repo_name = Path(input_file).stem

        print(f"   Repository: {repo_name}")
        print(f"   Code files: {len(repo_data.get('code_files', []))}")
        print(f"   Documentation: {len(repo_data.get('documentation', []))}")
        print(f"   Issues: {len(repo_data.get('issues', []))}")
        print(f"   PRs: {len(repo_data.get('prs', []))}")
        print(f"   Commits: {len(repo_data.get('commits', []))}")

        # Initialize processors
        print("\n🔧 Step 2/6: Initializing processors...")
        self.chunker = IntelligentChunker(
            chunk_size=self.chunk_size, overlap=self.overlap
        )
        self.enricher = MetadataEnricher(repo_data)
        self.graph_builder = KnowledgeGraphBuilder(repo_data)
        self.relationship_mapper = RelationshipMapper(repo_data)

        # Chunk all content
        print("\n✂️  Step 3/6: Chunking content...")
        self.chunks = self._chunk_all_content(repo_data)
        print(f"   ✓ Created {len(self.chunks)} chunks")

        # Enrich metadata
        print("\n🏷️  Step 4/6: Enriching metadata...")
        self.enriched_chunks = self._enrich_all_chunks()
        print(f"   ✓ Enriched {len(self.enriched_chunks)} chunks")

        # Build knowledge graph
        print("\n🕸️  Step 5/6: Building knowledge graph...")
        self.knowledge_graph = self.graph_builder.build(self.enriched_chunks)
        print(f"   ✓ Graph nodes: {self.knowledge_graph.get('node_count', 0)}")
        print(f"   ✓ Graph edges: {self.knowledge_graph.get('edge_count', 0)}")

        # Map relationships
        print("\n🔗 Step 6/6: Mapping relationships...")
        self.relationships = self.relationship_mapper.map_relationships(
            self.enriched_chunks, self.knowledge_graph
        )
        print(
            f"   ✓ Issue-PR links: {len(self.relationships.get('issue_pr_links', []))}"
        )
        print(
            f"   ✓ File dependencies: {len(self.relationships.get('file_dependencies', []))}"
        )

        # Generate Mermaid diagrams
        print("\n📊 Step 7/7: Generating Mermaid diagrams...")
        mermaid_generator = MermaidGenerator(
            processed_data={
                'chunks': self.enriched_chunks,
                'knowledge_graph': self.knowledge_graph,
                'relationships': self.relationships
            },
            raw_data=self.raw_data  # NEW: Pass raw data for dynamic diagrams
        )

        self.diagrams = mermaid_generator.generate_all_diagrams()
        print(f"   ✓ Generated {len(self.diagrams)} diagram types")

        # Show available dynamic diagrams
        if 'diagram_index' in self.diagrams:
            diagram_index = json.loads(self.diagrams['diagram_index'])
            dynamic_count = len(diagram_index.get('dynamic_diagrams', []))
            print(f"   ℹ️  {dynamic_count} dynamic diagram types available")
            print(f"   ℹ️  {len(diagram_index.get('available_issues', []))} issues indexed")
            print(f"   ℹ️  {len(diagram_index.get('available_prs', []))} PRs indexed")

        # Save diagrams
        diagram_files = mermaid_generator.save_diagrams(output_dir)
        print(f"   ✓ Saved diagrams to: {output_dir}/diagrams/")

        # Save results
        print("\n💾 Saving processed data...")
        output_path = self._save_results(repo_name, output_dir)

        # Generate statistics
        self._generate_statistics(repo_data)

        print(f"\n{'='*70}")
        print("✅ PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"\n📊 Statistics:")
        print(f"   Total chunks: {self.stats['total_chunks']}")
        print(f"   Onboarding chunks: {self.stats['onboarding_chunks']}")
        print(f"   Offboarding chunks: {self.stats['offboarding_chunks']}")
        print(f"   Average chunk size: {self.stats['avg_chunk_size']} tokens")
        print(f"   High importance chunks: {self.stats['high_importance_chunks']}")
        print(f"\n💾 Output:")
        print(f"   Location: {output_path}")
        print(f"   Diagrams: {output_dir}/diagrams/ (6 types)")
        print(f"   Combined view: {output_dir}/DIAGRAMS.md")
        print(f"   Ready for embedding generation (Step 3)")
        print(f"\n{'='*70}\n")

        return {
            "output_path": output_path,
            "stats": self.stats,
            "chunk_count": len(self.enriched_chunks),
            "diagrams": list(self.diagrams.keys()),
            "diagram_files": diagram_files,
        }

    def _load_data(self, input_file: str) -> Dict[str, Any]:
        """Load collected repository data"""
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    def _chunk_all_content(self, repo_data: Dict[str, Any]) -> List[Chunk]:
        """Chunk all repository content"""
        all_chunks = []

        # Chunk code files
        code_files = repo_data.get("code_files", [])
        if code_files:
            print(f"   Chunking {len(code_files)} code files...")
            if self.enable_parallel:
                chunks = self._parallel_chunk(code_files, "code")
            else:
                chunks = self._sequential_chunk(code_files, "code")
            all_chunks.extend(chunks)
            print(f"   ✓ Code chunks: {len(chunks)}")

        # Chunk documentation
        docs = repo_data.get("documentation", [])
        if docs:
            print(f"   Chunking {len(docs)} documentation files...")
            if self.enable_parallel:
                chunks = self._parallel_chunk(docs, "documentation")
            else:
                chunks = self._sequential_chunk(docs, "documentation")
            all_chunks.extend(chunks)
            print(f"   ✓ Documentation chunks: {len(chunks)}")

        # Chunk onboarding data
        onboarding = repo_data.get("onboarding", {})
        if onboarding:
            print(f"   Chunking onboarding data...")
            chunks = self._chunk_onboarding_data(onboarding)
            all_chunks.extend(chunks)
            print(f"   ✓ Onboarding chunks: {len(chunks)}")

        # Chunk offboarding data
        offboarding = repo_data.get("offboarding", {})
        if offboarding:
            print(f"   Chunking offboarding data...")
            chunks = self._chunk_offboarding_data(offboarding)
            all_chunks.extend(chunks)
            print(f"   ✓ Offboarding chunks: {len(chunks)}")

        # Chunk issues
        issues = repo_data.get("issues", [])
        if issues:
            print(f"   Chunking {len(issues)} issues...")
            chunks = self._chunk_issues(issues)
            all_chunks.extend(chunks)
            print(f"   ✓ Issue chunks: {len(chunks)}")

        # Chunk PRs
        prs = repo_data.get("prs", [])
        if prs:
            print(f"   Chunking {len(prs)} pull requests...")
            chunks = self._chunk_prs(prs)
            all_chunks.extend(chunks)
            print(f"   ✓ PR chunks: {len(chunks)}")

        # Chunk commits (sample only - too many)
        commits = repo_data.get("commits", [])[:100]
        if commits:
            print(f"   Chunking {len(commits)} commits (sampled)...")
            chunks = self._chunk_commits(commits)
            all_chunks.extend(chunks)
            print(f"   ✓ Commit chunks: {len(chunks)}")

        return all_chunks

    def _sequential_chunk(self, items: List[Dict], item_type: str) -> List[Chunk]:
        """Chunk items sequentially"""
        chunks = []
        for item in tqdm(items, desc=f"Chunking {item_type}", leave=False):
            if item_type == "code":
                chunks.extend(self.chunker.chunk_code_file(item))
            elif item_type == "documentation":
                chunks.extend(self.chunker.chunk_documentation(item))
        return chunks

    def _parallel_chunk(self, items: List[Dict], item_type: str) -> List[Chunk]:
        """Chunk items in parallel"""
        chunks = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            if item_type == "code":
                futures = {
                    executor.submit(self.chunker.chunk_code_file, item): item
                    for item in items
                }
            elif item_type == "documentation":
                futures = {
                    executor.submit(self.chunker.chunk_documentation, item): item
                    for item in items
                }
            else:
                return self._sequential_chunk(items, item_type)

            for future in tqdm(
                as_completed(futures),
                total=len(items),
                desc=f"Chunking {item_type}",
                leave=False,
            ):
                try:
                    result = future.result()
                    chunks.extend(result)
                except Exception as e:
                    print(f"   ⚠️ Error chunking: {e}")

        return chunks

    def _chunk_onboarding_data(self, onboarding: Dict[str, Any]) -> List[Chunk]:
        """Chunk onboarding-specific data"""
        chunks = []

        # Setup instructions
        for idx, instruction in enumerate(onboarding.get("setup_instructions", [])):
            content = f"## {instruction.get('section', 'Setup')}\n\n"
            content += "\n".join(instruction.get("steps", []))

            chunk = Chunk(
                content=content,
                chunk_type=ChunkType.DOCUMENTATION,
                metadata={
                    "source": "onboarding",
                    "subsection": "setup_instructions",
                    "index": idx,
                },
                chunk_id=f"onboarding_setup_{idx}",
                importance_score=2.5,
                tokens=self.chunker._estimate_tokens(content),
            )
            chunks.append(chunk)

        env_config = onboarding.get("environment_config", {})
        if env_config:
            content = "# Environment Configuration\n\n"
            content += "## Required Variables:\n"
            content += "\n".join(
                [f"- {var}" for var in env_config.get("required_env_vars", [])]
            )
            content += "\n\n## Optional Variables:\n"
            content += "\n".join(
                [f"- {var}" for var in env_config.get("optional_env_vars", [])]
            )

            chunk = Chunk(
                content=content,
                chunk_type=ChunkType.CONFIG,
                metadata={"source": "onboarding", "subsection": "environment_config"},
                chunk_id="onboarding_env_config",
                importance_score=2.5,
                tokens=self.chunker._estimate_tokens(content),
            )
            chunks.append(chunk)

        for idx, step in enumerate(onboarding.get("quick_start_guide", [])):
            content = f"## Quick Start Step {step.get('step', idx+1)}\n\n"
            content += f"```{step.get('type', 'bash')}\n{step.get('code', '')}\n```"

            chunk = Chunk(
                content=content,
                chunk_type=ChunkType.DOCUMENTATION,
                metadata={
                    "source": "onboarding",
                    "subsection": "quick_start",
                    "step": step.get("step"),
                },
                chunk_id=f"onboarding_quickstart_{idx}",
                importance_score=2.0,
                tokens=self.chunker._estimate_tokens(content),
            )
            chunks.append(chunk)

        return chunks

    def _chunk_offboarding_data(self, offboarding: Dict[str, Any]) -> List[Chunk]:
        """Chunk offboarding-specific data"""
        chunks = []

        # Workarounds and hacks
        for idx, item in enumerate(offboarding.get("workarounds_and_hacks", [])):
            content = f"# Workaround in {item.get('file', 'unknown')}\n\n"
            content += item.get("comment", "")

            chunk = Chunk(
                content=content,
                chunk_type=ChunkType.COMMENT,
                metadata={
                    "source": "offboarding",
                    "subsection": "workarounds",
                    "file": item.get("file"),
                    "type": item.get("type"),
                },
                chunk_id=f"offboarding_workaround_{idx}",
                importance_score=1.8,
                tokens=self.chunker._estimate_tokens(content),
            )
            chunks.append(chunk)

        for idx, item in enumerate(offboarding.get("design_decisions", [])):
            content = f"# Design Decision\n\n"
            if item.get("file"):
                content += f"**File:** {item['file']}\n\n"
            content += item.get("comment", item.get("message", ""))

            chunk = Chunk(
                content=content,
                chunk_type=ChunkType.COMMENT,
                metadata={
                    "source": "offboarding",
                    "subsection": "design_decisions",
                    "file": item.get("file"),
                    "source_type": item.get("source", "unknown"),
                },
                chunk_id=f"offboarding_decision_{idx}",
                importance_score=2.0,
                tokens=self.chunker._estimate_tokens(content),
            )
            chunks.append(chunk)

        # Complex areas
        for idx, item in enumerate(offboarding.get("complex_areas", [])):
            content = f"# Complex Area: {item.get('file', 'unknown')}\n\n"
            content += f"**Complexity Score:** {item.get('complexity_score')}\n"
            content += f"**Indicators:** {', '.join(item.get('indicators', []))}\n"
            content += f"**Priority:** {item.get('priority', 'medium')}"

            chunk = Chunk(
                content=content,
                chunk_type=ChunkType.COMMENT,
                metadata={
                    "source": "offboarding",
                    "subsection": "complex_areas",
                    "file": item.get("file"),
                    "complexity_score": item.get("complexity_score"),
                    "priority": item.get("priority"),
                },
                chunk_id=f"offboarding_complex_{idx}",
                importance_score=1.5,
                tokens=self.chunker._estimate_tokens(content),
            )
            chunks.append(chunk)

        return chunks

    def _chunk_issues(self, issues: List[Dict]) -> List[Chunk]:
        chunks = []

        def _k(it):
            n = it.get("number")
            return (int(n) if n is not None else 1 << 30, it.get("created_at") or "")

        issues_sorted = sorted(issues, key=_k)

        for issue in issues_sorted:
            chunks.extend(self.chunker.chunk_issue(issue))
        return chunks

    def _chunk_prs(self, prs: List[Dict]) -> List[Chunk]:
        chunks = []

        def _k(pr):
            n = pr.get("number")
            return (int(n) if n is not None else 1 << 30, pr.get("created_at") or "")

        prs_sorted = sorted(prs, key=_k)

        for pr in prs_sorted:
            chunks.extend(self.chunker.chunk_pr(pr))
        return chunks

    def _chunk_commits(self, commits: List[Dict]) -> List[Chunk]:
        """Chunk commits"""
        chunks = []
        for commit in commits:
            chunk = self.chunker.chunk_commit(commit)
            chunks.append(chunk)
        return chunks

    def _enrich_all_chunks(self) -> List[Dict[str, Any]]:
        """Enrich all chunks with metadata"""
        enriched = []

        if self.enable_parallel:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self.enricher.enrich_chunk, chunk): chunk
                    for chunk in self.chunks
                }

                for future in tqdm(
                    as_completed(futures),
                    total=len(self.chunks),
                    desc="Enriching chunks",
                    leave=False,
                ):
                    try:
                        result = future.result()
                        result["content"] = futures[future].content
                        enriched.append(result)
                    except Exception as e:
                        print(f"   ⚠️ Error enriching chunk: {e}")
        else:
            for chunk in tqdm(self.chunks, desc="Enriching chunks", leave=False):
                try:
                    metadata = self.enricher.enrich_chunk(chunk)
                    metadata["content"] = chunk.content
                    enriched.append(metadata)
                except Exception as e:
                    print(f"   ⚠️ Error enriching chunk: {e}")

        return enriched

    def _save_results(self, repo_name: str, output_dir: str) -> str:
        """Save processed data"""
        os.makedirs(output_dir, exist_ok=True)

        # Main processed data file
        output_file = os.path.join(output_dir, f"{repo_name}_processed.json")

        output_data = {
            "repository": repo_name,
            "processing_config": {
                "chunk_size": self.chunk_size,
                "overlap": self.overlap,
                "parallel_processing": self.enable_parallel,
            },
            "chunks": self.enriched_chunks,
            "knowledge_graph": self.knowledge_graph,
            "relationships": self.relationships,
            "diagrams": self.diagrams,
            "statistics": self.stats,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        # Save chunks separately for easy loading
        chunks_file = os.path.join(output_dir, f"{repo_name}_chunks.json")
        with open(chunks_file, "w", encoding="utf-8") as f:
            json.dump(self.enriched_chunks, f, indent=2, ensure_ascii=False)

        # Save knowledge graph separately
        graph_file = os.path.join(output_dir, f"{repo_name}_graph.json")
        with open(graph_file, "w", encoding="utf-8") as f:
            json.dump(self.knowledge_graph, f, indent=2, ensure_ascii=False)

        # Save Mermaid diagrams as markdown
        diagrams_md = os.path.join(output_dir, "DIAGRAMS.md")
        if self.diagrams and "combined" in self.diagrams:
            with open(diagrams_md, "w", encoding="utf-8") as f:
                f.write(self.diagrams["combined"])

        print(f"   ✓ Main data: {output_file}")
        print(f"   ✓ Chunks: {chunks_file}")
        print(f"   ✓ Graph: {graph_file}")
        print(f"   ✓ Diagrams: {diagrams_md}")

        return output_file

    def _generate_statistics(self, repo_data: Dict[str, Any]) -> None:
        """Generate processing statistics"""
        self.stats = {
            "total_chunks": len(self.enriched_chunks),
            "onboarding_chunks": sum(
                1
                for c in self.enriched_chunks
                if "onboarding" in c.get("semantic_tags", [])
            ),
            "offboarding_chunks": sum(
                1
                for c in self.enriched_chunks
                if "offboarding" in c.get("semantic_tags", [])
            ),
            "avg_chunk_size": (
                sum(c.get("tokens", 0) for c in self.enriched_chunks)
                / len(self.enriched_chunks)
                if self.enriched_chunks
                else 0
            ),
            "high_importance_chunks": sum(
                1 for c in self.enriched_chunks if c.get("importance_score", 0) >= 2.0
            ),
            "chunks_by_type": self._count_by_type(),
            "chunks_by_category": self._count_by_category(),
            "total_tokens": sum(c.get("tokens", 0) for c in self.enriched_chunks),
            "source_data": {
                "code_files": len(repo_data.get("code_files", [])),
                "documentation": len(repo_data.get("documentation", [])),
                "issues": len(repo_data.get("issues", [])),
                "prs": len(repo_data.get("prs", [])),
                "commits": len(repo_data.get("commits", [])),
            },
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count chunks by type"""
        counts = {}
        for chunk in self.enriched_chunks:
            chunk_type = chunk.get("chunk_type", "unknown")
            counts[chunk_type] = counts.get(chunk_type, 0) + 1
        return counts

    def _count_by_category(self) -> Dict[str, int]:
        """Count chunks by category"""
        counts = {}
        for chunk in self.enriched_chunks:
            category = chunk.get("category", "general")
            counts[category] = counts.get(category, 0) + 1
        return counts

    def get_chunks_by_importance(self, min_score: float = 2.0) -> List[Dict[str, Any]]:
        """Get high-importance chunks"""
        return [
            c for c in self.enriched_chunks if c.get("importance_score", 0) >= min_score
        ]

    def get_chunks_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get chunks with specific semantic tag"""
        return [c for c in self.enriched_chunks if tag in c.get("semantic_tags", [])]

    def get_chunks_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get chunks in specific category"""
        return [c for c in self.enriched_chunks if c.get("category") == category]

    def export_for_embeddings(self, output_file: str) -> None:
        """Export chunks in format ready for embedding generation"""
        embedding_data = []

        for chunk in self.enriched_chunks:
            embedding_data.append(
                {
                    "id": chunk["chunk_id"],
                    "text": chunk["content"],
                    "metadata": {
                        "type": chunk["chunk_type"],
                        "category": chunk.get("category"),
                        "importance": chunk.get("importance_score"),
                        "tags": chunk.get("semantic_tags", []),
                        "keywords": chunk.get("keywords", []),
                        "search_terms": chunk.get("search_terms", []),
                    },
                }
            )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(embedding_data, f, indent=2, ensure_ascii=False)

        print(f"   ✓ Exported {len(embedding_data)} chunks for embedding")
        print(f"   ✓ Location: {output_file}")

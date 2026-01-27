"""
Enterprise-Grade Embedding Generation (Step 3)
Optimized for GitHub-first → Gmail correlation with rich metadata
Supports hybrid embedding: content + entities + temporal context
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from collections import defaultdict

# Add workspace root (parent of backend) to path BEFORE any imports to support both script and module execution
# This allows importing 'backend' as a module
_workspace_root = Path(__file__).resolve().parents[3]  # Go up to workspace root
_workspace_root_str = str(_workspace_root)
if _workspace_root_str not in sys.path:
    sys.path.insert(0, _workspace_root_str)

# Also add backend directory for core imports
_backend_dir = Path(__file__).resolve().parents[2]
_backend_dir_str = str(_backend_dir)
if _backend_dir_str not in sys.path:
    sys.path.insert(0, _backend_dir_str)

# Now import using absolute imports (works for both script and module)
from backend.main.GenerateEmbedding.analytics.graph_nodes import prepare_graph_nodes
from backend.main.GenerateEmbedding.utils.file_utils import get_size
from backend.main.GenerateEmbedding.loaders.source_detector import detect_source_type
from backend.main.GenerateEmbedding.config.state import load_current_repo_from_state
from backend.main.GenerateEmbedding.preparation.chunk_preparer import prepare_chunks_for_embedding
from backend.main.GenerateEmbedding.analytics.repo_metrics import compute_repo_metrics
from backend.main.GenerateEmbedding.analytics.cost_estimator import estimate_cost
from backend.main.GenerateEmbedding.config.provider import auto_detect_provider
from backend.main.GenerateEmbedding.loaders.tech_summary_loader import inject_tech_summary
from core.GenerateEmbedding.generator import EmbeddingGenerator
from backend.utils.repo_normalizer import repo_matches, normalize_repo_name, normalize_repo_owner, extract_repo_parts
                
load_dotenv()


REPO_OWNER, REPO_NAME = load_current_repo_from_state()
FULL_REPO_NAME = f"{REPO_OWNER}/{REPO_NAME}"

print(f"\n{'='*70}")
print(f"GENERATING EMBEDDINGS FOR REPO: {REPO_OWNER}/{REPO_NAME}")
print(f"{'='*70}\n")


def batch_generate(args):
    processed_dir = Path("../../data/DataProcessing") / REPO_OWNER / REPO_NAME / "chunks"
    base_output_dir = Path(str(args.output_dir))
    output_dir = base_output_dir / REPO_OWNER / REPO_NAME

    normalized_current_owner, normalized_current_repo = extract_repo_parts(FULL_REPO_NAME)
    normalized_current_owner = normalized_current_owner or normalize_repo_owner(REPO_OWNER)
    normalized_current_repo = normalized_current_repo or normalize_repo_name(REPO_NAME)


    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    if not processed_dir.exists():
        print(f"Error: Processed directory not found: {processed_dir}")
        return

    # Pick up type-specific files only
    chunks_files = [
        f for f in processed_dir.glob("*_chunks.json")
        if not any(skip in f.name for skip in ['strategy', 'entities', '_git_chunks', '_gmail_chunks', 'aggregated'])
    ]

    if not chunks_files:
        print(f"Error: No chunks files found in {processed_dir}")
        return

    print(f"Found {len(chunks_files)} type-specific chunks files\n")

    # Group by repository and type with BETTER parsing
    by_repo = defaultdict(dict)
    for f in chunks_files:
        # Extract from filename: owner_repo_TYPE_chunks.json
        parts = f.stem.split('_')

        # Find the position of "chunks" to identify type
        if 'chunks' in parts:
            chunks_idx = parts.index('chunks')
            if chunks_idx > 0:
                # Type is the word RIGHT BEFORE "chunks"
                chunk_type = parts[chunks_idx - 1]
                # Repo name is everything BEFORE the type
                repo_name = '_'.join(parts[:chunks_idx - 1])

                # VALIDATION: Skip if chunk_type is empty or invalid
                if not chunk_type or chunk_type in ['git', 'gmail', 'unknown']:
                    print(f"   ⚠️  Skipping invalid chunk type '{chunk_type}' from {f.name}")
                    continue

                by_repo[repo_name][chunk_type] = f
            else:
                print(f"   ⚠️  Could not parse filename: {f.name}")
        else:
            print(f"   ⚠️  Invalid filename format (missing 'chunks'): {f.name}")

    if not by_repo:
        print(f"Error: No valid chunk files found after parsing")
        return

    # CRITICAL: Filter to only process current repo
    # The parsed repo_name from filename might not match, so we'll filter chunks instead
        
    print(f"Repositories found in filenames: {len(by_repo)}\n")
    for repo_name, types in by_repo.items():
        print(f"   {repo_name}:")
        for chunk_type, file in types.items():
            print(f"      {chunk_type}: {file.name}")
    print()
    
    # Filter: Only process files that are in the current repo's directory structure
    # Since files are already in processed_dir which is repo-specific, we can process them
    # But we'll filter chunks by repo_name when loading

    graph_file = processed_dir.parent / "graph_data.json"
    has_graph = graph_file.exists()

    provider = args.provider
    model = args.model

    if not provider:
        provider, default_model = auto_detect_provider()
        if not model:
            model = default_model
        print(f"Using provider: {provider} ({model})\n")

    try:
        generator = EmbeddingGenerator(
            provider=provider,
            model=model,
            batch_size=args.batch_size,
            cache_dir=Path(str(args.cache_dir))
        )
    except Exception as e:
        print(f"Error initializing generator: {e}")
        return

    results = []

    # Process each type-specific file
    for repo_name, type_files in by_repo.items():
        print(f"\n{'=' * 70}")
        print(f"Processing repository: {repo_name}")
        print(f"{'=' * 70}")

        any_chunk_file = next(iter(type_files.values()))
        repo_data_dir = any_chunk_file.parent.parent
        graph_file = repo_data_dir / "graph_data.json"
        
        has_graph = graph_file.exists()
        if has_graph:
            print(f"   🕸️  Found Graph Data: {graph_file}")
        else:
            print(f"   ⚠️  Graph Data NOT found at: {graph_file}")

        # Collect all chunks for combined index
        all_chunks_for_repo = []

        for chunk_type, chunks_file in type_files.items():
            print(f"\n   Type: {chunk_type}")
            print(f"   File: {chunks_file.name}")

            try:
                # Load chunks
                with open(chunks_file, 'r', encoding='utf-8') as f:
                    chunks = json.load(f)

                if not chunks:
                    print(f"      Warning: Empty file, skipping...")
                    continue

                print(f"      Raw chunks: {len(chunks)}")
                
                
                
                filtered_chunks = []
                skipped_count = 0
                for chunk in chunks:
                    chunk_repo_raw = chunk.get('repo_name', '')
                    chunk_owner_raw = chunk.get('repo_owner', '')
                    
                    # Normalize chunk repo info
                    normalized_chunk_owner, normalized_chunk_repo = extract_repo_parts(chunk_repo_raw)
                    if not normalized_chunk_owner and chunk_owner_raw:
                        normalized_chunk_owner = normalize_repo_owner(chunk_owner_raw)
                    if not normalized_chunk_repo:
                        normalized_chunk_repo = normalize_repo_name(chunk_repo_raw)
                    
                    # Use flexible matching
                    matches_repo = repo_matches(
                        normalized_current_owner, normalized_current_repo,
                        normalized_chunk_owner, normalized_chunk_repo
                    )
                    
                    if matches_repo:
                        # Ensure repo_name is set correctly
                        chunk['repo_name'] = REPO_NAME
                        chunk['repo_owner'] = REPO_OWNER
                        filtered_chunks.append(chunk)
                    else:
                        skipped_count += 1
                
                if skipped_count > 0:
                    print(f"      ⚠️  Filtered out {skipped_count} chunks from other repositories")
                
                chunks = filtered_chunks
                
                if not chunks:
                    print(f"      Warning: No chunks for current repo after filtering, skipping...")
                    results.append((repo_name, chunk_type, "Skipped", "No chunks for current repo"))
                    continue
                
                print(f"      Chunks for {REPO_OWNER}/{REPO_NAME}: {len(chunks)}")

                # Prepare chunks for embedding
                prepared_chunks, prep_stats = prepare_chunks_for_embedding(chunks)

                print(f"      Enhanced chunks: {prep_stats['processed']}")
                print(f"      Skipped: {prep_stats['skipped']}")

                if prep_stats['processed'] == 0:
                    print(f"      Warning: No chunks to embed, skipping...")
                    results.append((repo_name, chunk_type, "Skipped", "No embeddable chunks"))
                    continue

                # Generate embeddings
                print(f"      Generating embeddings...")
                result = generator.generate_embeddings(prepared_chunks)

                # Create type-specific directory
                type_dir = output_dir / chunk_type
                type_dir.mkdir(parents=True, exist_ok=True)

                # Save embeddings
                output_path = type_dir / chunk_type
                generator.save_embeddings(result, str(output_path))

                print(f"      Saved -> {chunk_type}/{chunk_type}.npy + {chunk_type}.json")

                results.append((repo_name, chunk_type, "Success", result['statistics']))

                # Collect for combined index (chunks are already filtered above)
                all_chunks_for_repo.extend(chunks)

            except Exception as e:
                print(f"      Error: {e}")
                import traceback
                traceback.print_exc()
                results.append((repo_name, chunk_type, "Failed", str(e)))

        # Generate combined "all" index for this repository
        # Double-check: Filter again to ensure only current repo chunks
        final_all_chunks = []
        for chunk in all_chunks_for_repo:
                        
            chunk_repo_raw = chunk.get('repo_name', '')
            chunk_owner_raw = chunk.get('repo_owner', '')
            
            
            # Normalize chunk repo
            normalized_chunk_owner, normalized_chunk_repo = extract_repo_parts(chunk_repo_raw)
            if not normalized_chunk_owner and chunk_owner_raw:
                normalized_chunk_owner = normalize_repo_owner(chunk_owner_raw)
            if not normalized_chunk_repo:
                normalized_chunk_repo = normalize_repo_name(chunk_repo_raw)
            
            # Use flexible matching
            if repo_matches(
                normalized_current_owner, normalized_current_repo,
                normalized_chunk_owner, normalized_chunk_repo
            ):
                chunk['repo_name'] = REPO_NAME
                chunk['repo_owner'] = REPO_OWNER
                final_all_chunks.append(chunk)
        
        if final_all_chunks:
            print(f"\n   Generating combined 'all' index for {REPO_OWNER}/{REPO_NAME}...")

            try:
                print(f"      Total chunks: {len(final_all_chunks)}")

                # Prepare all chunks (use filtered chunks)
                prepared_all, prep_all_stats = prepare_chunks_for_embedding(final_all_chunks)

                print(f"      Enhanced: {prep_all_stats['processed']}")

                if prep_all_stats['processed'] > 0:
                    # Generate combined embeddings
                    combined_result = generator.generate_embeddings(prepared_all)

                    # Save to "all" directory
                    all_dir = output_dir / "all"
                    all_dir.mkdir(parents=True, exist_ok=True)

                    combined_path = all_dir / "all"
                    generator.save_embeddings(combined_result, str(combined_path))

                    print(f"      Saved -> all/all.npy + all.json")

                    results.append((repo_name, "all", "Success", combined_result['statistics']))

            except Exception as e:
                print(f"      Failed to generate combined index: {e}")
                results.append((repo_name, "all", "Failed", str(e)))

    if has_graph:
        print(f"\n{'=' * 70}\nProcessing Graph Nodes: {REPO_NAME}\n{'=' * 70}")
        try:
            with open(graph_file, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            
            # Use the helper we defined earlier
            prepared_nodes, node_stats = prepare_graph_nodes(graph_data)
            
            if prepared_nodes:
                print(f"      Generating embeddings for {len(prepared_nodes)} graph nodes...")
                result = generator.generate_embeddings(prepared_nodes)
                
                # Save to "graph" directory
                graph_out_dir = output_dir / "graph"
                graph_out_dir.mkdir(parents=True, exist_ok=True)

                repo_out_dir = base_output_dir / REPO_OWNER / REPO_NAME
                graph_out_dir = repo_out_dir / "graph"
                graph_out_dir.mkdir(parents=True, exist_ok=True)
                
                generator.save_embeddings(result, str(graph_out_dir / "graph_nodes"))
                print(f"      Saved -> graph/graph_nodes.npy + graph_nodes.json")
                
                results.append((REPO_NAME, "graph_nodes", "Success", result['statistics']))
            else:
                print("      No embeddable nodes found.")
                
        except Exception as e:
            print(f"      Failed to embed graph nodes: {e}")
            import traceback; traceback.print_exc()
            results.append((REPO_NAME, "graph_nodes", "Failed", str(e)))

    # Print summary
    print(f"\n{'=' * 70}")
    print("BATCH GENERATION SUMMARY")
    print(f"{'=' * 70}\n")

    successful = [r for r in results if r[2] == "Success"]
    skipped = [r for r in results if r[2] == "Skipped"]
    failed = [r for r in results if r[2] == "Failed"]

    print(f"Successful: {len(successful)}/{len(results)}")
    if skipped:
        print(f"Skipped: {len(skipped)}/{len(results)}")
    if failed:
        print(f"Failed: {len(failed)}/{len(results)}")

    if successful:
        # Group by type
        by_type_summary = defaultdict(int)
        total_embeddings = 0

        for repo, ctype, status, stats in successful:
            if isinstance(stats, dict):
                count = stats.get('count', 0)
                by_type_summary[ctype] += count
                total_embeddings += count

        print(f"\nTotal embeddings generated: {total_embeddings}")
        print(f"\nBy type:")
        for ctype, count in sorted(by_type_summary.items()):
            print(f"   {ctype}: {count}")

    if failed:
        print(f"\nFailed:")
        for repo, ctype, status, error in failed:
            print(f"   {repo} ({ctype}): {error}")

    if skipped:
        print(f"\nSkipped:")
        for repo, ctype, status, reason in skipped:
            print(f"   {repo} ({ctype}): {reason}")

    print(f"\nOutput directory: {output_dir}")
    print(f"\nNext Step:")
    print(f"   python core/VectorDB/build_indices.py")

def main():
    parser = argparse.ArgumentParser(
        description="Enhanced embedding generation with entity + temporal + correlation context",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python generate_embeddings.py
        python generate_embeddings.py processed/repo_name_git_chunks.json
        python generate_embeddings.py --provider openai
        python generate_embeddings.py --batch
                """
    )
    parser.add_argument('input_file', nargs='?', help='Path to chunks JSON file')
    parser.add_argument('--output-dir', default='../../data/Embeddings/', help='Output directory')
    parser.add_argument('--provider', choices=['openai', 'sentence-transformers', 'cohere', 'huggingface'])
    parser.add_argument('--model', help='Model name')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--cache-dir', default='../../data/Embeddings/embeddings_cache', help='Cache directory')
    parser.add_argument('--batch', action='store_true', help='Process all chunks files')

    args = parser.parse_args()

    if args.batch:
        batch_generate(args)
        return

    # Use absolute paths from script location (not relative to CWD)
    backend_dir = Path(__file__).resolve().parents[2]
    processed_dir = backend_dir / "data" / "DataProcessing" / REPO_OWNER / REPO_NAME / "chunks"
    embeddings_base_dir = backend_dir / "data" / "Embeddings"
    output_base_dir = backend_dir / "data" / "Embeddings"
    
    chunks_files = sorted(
        f for f in processed_dir.glob("*_chunks.json")
        if not any(skip in f.name for skip in ['strategy', 'entities', 'aggregated'])
    )

    if not chunks_files:
        # Check if embeddings already exist for this repo
        embeddings_dir = embeddings_base_dir / REPO_OWNER / REPO_NAME
        if embeddings_dir.exists() and any(embeddings_dir.glob("*/faiss.index")):
            print(f"✅ Embeddings already exist for {REPO_OWNER}/{REPO_NAME}")
            print(f"   Location: {embeddings_dir}")
            print(f"\n   No processed chunks found at: {processed_dir}")
            print(f"   This is expected if embeddings were already generated.")
            print(f"\n   To regenerate embeddings:")
            print(f"   1. Run: python main/DataProcessing/process_data.py")
            print(f"   2. Then: python main/GenerateEmbedding/generate_embedding.py")
            sys.exit(0)
        
        print(f"Error: No JSON files found at {processed_dir}")
        print(f"\nTo generate embeddings, you need:")
        print(f"  1. Run data processing first: python main/DataProcessing/process_data.py")
        print(f"  2. Then generate embeddings: python main/GenerateEmbedding/generate_embedding.py")
        sys.exit(1)

    print(f"Found {len(chunks_files)} JSON files to embed:")
    for f in chunks_files:
        print("  ", f.name)

    provider = args.provider
    model = args.model

    # Use absolute paths for cache and output
    cache_dir = backend_dir / "data" / "Embeddings" / "embeddings_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    output_dir = output_base_dir / REPO_OWNER / REPO_NAME
    output_dir.mkdir(parents=True, exist_ok=True)


    if not provider:
        print("Auto-detecting embedding provider...")
        provider, default_model = auto_detect_provider()
        if provider == 'openai':
            print(f"Detected OpenAI API key")
        elif provider == 'cohere':
            print(f"Detected Cohere API key")
        else:
            print(f"No API keys found - using free Sentence-Transformers")
        if not model:
            model = default_model
        print(f"   Provider: {provider}")
        print(f"   Model: {model}\n")
    else:
        default_models = {
            'openai': 'text-embedding-3-small',
            'sentence-transformers': 'all-MiniLM-L6-v2',
            'cohere': 'embed-english-v3.0',
            'huggingface': 'sentence-transformers/all-MiniLM-L6-v2'
        }
        if not model:
            model = default_models[provider]

    print(f"{'='*70}")
    print(f"ENHANCED EMBEDDING GENERATION - STEP 3")
    print(f"{'='*70}\n")

    print(f"Loading chunks from: {len(chunks_files)} files")
    all_chunks = []
    for file_path in chunks_files:
        print(f"Loading chunks from {file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                all_chunks.extend(data)
            else:
                print(f"Warning: Skipping {file_path.name} - JSON is not a list")
                continue

    chunks = all_chunks
    print(f"\nTotal merged chunks: {len(chunks)}\n")

    chunks = inject_tech_summary(processed_dir, chunks)

    source_type = detect_source_type(chunks)
    if len(chunks_files) == 1:
        file_name = Path(chunks_files[0]).stem
    else:
        file_name = "combined"

    if not chunks:
        print(f"Error: No chunks found in file")
        sys.exit(1)

    print(f"   File: {file_name}")
    print(f"   Source: {source_type}")
    print(f"   Total chunks: {len(chunks)}")

    chunk_types = {}
    for chunk in chunks:
        ct = chunk.get('type', 'unknown')
        chunk_types[ct] = chunk_types.get(ct, 0) + 1

    print(f"\n   Chunk types:")
    for ct, count in sorted(chunk_types.items()):
        print(f"      {ct}: {count}")

    print("\nComputing repository metrics (lines, functions, structure)...")
    repo_metrics = compute_repo_metrics(chunks)
    metrics_chunk = {
        'chunk_id': f"repo_metrics_{int(datetime.now(timezone.utc).timestamp())}",
        'type': 'repo_metrics',
        'source': 'computed',
        'content': ("Repository metrics: "
                    f"total_lines={repo_metrics['total_lines']}, "
                    f"total_functions={repo_metrics['total_functions']}, "
                    f"total_files={repo_metrics['total_files']}. "
                    "By repo: " + ", ".join(f"{r}({s['files']} files)" for r, s in repo_metrics['by_repo'].items())),
        'metadata': {
            'computed_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'metrics': repo_metrics
        },
        'full_chunk': {'metrics': repo_metrics},
        'skip_embedding': False
    }
    chunks = [metrics_chunk] + chunks

    print(f"\nPreparing enhanced chunks for embedding...")
    print(f"   Extracting main content")
    print(f"   Formatting entity context")
    print(f"   Adding temporal context")
    if source_type == 'gmail':
        print(f"   Including GitHub correlation data")

    prepared_chunks, prep_stats = prepare_chunks_for_embedding(chunks)

    print(f"\n   Preparation complete:")
    print(f"      Total chunks: {prep_stats['total']}")
    print(f"      Will embed: {prep_stats['processed']}")
    print(f"      Skipped: {prep_stats['skipped']}")
    if prep_stats['raw_data_refs'] > 0:
        print(f"        Raw data refs: {prep_stats['raw_data_refs']} (too large)")
    if prep_stats['empty_content'] > 0:
        print(f"        Empty content: {prep_stats['empty_content']}")

    print(f"\n   By retrieval priority:")
    for priority in sorted(prep_stats['by_priority'].keys()):
        count = prep_stats['by_priority'][priority]
        print(f"      Priority {priority}: {count} chunks")

    if prep_stats['processed'] == 0:
        print(f"\nError: No chunks to embed!")
        sys.exit(1)

    if prepared_chunks:
        sample = prepared_chunks[0]
        print(f"\n   Sample enhanced chunk:")
        print(f"      ID: {sample.get('chunk_id', 'N/A')}")
        print(f"      Type: {sample.get('type', 'N/A')}")
        print(f"      Content length: {len(sample.get('content', ''))} chars")
        print(f"      Preview: {sample.get('content', '')[:150]}...\n")

    try:
        generator = EmbeddingGenerator(
            provider=provider,
            model=model,
            batch_size=args.batch_size,
            cache_dir=cache_dir
        )
    except Exception as e:
        print(f"\nError initializing embedding generator: {e}")
        print(f"\nInstallation guide:")
        if provider == 'openai':
            print(f"   1. pip install openai python-dotenv")
            print(f"   2. Create .env file with: OPENAI_API_KEY=your-key")
        elif provider == 'sentence-transformers':
            print(f"   pip install sentence-transformers")
        elif provider == 'cohere':
            print(f"   1. pip install cohere python-dotenv")
            print(f"   2. Create .env file with: COHERE_API_KEY=your-key")
        sys.exit(1)

    print("\nGenerating embeddings by chunk type...")
    
    # Group prepared chunks by type
    chunks_by_type = defaultdict(list)
    for prepared_chunk in prepared_chunks:
        chunk_type = prepared_chunk.get('type', 'unknown')
        chunks_by_type[chunk_type].append(prepared_chunk)
    
    # Track results by type
    type_results = {}
    all_chunks_for_combined = []
    
    # Generate embeddings for each chunk type separately
    print(f"\n   Found {len(chunks_by_type)} chunk types:")
    for chunk_type in sorted(chunks_by_type.keys()):
        print(f"      {chunk_type}: {len(chunks_by_type[chunk_type])} chunks")
    
    print("\n   Generating embeddings for each type...\n")
    
    for chunk_type, type_chunks in sorted(chunks_by_type.items()):
        if chunk_type == 'repo_metrics':
            # Skip metrics chunk for individual type generation
            all_chunks_for_combined.extend(type_chunks)
            continue
        
        print(f"   Processing {chunk_type}...")
        try:
            # Generate embeddings for this type
            type_result = generator.generate_embeddings(type_chunks)
            
            # Create type-specific directory
            type_dir = output_dir / chunk_type
            type_dir.mkdir(parents=True, exist_ok=True)
            
            # Save embeddings
            output_path = type_dir / chunk_type
            generator.save_embeddings(type_result, str(output_path))
            
            type_results[chunk_type] = {
                'path': output_path,
                'config': type_result['config'],
                'stats': type_result['statistics'],
                'count': len(type_chunks)
            }
            
            print(f"      ✓ Saved -> {chunk_type}/{chunk_type}.npy + {chunk_type}.json")
            print(f"        Embeddings: {type_result['statistics'].get('count', 0)}")
            
            # Collect for combined index
            all_chunks_for_combined.extend(type_chunks)
            
        except Exception as e:
            print(f"      ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate combined "all" index
    if all_chunks_for_combined:
        print(f"\n   Generating combined 'all' index...")
        try:
            print(f"      Total chunks: {len(all_chunks_for_combined)}")
            
            # Generate combined embeddings
            combined_result = generator.generate_embeddings(all_chunks_for_combined)
            
            # Save to "all" directory
            all_dir = output_dir / "all"
            all_dir.mkdir(parents=True, exist_ok=True)
            
            combined_path = all_dir / "all"
            generator.save_embeddings(combined_result, str(combined_path))
            
            type_results['all'] = {
                'path': combined_path,
                'config': combined_result['config'],
                'stats': combined_result['statistics'],
                'count': len(all_chunks_for_combined)
            }
            
            print(f"      ✓ Saved -> all/all.npy + all.json")
            print(f"        Embeddings: {combined_result['statistics'].get('count', 0)}")
            
        except Exception as e:
            print(f"      ✗ Failed to generate combined index: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*70}")
    print("EMBEDDING GENERATION COMPLETE")
    print(f"{'='*70}")

    print(f"\nConfiguration:")
    print(f"   Source: {source_type}")
    print(f"   Provider: {provider}")
    print(f"   Model: {model}")
    if type_results:
        first_result = next(iter(type_results.values()))
        print(f"   Dimension: {first_result['config']['dimension']}")

    print(f"\nGenerated Embeddings by Type:")
    total_embeddings = 0
    for chunk_type in sorted(type_results.keys()):
        result_info = type_results[chunk_type]
        embeddings_count = result_info['stats'].get('count', 0)
        total_embeddings += embeddings_count
        print(f"   {chunk_type}: {embeddings_count} embeddings")
        print(f"      Vectors: {result_info['path']}.npy ({get_size(result_info['path'].with_suffix('.npy'))})")
        print(f"      Metadata: {result_info['path']}.json ({get_size(result_info['path'].with_suffix('.json'))})")

    print(f"\n   Total embeddings: {total_embeddings}")

    if provider in ['openai', 'cohere']:
        estimate_cost(provider, model, len(prepared_chunks), type_results.get('all', {}).get('stats', {}))

    print(f"\n{'='*70}\n")
    print(f"Output structure:")
    print(f"   {output_dir}/")
    for chunk_type in sorted(type_results.keys()):
        print(f"      {chunk_type}/")
        print(f"         {chunk_type}.npy")
        print(f"         {chunk_type}.json")
    print(f"\nReady for vector DB indexing!")
    print(f"   Next: python core/VectorDB/build_indices.py\n")


if __name__ == "__main__":
    main()
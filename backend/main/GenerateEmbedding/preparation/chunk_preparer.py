from typing import List, Any, Tuple, Dict
from core.GenerateEmbedding.raw_data_extraction import convert_raw_to_chunks
from preparation.enhanced_chunk import prepare_enhanced_chunk_for_embedding




def prepare_chunks_for_embedding(chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Prepare chunks for embedding, handling raw data references."""
    prepared_chunks = []
    stats = {
        'total': len(chunks),
        'processed': 0,
        'skipped': 0,
        'raw_data_refs': 0,
        'empty_content': 0,
        'by_type': {},
        'by_priority': {}
    }
    for chunk in chunks:
        # 🔥 Intercept raw-data chunks and convert them to real chunks
        from core.GenerateEmbedding.raw_data_extraction import convert_raw_to_chunks

        if chunk.get("is_raw_data", False):
            generated = convert_raw_to_chunks(chunk)  # produce code/issue/pr/commit chunks
            # Instead of embedding the raw container, embed the generated chunks
            print(f"RAW → GENERATED: {len(generated)} new chunks from {chunk.get('source')}")

            for g in generated:
                prepared_chunks.append(prepare_enhanced_chunk_for_embedding(g))
                stats['processed'] += 1
                ctype = g.get('type', 'unknown')
                stats['by_type'][ctype] = stats['by_type'].get(ctype, 0) + 1
            stats['raw_data_refs'] += 1
            continue

        prepared = prepare_enhanced_chunk_for_embedding(chunk)
        chunk_type = prepared['type']

        # if chunk_type == "issue":
        #    print("DEBUG:", prepared["metadata"])


        stats['by_type'][chunk_type] = stats['by_type'].get(chunk_type, 0) + 1
        if prepared.get('skip_embedding'):
            stats['skipped'] += 1
            if chunk.get('is_raw_data'):
                stats['raw_data_refs'] += 1
            else:
                stats['empty_content'] += 1
            continue
        prepared_chunks.append(prepared)
        stats['processed'] += 1
        priority = prepared['metadata'].get('retrieval_priority', 3)
        stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
    return prepared_chunks, stats

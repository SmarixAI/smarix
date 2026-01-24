

from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime, timezone


def load_and_inject_aggregated_tech_summary(processed_dir: Path, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tech_file = processed_dir / "aggregated_tech_stack_summary.json"
    if not tech_file.exists():
        return chunks
    try:
        with open(tech_file, 'r', encoding='utf-8') as f:
            tech_summary = json.load(f)
    except Exception:
        return chunks
    readable = []
    if isinstance(tech_summary, dict):
        digest = tech_summary.get('digest') or tech_summary.get('summary') or None
        if digest:
            readable.append(str(digest)[:3000])
        languages = tech_summary.get('languages') or tech_summary.get('language_breakdown') or {}
        if languages:
            parts = [f"{lang}: {count}" for lang, count in (languages.items() if isinstance(languages, dict) else [])][:50]
            if parts:
                readable.append("Languages: " + ", ".join(parts[:20]))
        libs = tech_summary.get('top_libraries') or tech_summary.get('libraries') or []
        if libs and isinstance(libs, list):
            readable.append("Top libraries: " + ", ".join(libs[:20]))
        notable = {}
        for k in ['total_files', 'total_lines', 'repo_count', 'most_used_frameworks']:
            if k in tech_summary:
                notable[k] = tech_summary[k]
        if notable:
            readable.append("Notable: " + json.dumps
            (notable)[:1000])
    summarized_text = "\n\n".join(readable) if readable else json.dumps(tech_summary)[:3000]
    tech_chunk = {
        'chunk_id': f"tech_summary_{int(datetime.now(timezone.utc).timestamp())}",
        'type': 'tech_stack_summary',
        'source': 'aggregated_tech_stack_summary',
        'content': summarized_text,
        'metadata': {
            'origin_file': str(tech_file),
            'raw_summary': tech_summary
        },
        'full_chunk': {'raw': tech_summary},
        'skip_embedding': False,
    }
    return [tech_chunk] + chunks


def inject_tech_summary(processed_dir, chunks):
    """Alias for load_and_inject_aggregated_tech_summary for backward compatibility"""
    if isinstance(processed_dir, str):
        processed_dir = Path(processed_dir)
    return load_and_inject_aggregated_tech_summary(processed_dir, chunks)

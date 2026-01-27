import json
import time
from typing import Dict, Any
from datetime import datetime


def create_raw_data_reference(
    self,
    data: Dict[str, Any],
    source: str,
    repo_name: str,
    repo_owner: str,
) -> Dict[str, Any]:
    """
    Create comprehensive raw data reference for edge case fallback
    """
    data_summary = {}

    for key, value in data.items():
        if isinstance(value, list):
            data_summary[key] = {
                "count": len(value),
                "sample": value[:2] if value else [],
            }
        elif isinstance(value, dict):
            data_summary[key] = {"keys": list(value.keys())}
        else:
            data_summary[key] = str(value)[:100]

    return {
        "chunk_id": f"{repo_name}_raw_{source}_{int(time.time())}",
        "type": "raw_data_reference",
        "source": source,
        "repo_name": repo_name,
        "repo_owner": repo_owner,
        "retrieval_priority": 4,  # Lowest priority - fallback only
        "is_raw_data": True,
        "metadata": {
            "repo_name": repo_name,
            "repo_owner": repo_owner,
            "source": source,
            "data_keys": list(data.keys()),
            "summary": data_summary,
            "created_at": datetime.now().isoformat(),
            "total_size_bytes": len(json.dumps(data).encode("utf-8")),
        },
        "raw_data": data,
        "search_hints": {
            "text": json.dumps(data_summary),
            "keywords": [],
        },
    }

import re
import math
from collections import defaultdict


def tokenize_text(text: str):
    if not text:
        return []

    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)

    tokens = text.split()
    tokens = [t for t in tokens if len(t) > 2]

    return tokens


def extract_tokens_from_metadata(m: dict):
    tokens = set()

    # File path
    file_path = m.get("file_path", "")
    tokens.update(tokenize_text(file_path))

    # Content
    content = m.get("content", "")
    if isinstance(content, str):
        tokens.update(tokenize_text(content))

    # Patch (PR chunks)
    patch = m.get("patch", "")
    if isinstance(patch, str):
        tokens.update(tokenize_text(patch))

    # Search hints (code chunks)
    search_hints = m.get("search_hints", {})
    if isinstance(search_hints, dict):
        tokens.update(tokenize_text(search_hints.get("text", "")))

    return list(tokens)


def build_keyword_index(all_metadata):
    inverted_index = defaultdict(set)
    df_counter = defaultdict(int)

    total_chunks = len(all_metadata)

    for m in all_metadata:
        chunk_id = m.get("chunk_id")
        tokens = extract_tokens_from_metadata(m)

        unique_tokens = set(tokens)
        m["tokens"] = list(unique_tokens)

        for token in unique_tokens:
            inverted_index[token].add(chunk_id)
            df_counter[token] += 1

    idf_scores = {
        token: math.log((total_chunks + 1) / (df + 1))
        for token, df in df_counter.items()
    }

    inverted_index_serializable = {
        token: list(chunk_ids)
        for token, chunk_ids in inverted_index.items()
    }

    return inverted_index_serializable, idf_scores

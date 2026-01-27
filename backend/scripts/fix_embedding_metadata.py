#!/usr/bin/env python3
"""
Fix embedding metadata by extracting file_path and language from the content block
when file_path is null or empty.
"""

import re
import json
from pathlib import Path
from datetime import datetime


def extract_from_content(text: str):
    if not text:
        return None, None

    # Case 1: "file: lib/app/.."
    m = re.search(r"(?:^|\n)\s*(?:file|Path|File):\s*([^\n]+)", text, flags=re.IGNORECASE)
    if m:
        path = m.group(1).strip()
        mlang = re.search(r"(?:^|\n)\s*Language:\s*([^\n]+)", text, flags=re.IGNORECASE)
        lang = mlang.group(1).strip().lower() if mlang else None
        return path, lang

    # Case 2: JSON CODE ANALYSIS block: `"path": "lib/app/file.dart"`
    m2 = re.search(r'"path"\s*:\s*"([^"]+)"', text)
    if m2:
        path = m2.group(1).strip()
        mlang = re.search(r'"language"\s*:\s*"([^"]+)"', text)
        lang = mlang.group(1).strip().lower() if mlang else None
        return path, lang

    return None, None


def extract_text(rec):
    """Handles content stored as string OR nested under content['content'] OR raw OR text"""
    c = rec.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, dict):
        return c.get("content") or c.get("raw") or c.get("text") or ""
    return ""


def fix_file(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except:
        print(f"Skipping {path} — invalid JSON")
        return

    changed = False

    def fix_rec(rec):
        nonlocal changed
        if not isinstance(rec, dict):
            return

        target = rec  # metadata is directly stored at record level
        fp = target.get("file_path")
        lang = target.get("language")

        if fp and fp.strip():
            return

        text = extract_text(rec)
        extracted_path, extracted_lang = extract_from_content(text)

        if extracted_path:
            # Use path normalizer for consistent normalization
            from utils.path_normalizer import normalize_path, extract_filename, extract_directory
            normalized_path = normalize_path(extracted_path, '')
            if normalized_path:
                target["file_path"] = normalized_path
                target["filename"] = extract_filename(normalized_path) or ''
                target["directory"] = extract_directory(normalized_path) or ''
                changed = True

        if (not lang) and extracted_lang:
            target["language"] = extracted_lang
            changed = True

    # JSON may be list or wrap records under metadata/records/items
    if isinstance(data, list):
        for rec in data:
            fix_rec(rec)
    elif isinstance(data, dict):
        container_keys = ["metadata", "records", "items"]
        for key in container_keys:
            if key in data and isinstance(data[key], list):
                for rec in data[key]:
                    fix_rec(rec)
                break
        else:
            fix_rec(data)

    if changed:
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        backup = path.with_suffix(path.suffix + f".bak.{ts}")
        path.rename(backup)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"✔ Fixed {path} (backup saved as {backup})")
    else:
        print(f"No changes for {path}")


def main():
    base = Path(__file__).resolve().parents[1] / "data" / "Embeddings"
    if not base.exists():
        print(f"❌ Embeddings folder not found: {base}")
        return

    json_files = list(base.rglob("*.json"))
    print(f"🔍 Found {len(json_files)} JSON files")

    for jf in json_files:
        fix_file(jf)


if __name__ == "__main__":
    main()

from typing import Tuple
import re
from typing import List, Dict, Any


def _count_lines_and_functions_in_code(content: str, language_hint: str = "") -> Tuple[int, int]:
    if not content:
        return 0, 0
    lines = content.splitlines()
    non_empty_lines = [l for l in lines if l.strip() != ""]
    line_count = len(non_empty_lines)
    func_count = 0
    func_count += len(re.findall(r'^\s*def\s+\w+\s*\(', content, flags=re.MULTILINE))
    func_count += len(re.findall(r'^\s*(?:function\s+\w+|\w+\s*:\s*function\s*\(|(?:const|let|var)\s+\w+\s*=\s*\(.*?\)\s*=>)', content, flags=re.MULTILINE))
    func_count += len(re.findall(r'^\s*\w+\s*\(.*?\)\s*\{', content, flags=re.MULTILINE))
    func_count += len(re.findall(r'^\s*(?:public|private|protected|static|final|\w+)\s+\w+\s+\w+\s*\(.*?\)\s*\{', content, flags=re.MULTILINE))
    func_count += len(re.findall(r'^\s*func\s+\w+\s*\(', content, flags=re.MULTILINE))
    func_count = min(func_count, line_count)
    return line_count, func_count


def compute_repo_metrics(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    metrics = {
        'total_lines': 0,
        'total_functions': 0,
        'total_files': 0,
        'by_repo': {},
        'repo_structure': {},
        'total_chunks_by_type': {},
    }
    for chunk in chunks:
        ctype = chunk.get('type', 'unknown')
        metrics['total_chunks_by_type'][ctype] = metrics['total_chunks_by_type'].get(ctype, 0) + 1
        if ctype != 'code':
            continue
        repo = chunk.get('repo_name') or chunk.get('metadata', {}).get('repo_name') or chunk.get('source_repo') or 'unknown_repo'
        entities = chunk.get('entities', {}) or {}
        path = entities.get('path') or chunk.get('path') or 'unknown_path'
        language = entities.get('language', '') or ''
        content = None
        c = chunk.get('content')
        if isinstance(c, dict):
            content = c.get('content') or ''
        else:
            content = c or ''
        lines, funcs = _count_lines_and_functions_in_code(content, language)
        metrics['total_lines'] += lines
        metrics['total_functions'] += funcs
        metrics['total_files'] += 1
        repo_stats = metrics['by_repo'].setdefault(repo, {'lines': 0, 'functions': 0, 'files': 0, 'sample_paths': []})
        repo_stats['lines'] += lines
        repo_stats['functions'] += funcs
        repo_stats['files'] += 1
        if len(repo_stats['sample_paths']) < 10:
            repo_stats['sample_paths'].append(path)
        top = path.split('/', 1)[0] if path else ''
        repo_struct = metrics['repo_structure'].setdefault(repo, {'top_level_dirs': {}, 'files': []})
        if top:
            repo_struct['top_level_dirs'][top] = repo_struct['top_level_dirs'].get(top, 0) + 1
        if len(repo_struct['files']) < 10:
            repo_struct['files'].append(path)
    return metrics


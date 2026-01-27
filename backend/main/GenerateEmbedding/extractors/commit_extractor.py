from typing import Any, Tuple, List
from typing import Dict

def extract_commit_data(chunk: Dict[str, Any]) -> Tuple[str, List[str], Dict[str, str]]:
    commit_message = ""
    files_modified = []
    author_info = {}
    content = chunk.get('content', {})
    if isinstance(content, dict):
        commit_message = content.get('message', '')
        files_modified = content.get('files_modified', [])
    if not commit_message:
        raw_data = chunk.get('raw_data', {})
        if isinstance(raw_data, dict):
            commit_obj = raw_data.get('commit', {})
            if isinstance(commit_obj, dict):
                commit_message = commit_obj.get('message', '')
                author_data = commit_obj.get('author', {})
                if isinstance(author_data, dict):
                    author_info['name'] = author_data.get('name', '')
                    author_info['email'] = author_data.get('email', '')
                    author_info['date'] = author_data.get('date', '')
            if 'files' in raw_data and isinstance(raw_data['files'], list):
                files_modified = [
                    f.get('filename', '')
                    for f in raw_data['files']
                    if isinstance(f, dict) and f.get('filename')
                ]
    if not commit_message and not author_info:
        entities = chunk.get('entities', {})
        if isinstance(entities, dict):
            author_info['name'] = entities.get('author', '')
            author_info['sha'] = entities.get('sha', '') or entities.get('sha_short', '')
    if not commit_message:
        search_hints = chunk.get('search_hints', {})
        if isinstance(search_hints, dict):
            hint_text = search_hints.get('text', '')
            if hint_text and 'commit' in hint_text.lower():
                commit_message = hint_text[:500]
    return commit_message, files_modified, author_info

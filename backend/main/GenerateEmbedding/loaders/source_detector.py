

def detect_source_type(chunks):
    if not chunks:
        return 'unknown'
    first_chunk = chunks[0]
    source = first_chunk.get('source', None)
    if source:
        return source
    chunk_type = first_chunk.get('type', '')
    if chunk_type in ['email', 'email_attachment']:
        return 'gmail'
    elif chunk_type in ['issue', 'pr', 'commit', 'code', 'documentation']:
        return 'git'
    return 'unknown'

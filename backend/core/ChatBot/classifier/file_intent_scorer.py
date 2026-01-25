# file_lookup_scorer.py
import re
from typing import Dict
from ..query_type import QueryType


FILE_EXT_PATTERN = r'\.(py|js|ts|dart|java|go|rs|cpp|c|h|hpp|md|json|yaml|yml)'
FILE_PATH_PATTERN = r'[\w\-_/\\]+/[\w\-_/\\]+'
SNAKE_CASE_PATTERN = r'\b[a-z][a-z0-9_]{2,}\b'

FILE_INTENT_WORDS = [
    'file', 'where', 'which', 'show', 'find',
    'open', 'locate', 'path', 'implementation'
]

CLASS_NAME_PATTERN = (
    r'\b[A-Z][a-zA-Z0-9]+'
    r'(Controller|Service|Manager|Repository|Bloc|ViewModel)\b'
)


def file_lookup_scorer(query: str) -> Dict[QueryType, int]:
    """
    Scores FILE_LOOKUP intent with strong confidence.
    """
    q = query.lower()
    score = 0

    # 1️⃣ Explicit file extensions
    if re.search(FILE_EXT_PATTERN, q):
        score += 5

    # 2️⃣ File paths
    if re.search(FILE_PATH_PATTERN, q):
        score += 4

    # 3️⃣ Explicit 'file' intent words
    if 'file' in q and any(w in q for w in FILE_INTENT_WORDS):
        score += 4

    # 4️⃣ PascalCase class names (Controller, Service, etc.)
    if re.search(CLASS_NAME_PATTERN, query):
        score += 4

    # 5️⃣ Snake_case identifiers commonly used as filenames
    if 'file' in q and re.search(SNAKE_CASE_PATTERN, q):
        score += 3

    if score > 0:
        return {QueryType.FILE_LOOKUP: score}

    return {}

import os

def auto_detect_provider():
    if os.getenv("OPENAI_API_KEY"):
        return "openai", "text-embedding-3-small"
    if os.getenv("COHERE_API_KEY"):
        return "cohere", "embed-english-v3.0"
    return "sentence-transformers", "all-MiniLM-L6-v2"

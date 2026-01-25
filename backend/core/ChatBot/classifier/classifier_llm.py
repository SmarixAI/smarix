from ..query_type import QueryType

def llm_classify_query(query: str) -> QueryType:
    """
    Thin wrapper over your existing LLM classification logic
    """
    # reuse your existing LLM logic here
    # must return QueryType
    raise NotImplementedError

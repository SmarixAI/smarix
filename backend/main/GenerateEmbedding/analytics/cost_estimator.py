

def estimate_cost(provider: str, model: str, num_chunks: int, stats: dict):
    avg_tokens_per_chunk = 800
    total_tokens = num_chunks * avg_tokens_per_chunk
    costs = {
        'openai': {
            'text-embedding-3-small': 0.02 / 1_000_000,
            'text-embedding-3-large': 0.13 / 1_000_000,
            'text-embedding-ada-002': 0.10 / 1_000_000
        },
        'cohere': {
            'embed-english-v3.0': 0.10 / 1_000_000,
            'embed-multilingual-v3.0': 0.10 / 1_000_000
        }
    }
    cost_per_token = costs.get(provider, {}).get(model, 0)
    estimated_cost = total_tokens * cost_per_token
    if estimated_cost > 0:
        print(f"\nEstimated Cost:")
        print(f"   Tokens: ~{total_tokens:,}")
        print(f"   Cost: ~${estimated_cost:.3f}")

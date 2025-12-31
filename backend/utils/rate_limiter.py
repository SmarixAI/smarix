# Compatibility shim to preserve existing imports like `from utils.rate_limiter import RateLimiter`
# Delegates implementation to backend/utils/DataCollection/rate_limiter.py
from .DataCollection.rate_limiter import *


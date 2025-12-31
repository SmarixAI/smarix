import time
import requests
from config.DataCollection.settings import Config

class RateLimiter:
    """Handles API rate limiting"""
    
    def __init__(self):
        self.config = Config()
    
    def handle_rate_limit(self, response: requests.Response) -> None:
        """Handle rate limit exceeded response"""
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        wait_time = max(reset_time - int(time.time()), self.config.RATE_LIMIT_RETRY_DELAY)
        print(f"⏳ Rate limit hit. Waiting {wait_time} seconds...")
        time.sleep(wait_time)
    
    def apply_delay(self) -> None:
        """Apply standard delay between requests"""
        time.sleep(self.config.API_DELAY)

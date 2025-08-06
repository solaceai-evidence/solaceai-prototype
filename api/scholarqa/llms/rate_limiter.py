import threading
import time
import logging

logger = logging.getLogger(__name__)

# This class manages request and token limits to avoid exceeding LLM rate limits.
class RateLimiter:
    """
    General rate limiter for LLM APIs with configurable limits per model.
    Supports separate limits for requests, input tokens, and output tokens.
    """
    
    def __init__(self, max_requests_per_minute: int, max_input_tokens_per_minute: int, max_output_tokens_per_minute: int, max_workers: int = 3):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_input_tokens_per_minute = max_input_tokens_per_minute
        self.max_output_tokens_per_minute = max_output_tokens_per_minute
        self.max_workers = max_workers

        # Initialize tracking for requests and token usage over time
        self.request_times = []
        self.token_usage = [] # List of (timestamp, token_counf) tuples for input TPM
        
        #Thead-safe lock to manage concurrent access
        self.lock = threading.Lock()
        
        logger.info(f"Rate limiter initialized: {self.max_requests_per_minute} req/min, "   
                f"{self.max_input_tokens_per_minute} input tokens/min, "
                f"{self.max_output_tokens_per_minute} output tokens/min")
    
    # TODO: Implement token-based limits if needed
    # TODO: Implement max_workers limit if needed
    def acquire(self):
        """
        Acquire permission to make one API request.
        Blocks if rate limit would be exceeded.
        Cleans up old requests older than 60 seconds.
        """
        with self.lock:
            current_time = time.time()
            
            # Remove requests older than 60 seconds
            cutoff_time = current_time - 60
            self.request_times = [t for t in self.request_times if t > cutoff_time]
            
            # Check if we're at the limit
            if len(self.request_times) >= self.max_requests_per_minute:
                # Calculate wait time until oldest request expires
                wait_time = self.request_times[0] + 60 - current_time
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
                    # Clean up again after waiting
                    current_time = time.time()
                    cutoff_time = current_time - 60
                    self.request_times = [t for t in self.request_times if t > cutoff_time]
            
            # Record this request
            self.request_times.append(current_time)
            logger.debug(f"Request acquired. Current usage: {len(self.request_times)}/{self.max_requests_per_minute}")
    
    def get_current_usage(self):
        """Get current usage statistics"""
        current_time = time.time()
        cutoff_time = current_time - 60
        active_requests = [t for t in self.request_times if t > cutoff_time]
        
        return {
            "requests_used": len(active_requests),
            "requests_limit": self.max_requests_per_minute,
            "usage_percentage": (len(active_requests) / self.max_requests_per_minute) * 100
        }    
import threading
import time
import logging

from contextlib import contextmanager

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
        
        # Track active workers
        self.active_workers = 0
        self.worker_condition = threading.Condition()
        
        #Thead-safe lock to manage concurrent access
        self.lock = threading.Lock()
        
        logger.info(f"Rate limiter initialized: {self.max_requests_per_minute} req/min, "   
                f"{self.max_input_tokens_per_minute} input tokens/min, "
                f"{self.max_output_tokens_per_minute} output tokens/min" 
                f", {self.max_workers} max workers")
    

    def acquire(self):
        """
        Acquire permission to make one API request.
        Blocks if rate limit or max workers limit would be exceeded.
        Cleans up old requests older than 60 seconds.
        """
        
        # First check worker limit
        with self.worker_condition:
            while self.active_workers >= self.max_workers:
                logger.info(f"Max workers reached ({self.active_workers}/{self.max_workers}), waiting...")
                self.worker_condition.wait()
                
            # max workers not reached: Reserve a worker slot
            self.active_workers += 1
            logger.debug(f"Worker acquired. Active workers: {self.active_workers}/{self.max_workers}")
        
        # Now check rate limits       
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
    
    def release(self):
        """
        Release a worker slot after request completion.
        Should be called when request is done (success or failure).
        """
        with self.worker_condition:
            self.active_workers -= 1
            logger.debug(f"Worker released. Active workers: {self.active_workers}/{self.max_workers}")
            # Wake up one waiting thread
            self.worker_condition.notify()
    
            
    @contextmanager
    def request_context(self):
        """
        Context manager for rate-limited requests.
        Automatically acquires and releases resources.
        """
        try:
            self.acquire()
            yield
        finally:
            self.release()
    
        
    def get_current_usage(self):
        """Get current usage statistics"""
        current_time = time.time()
        cutoff_time = current_time - 60
        active_requests = [t for t in self.request_times if t > cutoff_time]
        
        return {
            "requests_used": len(active_requests),
            "requests_limit": self.max_requests_per_minute,
            "requests_usage_percentage": (len(active_requests) / self.max_requests_per_minute) * 100,
            "active_workers": self.active_workers,
            "max_workers": self.max_workers,
            "workers_usage_percentage": (self.active_workers / self.max_workers) * 100 if self.max_workers > 0 else 0
        }    
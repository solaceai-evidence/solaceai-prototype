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
        self.input_token_usage = []  # List of (timestamp, input_tokens) tuples for input TPM
        self.output_token_usage = [] # List of (timestamp, output_tokens) tuples for output TPM
        
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
        
        # Optimization: Skip worker management for single worker
        if self.max_workers > 1:
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
        # Optimization: Skip worker management for single worker
        if self.max_workers > 1:
            with self.worker_condition:
                self.active_workers -= 1
                logger.debug(f"Worker released. Active workers: {self.active_workers}/{self.max_workers}")
                # Wake up one waiting thread
                self.worker_condition.notify()
    
            
    def record_token_usage(self, input_tokens: int, output_tokens: int):
        """
        Record actual token usage after an API call.
        This should be called after each completion to track token consumption.
        """
        current_time = time.time()
        
        with self.lock:
            self.input_token_usage.append((current_time, input_tokens))
            self.output_token_usage.append((current_time, output_tokens))
            
            # Clean up old token usage (older than 60 seconds)
            cutoff_time = current_time - 60
            self.input_token_usage = [(t, tokens) for t, tokens in self.input_token_usage if t > cutoff_time]
            self.output_token_usage = [(t, tokens) for t, tokens in self.output_token_usage if t > cutoff_time]
            
            logger.debug(f"Recorded token usage: {input_tokens} input, {output_tokens} output")

    def check_token_limits(self, estimated_input_tokens: int, estimated_output_tokens: int = 0) -> bool:
        """
        Check if the proposed token usage would exceed limits.
        Returns True if within limits, False if would exceed.
        """
        current_time = time.time()
        cutoff_time = current_time - 60
        
        with self.lock:
            # Calculate current token usage in the last minute
            current_input_tokens = sum(tokens for t, tokens in self.input_token_usage if t > cutoff_time)
            current_output_tokens = sum(tokens for t, tokens in self.output_token_usage if t > cutoff_time)
            
            # Check if adding estimated tokens would exceed limits
            projected_input = current_input_tokens + estimated_input_tokens
            projected_output = current_output_tokens + estimated_output_tokens
            
            input_ok = projected_input <= self.max_input_tokens_per_minute
            output_ok = projected_output <= self.max_output_tokens_per_minute
            
            if not input_ok:
                logger.warning(f"Input token limit would be exceeded: {projected_input}/{self.max_input_tokens_per_minute}")
            if not output_ok:
                logger.warning(f"Output token limit would be exceeded: {projected_output}/{self.max_output_tokens_per_minute}")
                
            return input_ok and output_ok

    @contextmanager
    def request_context(self, estimated_input_tokens: int = 0, estimated_output_tokens: int = 0):
        """
        Context manager for rate-limited requests with token estimation.
        Automatically acquires and releases resources, and optionally checks token limits.
        """
        try:
            self.acquire()
            
            # Optional: Check token limits before proceeding if estimates provided
            if estimated_input_tokens > 0 or estimated_output_tokens > 0:
                if not self.check_token_limits(estimated_input_tokens, estimated_output_tokens):
                    logger.warning("Proceeding despite token limit concerns (rate limiter continues with request limiting)")
            
            yield self  # Yield the rate limiter instance so caller can call record_token_usage()
        finally:
            self.release()
    
        
    def get_current_usage(self):
        """Get current usage statistics"""
        current_time = time.time()
        cutoff_time = current_time - 60
        active_requests = [t for t in self.request_times if t > cutoff_time]
        
        # Calculate current token usage
        current_input_tokens = sum(tokens for t, tokens in self.input_token_usage if t > cutoff_time)
        current_output_tokens = sum(tokens for t, tokens in self.output_token_usage if t > cutoff_time)
        
        return {
            "requests_used": len(active_requests),
            "requests_limit": self.max_requests_per_minute,
            "requests_usage_percentage": (len(active_requests) / self.max_requests_per_minute) * 100,
            "input_tokens_used": current_input_tokens,
            "input_tokens_limit": self.max_input_tokens_per_minute,
            "input_tokens_usage_percentage": (current_input_tokens / self.max_input_tokens_per_minute) * 100,
            "output_tokens_used": current_output_tokens,
            "output_tokens_limit": self.max_output_tokens_per_minute,
            "output_tokens_usage_percentage": (current_output_tokens / self.max_output_tokens_per_minute) * 100,
            "active_workers": self.active_workers,
            "max_workers": self.max_workers,
            "workers_usage_percentage": (self.active_workers / self.max_workers) * 100 if self.max_workers > 0 else 0
        }    
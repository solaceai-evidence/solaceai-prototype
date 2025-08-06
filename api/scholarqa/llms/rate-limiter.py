import asyncio
import time
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Rate limiter for Anthropic API 
# This class manages request and token limits to avoid exceeding Anthropic's rate limits.
# TODO: Adapt for other LLM providers as needed
class AnthropicRateLimiter:
    def __init__(self, max_requests_per_minute: int = 45, max_tokens_per_minute: int = 25000):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_tokens_per_minute = max_tokens_per_minute
        self.request_times = []
        self.token_usage = []
        self.lock = asyncio.Lock()
    
    # Asynchronously acquire a token for a request
    # estimated_tokens: Estimated number of tokens for this request
    # Returns: None if successful, raises an exception if rate limit exceeded
    async def acquire(self, estimated_tokens: int = 1000):
        # Acquire a token for a request, respecting the rate limits
        async with self.lock:
            current_time = time.time()
            
            # Clean older than 1 minute requests and token usage
            cutoff_time = current_time - 60
            self.request_times = [t for t in self.request_times if t > cutoff_time]
            self.token_usage = [(t, tokens) for t, tokens in self.token_usage if t > cutoff_time]
            
            # Check if we need to wait
            if len(self.request_times) >= self.requests_per_minute:
                wait_time = 60 - (current_time - self.request_times[0])
                if wait_time > 0:
                    logger.info(f"Rate limit: waiting {wait_time:.1f}s for request limit")
                    await asyncio.sleep(wait_time)
            
            # Check token usage for limits. Wait if necessary
            current_tokens = sum(tokens for _, tokens in self.token_usage)
            if current_tokens + estimated_tokens > self.tokens_per_minute:
                wait_time = 60 - (current_time - self.token_usage[0][0])
                if wait_time > 0:
                    logger.info(f"Rate limit: waiting {wait_time:.1f}s for token limit")
                    await asyncio.sleep(wait_time)
            
            # Record this request and token usage
            self.request_times.append(current_time)
            self.token_usage.append((current_time, estimated_tokens))
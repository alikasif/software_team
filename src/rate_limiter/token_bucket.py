"""TokenBucket class implementation."""
import threading
import time


class TokenBucket:
    """Thread-safe token bucket rate limiter.
    
    Implements the token bucket algorithm for rate limiting.
    Tokens are added at a constant rate (tokens_per_second).
    Up to `capacity` tokens can be stored.
    """
    
    def __init__(self, capacity: float, tokens_per_second: float):
        """Initialize the token bucket.
        
        Args:
            capacity: Maximum number of tokens that can be stored.
            tokens_per_second: Rate at which tokens are added to the bucket.
        """
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if tokens_per_second <= 0:
            raise ValueError("tokens_per_second must be positive")
        
        self._capacity = capacity
        self._tokens_per_second = tokens_per_second
        self._tokens = capacity  # Start with full bucket
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time since last refill.
        
        This method should only be called while holding the lock.
        """
        now = time.monotonic()
        elapsed = now - self._last_refill
        tokens_to_add = elapsed * self._tokens_per_second
        self._tokens = min(self._capacity, self._tokens + tokens_to_add)
        self._last_refill = now
    
    def allow(self, tokens: float = 1) -> bool:
        """Check if tokens are available and consume them if so.
        
        This method does not block. Returns immediately.
        
        Args:
            tokens: Number of tokens to consume. Defaults to 1.
            
        Returns:
            True if tokens were consumed, False otherwise.
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
    
    def try_consume(self, tokens: float = 1) -> bool:
        """Alias for allow(). Try to consume tokens without blocking.
        
        Args:
            tokens: Number of tokens to consume. Defaults to 1.
            
        Returns:
            True if tokens were consumed, False otherwise.
        """
        return self.allow(tokens)
    
    def wait(self, tokens: float = 1) -> None:
        """Block until tokens are available, then consume them.
        
        This method blocks the calling thread until the specified
        number of tokens are available.
        
        Args:
            tokens: Number of tokens to consume. Defaults to 1.
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        
        while True:
            if self.allow(tokens):
                return
            # Sleep briefly to avoid busy-waiting
            time.sleep(0.001)

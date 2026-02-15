"""Unit tests for TokenBucket rate limiter."""
import pytest
import time
from src.rate_limiter.token_bucket import TokenBucket


class TestTokenBucketInitialization:
    """Test TokenBucket initialization."""
    
    def test_init_valid_parameters(self):
        """Test initialization with valid parameters."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        assert tb._capacity == 10
        assert tb._tokens_per_second == 5
        assert tb._tokens == 10  # Should start with full bucket
    
    def test_init_with_float_capacity(self):
        """Test initialization with float capacity."""
        tb = TokenBucket(capacity=5.5, tokens_per_second=2.5)
        assert tb._capacity == 5.5
        assert abs(tb._tokens - 5.5) < 0.001
    
    def test_init_with_high_rate(self):
        """Test initialization with high refill rate."""
        tb = TokenBucket(capacity=1000, tokens_per_second=1000)
        assert tb._capacity == 1000
        assert tb._tokens_per_second == 1000
    
    def test_init_with_low_rate(self):
        """Test initialization with very low refill rate."""
        tb = TokenBucket(capacity=1, tokens_per_second=0.001)
        assert tb._capacity == 1
        assert tb._tokens_per_second == 0.001
    
    def test_init_zero_capacity_raises_error(self):
        """Test that zero capacity raises ValueError."""
        with pytest.raises(ValueError, match="capacity must be positive"):
            TokenBucket(capacity=0, tokens_per_second=5)
    
    def test_init_negative_capacity_raises_error(self):
        """Test that negative capacity raises ValueError."""
        with pytest.raises(ValueError, match="capacity must be positive"):
            TokenBucket(capacity=-5, tokens_per_second=5)
    
    def test_init_zero_rate_raises_error(self):
        """Test that zero rate raises ValueError."""
        with pytest.raises(ValueError, match="tokens_per_second must be positive"):
            TokenBucket(capacity=10, tokens_per_second=0)
    
    def test_init_negative_rate_raises_error(self):
        """Test that negative rate raises ValueError."""
        with pytest.raises(ValueError, match="tokens_per_second must be positive"):
            TokenBucket(capacity=10, tokens_per_second=-5)


class TestTokenBucketAllow:
    """Test TokenBucket.allow() method."""
    
    def test_allow_single_token_success(self):
        """Test allowing a single token when available."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        assert tb.allow() is True
        assert abs(tb._tokens - 9) < 0.001
    
    def test_allow_single_token_failure(self):
        """Test denying token when none available."""
        tb = TokenBucket(capacity=1, tokens_per_second=1)
        tb.allow()  # Consume the only token
        assert tb.allow() is False  # Should fail immediately
    
    def test_allow_multiple_tokens_success(self):
        """Test consuming multiple tokens at once."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        assert tb.allow(5) is True
        assert abs(tb._tokens - 5) < 0.001
    
    def test_allow_multiple_tokens_failure(self):
        """Test denying multiple tokens when insufficient."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        assert tb.allow(15) is False
        assert abs(tb._tokens - 10) < 0.001  # Tokens unchanged
    
    def test_allow_partial_consumption(self):
        """Test error when requesting more than available."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        tb.allow(8)
        assert tb.allow(5) is False
        assert abs(tb._tokens - 2) < 0.001
    
    def test_allow_zero_tokens_raises_error(self):
        """Test that requesting zero tokens raises ValueError."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        with pytest.raises(ValueError, match="tokens must be positive"):
            tb.allow(0)
    
    def test_allow_negative_tokens_raises_error(self):
        """Test that requesting negative tokens raises ValueError."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        with pytest.raises(ValueError, match="tokens must be positive"):
            tb.allow(-5)
    
    def test_allow_float_tokens(self):
        """Test consuming fractional tokens."""
        tb = TokenBucket(capacity=10.5, tokens_per_second=5)
        assert tb.allow(0.5) is True
        assert abs(tb._tokens - 10) < 0.001
    
    def test_allow_exact_capacity(self):
        """Test consuming exactly the capacity."""
        tb = TokenBucket(capacity=5, tokens_per_second=2)
        assert tb.allow(5) is True
        assert abs(tb._tokens - 0) < 0.001


class TestTokenBucketWait:
    """Test TokenBucket.wait() method."""
    
    def test_wait_immediate_success(self):
        """Test wait() returns immediately when tokens available."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        start = time.monotonic()
        tb.wait(5)
        end = time.monotonic()
        assert (end - start) < 0.05  # Should be nearly instant
        assert abs(tb._tokens - 5) < 0.001
    
    def test_wait_blocks_until_available(self):
        """Test wait() blocks until tokens are available."""
        tb = TokenBucket(capacity=1, tokens_per_second=10)
        tb.allow()  # Consume the only token
        start = time.monotonic()
        tb.wait(1)
        end = time.monotonic()
        elapsed = end - start
        # Should take roughly 0.1 seconds to get 1 token at 10 tokens/sec
        assert 0.05 < elapsed < 0.25, f"Expected ~0.1s, got {elapsed}s"
    
    def test_wait_multiple_tokens(self):
        """Test wait() for multiple tokens."""
        tb = TokenBucket(capacity=1, tokens_per_second=20)
        tb.allow()  # Consume the only token
        start = time.monotonic()
        tb.wait(4)
        end = time.monotonic()
        elapsed = end - start
        # Should take roughly 0.2 seconds to get 4 tokens at 20 tokens/sec
        assert 0.1 < elapsed < 0.35, f"Expected ~0.2s, got {elapsed}s"
    
    def test_wait_zero_tokens_raises_error(self):
        """Test that wait(0) raises ValueError."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        with pytest.raises(ValueError, match="tokens must be positive"):
            tb.wait(0)
    
    def test_wait_negative_tokens_raises_error(self):
        """Test that wait(-1) raises ValueError."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        with pytest.raises(ValueError, match="tokens must be positive"):
            tb.wait(-1)
    
    def test_wait_consumes_tokens(self):
        """Test that wait() actually consumes tokens."""
        tb = TokenBucket(capacity=5, tokens_per_second=10)
        tb.wait(3)
        assert abs(tb._tokens - 2) < 0.001


class TestTokenRefill:
    """Test token refill mechanism."""
    
    def test_refill_over_time(self):
        """Test that tokens refill over time."""
        tb = TokenBucket(capacity=10, tokens_per_second=10)
        tb.allow(10)  # Consume all tokens
        assert abs(tb._tokens - 0) < 0.001
        
        time.sleep(0.15)
        # After 0.15s at 10 tokens/sec, should have ~1.5 tokens
        tb.allow()  # Trigger refill
        assert 0.4 < tb._tokens < 2, f"Expected ~1.5 tokens, got {tb._tokens}"
    
    def test_refill_clamped_at_capacity(self):
        """Test that refilled tokens don't exceed capacity."""
        tb = TokenBucket(capacity=5, tokens_per_second=100)
        assert abs(tb._tokens - 5) < 0.001  # Start full
        
        # Even with time passing, should not exceed capacity
        time.sleep(0.1)
        tb.allow()  # Trigger refill
        assert abs(tb._tokens - 5) < 0.001
    
    def test_refill_accumulates_correctly(self):
        """Test that refill accumulates at correct rate."""
        tb = TokenBucket(capacity=100, tokens_per_second=50)
        tb.allow(100)  # Empty bucket
        
        time.sleep(0.2)
        tb.allow()  # Trigger refill
        # After 0.2s at 50 tokens/sec, should have ~10 tokens
        assert 8 < tb._tokens < 12, f"Expected ~10 tokens, got {tb._tokens}"
    
    def test_refill_precision(self):
        """Test floating point precision in refill."""
        tb = TokenBucket(capacity=1000, tokens_per_second=33.33)
        tb.allow(1000)  # Empty bucket
        
        time.sleep(0.1)
        tb.allow()  # Trigger refill
        # After 0.1s at 33.33 tokens/sec, should have ~3.333 tokens
        assert 2.5 < tb._tokens < 4, f"Expected ~3.33 tokens, got {tb._tokens}"


class TestCapacityClamping:
    """Test capacity clamping."""
    
    def test_capacity_clamping_after_refill(self):
        """Test tokens are clamped at capacity after refill."""
        tb = TokenBucket(capacity=10, tokens_per_second=100)
        tb.allow(5)  # Consume 5, leaving 5
        
        time.sleep(0.2)
        tb.allow()  # Trigger refill
        # Even though we could add 20 tokens, should be clamped at 10
        assert abs(tb._tokens - 10) < 0.001
    
    def test_refill_maintains_capacity_invariant(self):
        """Test that tokens never exceed capacity."""
        tb = TokenBucket(capacity=7, tokens_per_second=1000)
        for _ in range(5):
            tb.allow()
            time.sleep(0.01)
        assert tb._tokens <= tb._capacity + 0.001


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_very_small_capacity(self):
        """Test very small capacity."""
        tb = TokenBucket(capacity=0.001, tokens_per_second=0.001)
        assert tb.allow(0.0005) is True
    
    def test_very_large_capacity(self):
        """Test very large capacity."""
        tb = TokenBucket(capacity=1000000, tokens_per_second=100000)
        assert tb.allow(500000) is True
    
    def test_rapid_allow_calls(self):
        """Test rapid consecutive allow() calls."""
        tb = TokenBucket(capacity=100, tokens_per_second=10)
        for _ in range(50):
            result = tb.allow(1)
            if not result:
                break
        assert tb._tokens >= 0
    
    def test_precision_with_fractional_tokens(self):
        """Test precision with fractional token amounts."""
        tb = TokenBucket(capacity=10, tokens_per_second=1)
        for _ in range(100):
            tb.allow(0.01)
        assert abs(tb._tokens - 9) < 0.001
    
    def test_many_sequential_operations(self):
        """Test many sequential operations maintain invariants."""
        tb = TokenBucket(capacity=50, tokens_per_second=10)
        for _ in range(100):
            tb.allow()
            assert tb._tokens <= tb._capacity + 0.001
            assert tb._tokens >= -0.001
    
    def test_capacity_never_negative(self):
        """Test tokens never go negative."""
        tb = TokenBucket(capacity=1, tokens_per_second=1)
        for _ in range(100):
            tb.allow(1)
        assert tb._tokens >= -0.001


class TestTryConsume:
    """Test try_consume alias for allow."""
    
    def test_try_consume_alias(self):
        """Test that try_consume is an alias for allow."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        result1 = tb.try_consume(3)
        assert result1 is True
        assert abs(tb._tokens - 7) < 0.001
    
    def test_try_consume_failure(self):
        """Test try_consume failure returns False."""
        tb = TokenBucket(capacity=2, tokens_per_second=1)
        tb.try_consume(2)
        result = tb.try_consume(3)
        assert result is False


class TestThreadSafety:
    """Test thread-safety basics (comprehensive threading tests in test_concurrency.py)."""
    
    def test_lock_exists(self):
        """Test that internal lock exists."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        assert hasattr(tb, '_lock')
        assert tb._lock is not None
    
    def test_concurrent_reads_safe(self):
        """Test that concurrent reads are safe."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        # Multiple threads reading tokens at same time
        results = []
        
        def read_tokens():
            time.sleep(0.001)  # Ensure overlapping access
            results.append(tb._tokens)
        
        import threading
        threads = [threading.Thread(target=read_tokens) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All reads should return valid values
        assert all(r >= 0 for r in results)


class TestFloatingPointPrecision:
    """Test floating point precision handling."""
    
    def test_precision_after_many_refills(self):
        """Test precision doesn't degrade over many refills."""
        tb = TokenBucket(capacity=100, tokens_per_second=0.1)
        initial_tokens = tb._tokens
        
        for _ in range(10):
            time.sleep(0.01)
            tb.allow()  # Trigger refill
        
        # Should still be close to initial (haven't consumed much)
        assert abs(tb._tokens - initial_tokens) < 1
    
    def test_fractional_token_precision(self):
        """Test precision with very small fractional tokens."""
        tb = TokenBucket(capacity=1, tokens_per_second=1)
        tb.allow(0.333)
        tb.allow(0.333)
        tb.allow(0.333)
        # After consuming 0.999, should have ~0.001 tokens left
        assert 0.0 <= tb._tokens < 0.01

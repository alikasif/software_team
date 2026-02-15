"""Edge case and performance tests for TokenBucket rate limiter."""
import pytest
import time
from src.rate_limiter.token_bucket import TokenBucket


class TestExtremeRates:
    """Test token bucket with extreme rate values."""
    
    def test_very_high_rate(self):
        """Test with very high refill rate."""
        tb = TokenBucket(capacity=1000, tokens_per_second=100000)
        tb.allow(1000)
        assert tb._tokens >= -0.001
        
        time.sleep(0.001)
        tb.allow()  # Trigger refill
        # Should have many tokens after refill
        assert tb._tokens > 90
    
    def test_very_low_rate(self):
        """Test with very low refill rate."""
        tb = TokenBucket(capacity=10, tokens_per_second=0.01)
        tb.allow(10)
        
        time.sleep(0.1)
        tb.allow()  # Trigger refill
        # Should have ~0.001 tokens after 0.1s at 0.01 rate
        # Actually at 0.01 tokens_per_second, after 0.1s we get 0.001 tokens
        assert tb._tokens < 1  # Very little refill
    
    def test_very_high_capacity(self):
        """Test with very high capacity."""
        tb = TokenBucket(capacity=1000000, tokens_per_second=100000)
        assert tb.allow(999999) is True
        assert tb._tokens > 0
    
    def test_very_low_capacity(self):
        """Test with very low capacity."""
        tb = TokenBucket(capacity=0.001, tokens_per_second=0.001)
        assert tb.allow(0.0005) is True
    
    def test_high_rate_high_capacity(self):
        """Test with both rate and capacity very high."""
        tb = TokenBucket(capacity=1000000, tokens_per_second=1000000)
        for _ in range(100):
            tb.allow(10000)
        assert tb._tokens >= -0.001
    
    def test_low_rate_low_capacity(self):
        """Test with both rate and capacity very low."""
        tb = TokenBucket(capacity=0.1, tokens_per_second=0.1)
        assert tb.allow(0.05) is True
        assert tb.allow(0.05) is True
        assert tb.allow(0.05) is False


class TestLargeTokenConsumption:
    """Test consuming large amounts of tokens."""
    
    def test_consume_full_capacity_at_once(self):
        """Test consuming the entire capacity at once."""
        tb = TokenBucket(capacity=1000, tokens_per_second=100)
        assert tb.allow(1000) is True
        assert abs(tb._tokens) < 0.001
    
    def test_consume_more_than_capacity(self):
        """Test trying to consume more than capacity."""
        tb = TokenBucket(capacity=100, tokens_per_second=10)
        assert tb.allow(101) is False
        assert abs(tb._tokens - 100) < 0.001
    
    def test_consume_large_fractional_amount(self):
        """Test consuming large fractional amounts."""
        tb = TokenBucket(capacity=1000, tokens_per_second=100)
        assert tb.allow(999.999) is True
        assert tb._tokens < 1
    
    def test_consume_just_over_capacity(self):
        """Test consuming just slightly more than available."""
        tb = TokenBucket(capacity=100, tokens_per_second=10)
        assert tb.allow(100) is True
        assert tb.allow(0.01) is False
    
    def test_many_large_consumptions(self):
        """Test many large consumption operations."""
        tb = TokenBucket(capacity=1000, tokens_per_second=1000)
        for i in range(10):
            result = tb.allow(99)
            # First one should succeed, rest may fail if tokens run out
            if i == 0:
                assert result is True
        assert tb._tokens >= -0.001


class TestNegativeRequestHandling:
    """Test handling of negative token requests."""
    
    def test_negative_allow_raises_error(self):
        """Test that negative token request to allow() raises error."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        with pytest.raises(ValueError, match="tokens must be positive"):
            tb.allow(-1)
    
    def test_negative_wait_raises_error(self):
        """Test that negative token request to wait() raises error."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        with pytest.raises(ValueError, match="tokens must be positive"):
            tb.wait(-1)
    
    def test_very_small_negative_allow(self):
        """Test with very small negative value."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        with pytest.raises(ValueError):
            tb.allow(-0.001)
    
    def test_large_negative_allow(self):
        """Test with large negative value."""
        tb = TokenBucket(capacity=10, tokens_per_second=5)
        with pytest.raises(ValueError):
            tb.allow(-1000)


class TestZeroAndNearZeroEdges:
    """Test edge cases with zero and near-zero values."""
    
    def test_zero_rate_initialization_fails(self):
        """Test that zero rate is rejected."""
        with pytest.raises(ValueError, match="tokens_per_second must be positive"):
            TokenBucket(capacity=10, tokens_per_second=0)
    
    def test_zero_capacity_initialization_fails(self):
        """Test that zero capacity is rejected."""
        with pytest.raises(ValueError, match="capacity must be positive"):
            TokenBucket(capacity=0, tokens_per_second=10)
    
    def test_near_zero_positive_rate(self):
        """Test with near-zero positive rate."""
        tb = TokenBucket(capacity=1, tokens_per_second=0.00001)
        assert tb._tokens_per_second == 0.00001
        tb.allow(1)
    
    def test_near_zero_positive_capacity(self):
        """Test with near-zero positive capacity."""
        tb = TokenBucket(capacity=0.00001, tokens_per_second=0.00001)
        assert tb._capacity == 0.00001
    
    def test_very_small_positive_allow(self):
        """Test allowing very small positive token amounts."""
        tb = TokenBucket(capacity=1, tokens_per_second=1)
        assert tb.allow(0.0000001) is True


class TestPerformanceBenchmark:
    """Performance benchmark tests."""
    
    def test_benchmark_10k_allow_calls(self):
        """Benchmark: time 10,000 allow() calls."""
        tb = TokenBucket(capacity=100000, tokens_per_second=100000)
        
        start = time.monotonic()
        for _ in range(10000):
            tb.allow(1)
        elapsed = time.monotonic() - start
        
        # Should complete in reasonable time (< 1 second for 10k calls)
        assert elapsed < 1.0, f"10k allow() calls took {elapsed}s"
        # Average time per call should be < 0.1ms
        avg_time = elapsed / 10000
        assert avg_time < 0.0001, f"Average call time: {avg_time*1000}ms"
    
    def test_benchmark_10k_failed_allow_calls(self):
        """Benchmark: 10,000 failed allow() calls."""
        tb = TokenBucket(capacity=1, tokens_per_second=1)
        tb.allow(1)  # Consume the only token
        
        start = time.monotonic()
        for _ in range(10000):
            tb.allow(100)  # Will always fail
        elapsed = time.monotonic() - start
        
        # Failed calls should also be fast
        assert elapsed < 0.5, f"10k failed allow() calls took {elapsed}s"
    
    def test_benchmark_5k_allow_with_refill(self):
        """Benchmark: 5,000 allow() calls with refill happening."""
        tb = TokenBucket(capacity=10000, tokens_per_second=10000)
        
        start = time.monotonic()
        for _ in range(5000):
            tb.allow(1)
            time.sleep(0.0001)  # Simulate some work
        elapsed = time.monotonic() - start
        
        # Should reasonably complete (includes ~0.5s of sleep from 5000 * 0.0001)
        assert elapsed < 3.0
    
    def test_benchmark_2k_wait_calls(self):
        """Benchmark: time 2,000 wait() calls with available tokens."""
        tb = TokenBucket(capacity=10000, tokens_per_second=10000)
        
        start = time.monotonic()
        for _ in range(2000):
            tb.wait(1)
        elapsed = time.monotonic() - start
        
        # With abundant tokens, wait should be fast
        assert elapsed < 0.5, f"2k wait() calls took {elapsed}s"


class TestComplexSequences:
    """Test complex sequences of operations."""
    
    def test_alternating_allow_and_wait(self):
        """Test alternating allow() and wait() calls."""
        tb = TokenBucket(capacity=100, tokens_per_second=100)
        
        for i in range(50):
            if i % 2 == 0:
                result = tb.allow(1)
                # Should eventually get some denials
            else:
                tb.wait(0.5)
        
        assert tb._tokens >= -0.001
    
    def test_burst_then_drain(self):
        """Test burst consumption then gradual drain."""
        tb = TokenBucket(capacity=100, tokens_per_second=10)
        
        # Burst: consume everything
        tb.allow(100)
        assert abs(tb._tokens) < 0.001
        
        # Drain: wait for tokens to come back
        for _ in range(50):
            tb.wait(0.1)
        
        # Should have consumed ~5 tokens (50 * 0.1)
        assert tb._tokens < 5
    
    def test_fractional_token_accumulation(self):
        """Test that fractional tokens accumulate correctly."""
        tb = TokenBucket(capacity=100, tokens_per_second=100)
        
        # Consume in small fractions
        for _ in range(1000):
            tb.allow(0.01)
        
        # Account for tokens refilling during loop (100 tokens/sec at ~10ms = ~1 token)
        assert tb._tokens > 80
    
    def test_mixed_amounts_sequence(self):
        """Test sequence with varying token amounts."""
        tb = TokenBucket(capacity=100, tokens_per_second=50)
        
        amounts = [1, 5, 0.5, 10, 2.5, 20, 1.5, 3, 0.1, 5]
        for amount in amounts:
            result = tb.allow(amount)
            assert isinstance(result, bool)
        
        assert tb._tokens >= -0.001


class TestRaceConditionCandidates:
    """Test scenarios that could reveal race conditions."""
    
    def test_rapid_token_consumption(self):
        """Test rapid token consumption in tight loop."""
        tb = TokenBucket(capacity=1000, tokens_per_second=1000)
        
        for _ in range(100):
            tb.allow(1)
        
        assert tb._tokens >= -0.001
        assert tb._tokens <= tb._capacity + 0.001
    
    def test_allow_immediately_after_wait(self):
        """Test allow() immediately after wait() completes."""
        tb = TokenBucket(capacity=5, tokens_per_second=100)
        tb.allow(5)  # Empty bucket
        
        tb.wait(1)  # Should wait then consume
        result = tb.allow(1)  # Try to consume immediately
        # Result depends on timing, but should not crash
        assert isinstance(result, bool)
    
    def test_refill_during_operations(self):
        """Test that operations work correctly during active refill."""
        tb = TokenBucket(capacity=10, tokens_per_second=10)
        tb.allow(10)  # Empty
        
        # Rapid allow calls while refill is happening
        for _ in range(20):
            tb.allow()  # May succeed or fail
            time.sleep(0.005)  # Allow partial refill
        
        assert tb._tokens >= -0.001
    
    def test_multiple_operations_same_time_window(self):
        """Test multiple operations in same time window."""
        tb = TokenBucket(capacity=100, tokens_per_second=100)
        
        start = time.monotonic()
        operations = 0
        while time.monotonic() - start < 0.01:  # All within 10ms
            tb.allow(1)
            operations += 1
        
        assert tb._tokens >= -0.001
        assert operations > 10


class TestStateInvariants:
    """Test that state invariants are maintained."""
    
    def test_tokens_never_exceed_capacity(self):
        """Test that tokens never exceed capacity."""
        tb = TokenBucket(capacity=50, tokens_per_second=1000)
        
        for _ in range(100):
            tb.allow()
            time.sleep(0.001)
            assert tb._tokens <= tb._capacity + 0.001
    
    def test_tokens_never_negative(self):
        """Test that tokens never go negative."""
        tb = TokenBucket(capacity=10, tokens_per_second=1)
        
        for _ in range(100):
            tb.allow(1)
            assert tb._tokens >= -0.001
    
    def test_rate_never_changes(self):
        """Test that rate remains constant."""
        tb = TokenBucket(capacity=50, tokens_per_second=25)
        original_rate = tb._tokens_per_second
        
        for _ in range(50):
            tb.allow(1)
        
        assert tb._tokens_per_second == original_rate
    
    def test_capacity_never_changes(self):
        """Test that capacity remains constant."""
        tb = TokenBucket(capacity=100, tokens_per_second=50)
        original_capacity = tb._capacity
        
        for _ in range(50):
            tb.allow(5)
        
        assert tb._capacity == original_capacity
    
    def test_last_refill_advances(self):
        """Test that last_refill time advances with operations."""
        tb = TokenBucket(capacity=10, tokens_per_second=10)
        initial_refill = tb._last_refill
        
        time.sleep(0.05)
        tb.allow()  # Trigger refill
        
        assert tb._last_refill > initial_refill


class TestBoundaryValues:
    """Test boundary values and transitions."""
    
    def test_exactly_capacity_available(self):
        """Test consuming exactly available capacity."""
        tb = TokenBucket(capacity=10.0, tokens_per_second=5.0)
        assert tb.allow(10.0) is True
    
    def test_just_over_available(self):
        """Test consuming just over available."""
        tb = TokenBucket(capacity=10.0, tokens_per_second=5.0)
        assert tb.allow(10.00001) is False
    
    def test_just_under_available(self):
        """Test consuming just under available."""
        tb = TokenBucket(capacity=10.0, tokens_per_second=5.0)
        assert tb.allow(9.99999) is True
    
    def test_single_precision_boundary(self):
        """Test at single precision boundaries."""
        tb = TokenBucket(capacity=1000000, tokens_per_second=1000000)
        # Should maintain precision with large numbers
        result = tb.allow(999999.9)
        assert result is True
    
    def test_refill_precision_at_boundary(self):
        """Test refill precision at capacity boundary."""
        tb = TokenBucket(capacity=1.0, tokens_per_second=1.0)
        tb.allow(1.0)
        
        time.sleep(0.1)
        tb.allow()  # Trigger refill
        
        # Should not exceed capacity
        assert tb._tokens <= 1.0 + 0.001


class TestStressAndStability:
    """Stress tests for stability."""
    
    def test_long_duration_operations(self):
        """Test long duration of operations."""
        tb = TokenBucket(capacity=1000, tokens_per_second=1000)
        
        start = time.monotonic()
        iterations = 0
        while time.monotonic() - start < 0.5:  # Run for 0.5 seconds
            tb.allow(1)
            iterations += 1
        
        assert iterations > 100
        assert tb._tokens >= -0.001
    
    def test_many_sequential_failures(self):
        """Test many sequential failed allow() attempts."""
        tb = TokenBucket(capacity=1, tokens_per_second=1)
        tb.allow(1)  # Empty bucket
        
        for _ in range(1000):
            result = tb.allow(100)
            assert result is False
        
        # Bucket should still be in valid state
        assert tb._tokens >= -0.001
    
    def test_alternating_success_failure(self):
        """Test alternating success and failure."""
        tb = TokenBucket(capacity=10, tokens_per_second=10)
        
        for i in range(100):
            if i % 2 == 0:
                result = tb.allow(10)
                # First one succeeds if bucket is full
            else:
                result = tb.allow(20)
                # Won't have 20 tokens
        
        assert tb._tokens >= -0.001

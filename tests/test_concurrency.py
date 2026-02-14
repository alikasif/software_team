"""Concurrency tests for TokenBucket rate limiter."""
import pytest
import threading
import time
from src.rate_limiter.token_bucket import TokenBucket


class TestConcurrentAllow:
    """Test allow() method under concurrent load."""
    
    def test_concurrent_allow_50_threads(self):
        """Test 50 threads calling allow() concurrently."""
        tb = TokenBucket(capacity=1000, tokens_per_second=1000)
        results = []
        
        def consume_tokens():
            for _ in range(5):
                result = tb.allow(1)
                results.append((result, tb._tokens))
        
        threads = [threading.Thread(target=consume_tokens) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 250 total attempts (50 threads * 5 each)
        assert len(results) == 250
        # Most should succeed given large initial capacity
        successes = sum(1 for r, _ in results if r is True)
        assert successes >= 200, f"Expected ~250 successes, got {successes}"
        # Tokens should never be negative
        assert all(tokens >= -0.001 for _, tokens in results)
    
    def test_concurrent_allow_100_operations(self):
        """Test 100+ concurrent operations via multiple threads."""
        tb = TokenBucket(capacity=500, tokens_per_second=500)
        results = []
        lock = threading.Lock()
        
        def worker(thread_id):
            for i in range(10):
                result = tb.allow(1)
                with lock:
                    results.append((thread_id, i, result))
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(15)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 150 total operations
        assert len(results) == 150
        # All results should be boolean
        assert all(isinstance(r, bool) for _, _, r in results)
    
    def test_concurrent_allow_token_consistency(self):
        """Test that token count remains consistent under concurrent load."""
        tb = TokenBucket(capacity=100, tokens_per_second=100)
        final_tokens = []
        
        def consume_and_check():
            for _ in range(20):
                tb.allow(1)
            with tb._lock:
                final_tokens.append(tb._tokens)
        
        threads = [threading.Thread(target=consume_and_check) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All final token counts should be non-negative
        assert all(t >= -0.001 for t in final_tokens)
        # Token bucket should still be in valid state
        assert tb._tokens >= -0.001
        assert tb._tokens <= tb._capacity + 0.001
    
    def test_concurrent_allow_different_amounts(self):
        """Test concurrent threads consuming different token amounts."""
        tb = TokenBucket(capacity=1000, tokens_per_second=1000)
        results = []
        lock = threading.Lock()
        
        def worker(thread_id):
            amount = thread_id % 5 + 1  # 1-5 tokens
            for _ in range(10):
                result = tb.allow(amount)
                with lock:
                    results.append((thread_id, amount, result))
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 500 operations
        assert len(results) == 500
        # Verify no negative tokens
        assert tb._tokens >= -0.001


class TestConcurrentWait:
    """Test wait() method under concurrent load."""
    
    def test_concurrent_wait_50_threads(self):
        """Test 50 threads calling wait() concurrently."""
        tb = TokenBucket(capacity=10, tokens_per_second=100)
        results = []
        lock = threading.Lock()
        
        def wait_for_token():
            start_time = time.monotonic()
            tb.wait(1)
            elapsed = time.monotonic() - start_time
            with lock:
                results.append(elapsed)
        
        # Create threads that will need to wait
        threads = [threading.Thread(target=wait_for_token) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should complete
        assert len(results) == 50
        # All times should be positive
        assert all(t >= 0 for t in results)
    
    def test_concurrent_wait_token_consumption(self):
        """Test that wait() correctly consumes tokens under concurrent load."""
        tb = TokenBucket(capacity=5, tokens_per_second=100)
        results = []
        lock = threading.Lock()
        
        def wait_and_record():
            tb.wait(1)
            with lock:
                results.append(tb._tokens)
        
        threads = [threading.Thread(target=wait_and_record) for _ in range(30)]
        start = time.monotonic()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.monotonic() - start
        
        # Should consume 30 tokens total
        assert len(results) == 30
        # Final state should be valid
        assert tb._tokens >= -0.001
        # Total elapsed should be reasonable (30 tokens / 100 rate ~ 0.3s)
        assert elapsed < 1.0  # Should be much less than 1 second
    
    def test_concurrent_wait_100_operations(self):
        """Test 100+ concurrent wait operations."""
        tb = TokenBucket(capacity=20, tokens_per_second=200)
        completion_count = []
        lock = threading.Lock()
        
        def worker():
            tb.wait(1)
            with lock:
                completion_count.append(1)
        
        threads = [threading.Thread(target=worker) for _ in range(120)]
        start = time.monotonic()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.monotonic() - start
        
        # All threads should complete
        assert sum(completion_count) == 120
        # Should complete in reasonable time (120 tokens / 200 rate ~ 0.6s)
        assert elapsed < 1.5
    
    def test_concurrent_wait_multiple_tokens(self):
        """Test concurrent wait with multiple token requests."""
        tb = TokenBucket(capacity=50, tokens_per_second=100)
        results = []
        lock = threading.Lock()
        
        def worker(thread_id):
            amount = (thread_id % 3) + 1  # 1-3 tokens per thread
            tb.wait(amount)
            with lock:
                results.append((thread_id, amount, tb._tokens))
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(40)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should complete
        assert len(results) == 40


class TestConcurrentMixed:
    """Test mixed concurrent allow() and wait() operations."""
    
    def test_concurrent_allow_and_wait_mixed(self):
        """Test concurrent mix of allow() and wait() calls."""
        tb = TokenBucket(capacity=100, tokens_per_second=100)
        results = []
        lock = threading.Lock()
        
        def worker(thread_id):
            for i in range(10):
                if i % 2 == 0:
                    # Even iterations: use allow()
                    result = tb.allow(1)
                    with lock:
                        results.append(('allow', result))
                else:
                    # Odd iterations: use wait()
                    tb.wait(1)
                    with lock:
                        results.append(('wait', True))
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(30)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 300 total operations (30 threads * 10)
        assert len(results) == 300
        # Verify token bucket is in valid state
        assert tb._tokens >= -0.001
        assert tb._tokens <= tb._capacity + 0.001
    
    def test_concurrent_operations_no_race_condition(self):
        """Test that concurrent operations don't cause race conditions."""
        tb = TokenBucket(capacity=200, tokens_per_second=200)
        token_snapshots = []
        lock = threading.Lock()
        operation_count = 0
        
        def worker(thread_id):
            nonlocal operation_count
            for _ in range(25):
                if thread_id % 2 == 0:
                    tb.allow(1)
                else:
                    tb.wait(1)
                operation_count += 1
                
                with lock:
                    token_snapshots.append(tb._tokens)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Verify all snapshots are valid
        assert all(ts >= -0.001 and ts <= tb._capacity + 0.001 for ts in token_snapshots)
        # Should have many snapshots
        assert len(token_snapshots) >= 400
    
    def test_concurrent_high_contention(self):
        """Test high contention scenario with many threads and frequent operations."""
        tb = TokenBucket(capacity=500, tokens_per_second=500)
        operation_results = []
        lock = threading.Lock()
        
        def high_frequency_worker():
            for _ in range(20):
                result = tb.allow(1)
                with lock:
                    operation_results.append(result)
                
                # Occasionally wait
                if len(operation_results) % 7 == 0:
                    time.sleep(0.0001)
        
        # Create 60 threads for high contention
        threads = [threading.Thread(target=high_frequency_worker) for _ in range(60)]
        start = time.monotonic()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.monotonic() - start
        
        # Should complete all operations
        assert len(operation_results) == 1200
        # Should complete reasonably fast
        assert elapsed < 2.0
        # All operations should be valid
        assert all(isinstance(r, bool) for r in operation_results)
    
    def test_concurrent_stress_test(self):
        """Stress test with many concurrent operations."""
        tb = TokenBucket(capacity=1000, tokens_per_second=1000)
        success_count = [0]
        lock = threading.Lock()
        
        def stress_worker():
            for _ in range(15):
                amount = (id(threading.current_thread()) % 3) + 1
                try:
                    result = tb.allow(amount)
                    with lock:
                        if result:
                            success_count[0] += 1
                except Exception as e:
                    pytest.fail(f"Unexpected exception: {e}")
        
        threads = [threading.Thread(target=stress_worker) for _ in range(50)]
        start = time.monotonic()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.monotonic() - start
        
        # Most operations should succeed
        assert success_count[0] > 400, f"Expected >400 successes, got {success_count[0]}"
        # Should complete in reasonable time
        assert elapsed < 1.0


class TestConcurrencyConsistency:
    """Test consistency invariants under concurrent load."""
    
    def test_token_count_consistency_multiple_snapshots(self):
        """Test that token count never violates invariants."""
        tb = TokenBucket(capacity=100, tokens_per_second=100)
        violations = []
        lock = threading.Lock()
        
        def worker():
            for _ in range(30):
                tb.allow(1)
                with tb._lock:
                    tokens = tb._tokens
                    capacity = tb._capacity
                    if tokens < -0.001 or tokens > capacity + 0.001:
                        with lock:
                            violations.append((tokens, capacity))
        
        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # No violations should be recorded
        assert len(violations) == 0, f"Found invariant violations: {violations}"
    
    def test_concurrent_refill_consistency(self):
        """Test that refill works correctly under concurrent load."""
        tb = TokenBucket(capacity=50, tokens_per_second=100)
        results = []
        lock = threading.Lock()
        
        def worker():
            for _ in range(25):
                tb.allow(1)
        
        # Empty the bucket
        tb.allow(50)
        
        # Wait a bit to allow refill
        time.sleep(0.1)
        
        # Now stress test concurrent access while tokens refill
        threads = [threading.Thread(target=worker) for _ in range(25)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # bucket should be in valid state
        assert tb._tokens >= -0.001
        assert tb._tokens <= tb._capacity + 0.001
    
    def test_lock_prevents_corruption(self):
        """Test that internal lock prevents data corruption."""
        tb = TokenBucket(capacity=1000, tokens_per_second=1000)
        final_states = []
        lock = threading.Lock()
        
        def worker():
            for _ in range(50):
                tb.allow(1)
            
            # Snapshot final state
            with tb._lock:
                with lock:
                    final_states.append({
                        'tokens': tb._tokens,
                        'capacity': tb._capacity,
                        'rate': tb._tokens_per_second
                    })
        
        threads = [threading.Thread(target=worker) for _ in range(30)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All snapshots should show consistent state values
        assert all(s['capacity'] == 1000 for s in final_states)
        assert all(s['rate'] == 1000 for s in final_states)
        # Final tokens should be valid
        assert all(s['tokens'] >= -0.001 for s in final_states)


class TestConcurrentTimingAccuracy:
    """Test timing accuracy under concurrent load."""
    
    def test_concurrent_wait_timing_accuracy(self):
        """Test that wait() timing is accurate under concurrent load."""
        tb = TokenBucket(capacity=10, tokens_per_second=50)
        timings = []
        lock = threading.Lock()
        
        def worker():
            # First consume tokens
            tb.allow(10)
            # Then measure wait time for 1 token
            start = time.monotonic()
            tb.wait(1)
            elapsed = time.monotonic() - start
            with lock:
                timings.append(elapsed)
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All waits should be roughly 0.02 seconds (1 token / 50 rate)
        # Allow wide tolerance for 10 concurrent threads under variable system load
        for timing in timings:
            assert 0.01 < timing < 0.25, f"Timing out of bounds: {timing}s"

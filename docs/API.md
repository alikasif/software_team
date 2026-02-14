# Token Bucket Rate Limiter - API Reference

Complete API documentation for the TokenBucket rate limiter implementation.

## Table of Contents

- [Overview](#overview)
- [TokenBucket Class](#tokenbucket-class)
- [Methods](#methods)
- [Exceptions](#exceptions)
- [Configuration Guide](#configuration-guide)
- [Thread Safety](#thread-safety)
- [Usage Patterns](#usage-patterns)

## Overview

The `TokenBucket` class from `src.rate_limiter.token_bucket` provides thread-safe rate limiting using the token bucket algorithm. It maintains a bucket of tokens that refill at a constant rate and supports both blocking and non-blocking operations.

### Quick Import

```python
from src.rate_limiter.token_bucket import TokenBucket
from src.rate_limiter.exceptions import RateLimitExceeded
```

## TokenBucket Class

### Constructor

```python
class TokenBucket:
    def __init__(self, capacity: float, tokens_per_second: float) -> None:
        """Initialize the token bucket.
        
        Args:
            capacity: Maximum number of tokens that can be stored.
                     Must be positive (> 0).
            tokens_per_second: Rate at which tokens are added to the bucket.
                              Must be positive (> 0).
        
        Raises:
            ValueError: If capacity or tokens_per_second is not positive.
        """
```

### Parameters

#### capacity: float
- **Description**: The maximum number of tokens the bucket can hold
- **Type**: float (supports integers and decimals)
- **Constraints**: Must be greater than 0
- **Default**: None (required parameter)
- **Purpose**: Allows bursting above the average rate for up to this many operations

**Examples:**
```python
# Standard burst of 100 requests
limiter = TokenBucket(capacity=100, tokens_per_second=50)

# Fractional capacity for sub-operation granularity
limiter = TokenBucket(capacity=5.5, tokens_per_second=2)

# Large capacity for bigger burst allowance
limiter = TokenBucket(capacity=10000, tokens_per_second=1000)

# Very small capacity for strict limiting
limiter = TokenBucket(capacity=1, tokens_per_second=0.1)
```

#### tokens_per_second: float
- **Description**: The rate at which tokens are added to the bucket
- **Type**: float (supports integers and decimals)
- **Constraints**: Must be greater than 0
- **Default**: None (required parameter)
- **Purpose**: Enforces the average rate limit in operations per second

**Examples:**
```python
# 100 requests per second
limiter = TokenBucket(capacity=50, tokens_per_second=100)

# 10 requests per second
limiter = TokenBucket(capacity=10, tokens_per_second=10)

# 1 request per minute (1/60)
limiter = TokenBucket(capacity=1, tokens_per_second=1/60)

# 0.5 requests per second (one every 2 seconds)
limiter = TokenBucket(capacity=1, tokens_per_second=0.5)

# Very fast rate
limiter = TokenBucket(capacity=100, tokens_per_second=10000)
```

### Constructor Examples

**Basic HTTP API Rate Limiter**
```python
# 100 requests per minute with burst up to 20
limiter = TokenBucket(capacity=20, tokens_per_second=100/60)
```

**Database Connection Throttle**
```python
# 1000 connections per second with 500 connection burst
limiter = TokenBucket(capacity=500, tokens_per_second=1000)
```

**Background Job Throttle**
```python
# 1 job per second
limiter = TokenBucket(capacity=5, tokens_per_second=1)
```

**Strict Rate Limit**
```python
# Exactly 5 per second, no burst
limiter = TokenBucket(capacity=5, tokens_per_second=5)
```

**Very Permissive Burst**
```python
# 2 per second average, but 1000 burst
limiter = TokenBucket(capacity=1000, tokens_per_second=2)
```

## Methods

### allow()

```python
def allow(self, tokens: float = 1) -> bool:
    """Check if tokens are available and consume them if so.
    
    This method does not block. Returns immediately with a boolean
    indicating whether the tokens were available.
    
    Args:
        tokens: Number of tokens to consume. Defaults to 1.
               Must be positive (> 0).
    
    Returns:
        bool: True if tokens were consumed, False otherwise.
    
    Raises:
        ValueError: If tokens <= 0.
    """
```

#### Parameters

**tokens: float**
- **Default**: 1
- **Constraints**: Must be positive (> 0)
- **Purpose**: Number of tokens to check and consume

#### Return Value

- **True**: Tokens were available and have been consumed
- **False**: Insufficient tokens available; no consumption occurred

#### Behavior

- Non-blocking: Returns immediately
- Atomic: All-or-nothing consumption (partial consumption not allowed)
- Refilling: Automatically refills tokens based on elapsed time
- Thread-safe: Safe to call from multiple threads

#### Examples

**Basic Single Token Check**
```python
limiter = TokenBucket(capacity=10, tokens_per_second=5)

if limiter.allow():
    print("Operation allowed")
    process_request()
else:
    print("Rate limit exceeded")
    reject_request()
```

**Checking Multiple Tokens**
```python
limiter = TokenBucket(capacity=10, tokens_per_second=5)

# Batch operation requiring 5 tokens
if limiter.allow(5):
    print("Can execute batch")
    process_batch()
else:
    print("Batch limit exceeded, retry later")
```

**Weighted Operations**
```python
limiter = TokenBucket(capacity=100, tokens_per_second=50)

def handle_request(request_type):
    # Different operations have different "costs"
    if request_type == "light":
        tokens_needed = 1
    elif request_type == "medium":
        tokens_needed = 5
    else:  # heavy
        tokens_needed = 20
    
    if limiter.allow(tokens_needed):
        process_request(request_type)
    else:
        respond_with_429()
```

**Fractional Tokens**
```python
limiter = TokenBucket(capacity=10, tokens_per_second=1)

# Each request uses only half a token
for i in range(100):
    if limiter.allow(0.5):
        print(f"Request {i} allowed")
```

**Loop with Backoff**
```python
limiter = TokenBucket(capacity=5, tokens_per_second=2)

def try_operation_with_backoff():
    attempt = 0
    while attempt < 5:
        if limiter.allow():
            perform_operation()
            return True
        attempt += 1
        print(f"Attempt {attempt} limited, waiting...")
        time.sleep(1)  # Back off
    return False
```

### wait()

```python
def wait(self, tokens: float = 1) -> None:
    """Block until tokens are available, then consume them.
    
    This method blocks the calling thread until the specified
    number of tokens are available. Once available, tokens are
    consumed and the method returns.
    
    Args:
        tokens: Number of tokens to wait for and consume.
               Defaults to 1. Must be positive (> 0).
    
    Raises:
        ValueError: If tokens <= 0.
    """
```

#### Parameters

**tokens: float**
- **Default**: 1
- **Constraints**: Must be positive (> 0)
- **Purpose**: Number of tokens to wait for and consume

#### Return Value

- **None**: Always returns None after successfully consuming tokens
- Does not return False or raise exception on success

#### Behavior

- Blocking: Sleeps until tokens are available
- Non-busy-waiting: Uses short sleeps (1ms) to avoid CPU spinning
- Atomic: Prevents partial consumption
- Thread-safe: Concurrent wait() calls are safe

#### Latency

- If tokens available immediately: ~1-5 microseconds
- If waiting needed: 1-2 milliseconds + wait time

#### Examples

**Basic Blocking Pattern**
```python
limiter = TokenBucket(capacity=10, tokens_per_second=5)

# Wait for 1 token, then proceed
limiter.wait()
print("Token acquired, processing...")
process_request()
```

**Controlled Request Loop**
```python
limiter = TokenBucket(capacity=5, tokens_per_second=10)

for i in range(100):
    limiter.wait()  # Ensures never exceeds 10 per second
    print(f"Processing request {i}")
```

**Batch Operations**
```python
limiter = TokenBucket(capacity=50, tokens_per_second=100)

def process_batch(items):
    # Wait for enough tokens for the whole batch
    limiter.wait(len(items))
    # Process all items at once
    for item in items:
        do_work(item)

process_batch([1, 2, 3, 4, 5])  # Waits for 5 tokens
```

**Thread Worker with Rate Limiting**
```python
limiter = TokenBucket(capacity=20, tokens_per_second=100)

def worker(requests):
    for req in requests:
        limiter.wait()
        handle_request(req)

# Multiple workers, coordinated rate limiting
threads = [threading.Thread(target=worker, args=(batch,)) 
           for batch in batch_requests]
```

**Adaptive Waiting**
```python
limiter = TokenBucket(capacity=10, tokens_per_second=5)

def get_data_with_wait(data_size):
    # Wait proportional to data size
    tokens_needed = data_size / 100  # 100 bytes = 1 token
    limiter.wait(tokens_needed)
    return fetch_data()
```

**Timed Operations**
```python
limiter = TokenBucket(capacity=10, tokens_per_second=2)

def timed_operation():
    start = time.time()
    limiter.wait()
    elapsed = time.time() - start
    print(f"Waited {elapsed:.3f} seconds for token")
    do_work()
```

### try_consume()

```python
def try_consume(self, tokens: float = 1) -> bool:
    """Alias for allow(). Try to consume tokens without blocking.
    
    This is an alternative name for allow() for API clarity.
    Behavior is identical to allow().
    
    Args:
        tokens: Number of tokens to consume. Defaults to 1.
               Must be positive (> 0).
    
    Returns:
        bool: True if tokens were consumed, False otherwise.
    
    Raises:
        ValueError: If tokens <= 0.
    """
```

#### Parameters

**tokens: float**
- **Default**: 1
- **Constraints**: Must be positive (> 0)

#### Return Value

- **True**: Tokens were consumed
- **False**: Insufficient tokens

#### Behavior

- Identical to `allow()`
- Provided as an alternative name for semantic clarity
- Useful when "try" semantics are clearer than "allow"

#### Examples

**Semantic Clarity**
```python
# Instead of:
if limiter.allow():
    proceed()

# Can also write:
if limiter.try_consume():
    proceed()

# Or with amounts:
if limiter.try_consume(5):
    do_batch()
```

**In Conditional Expressions**
```python
limiter = TokenBucket(capacity=100, tokens_per_second=50)

# Use as predicate
result = (limiter.try_consume() and process_data()) or fallback()

# In list comprehension (unlikely but possible)
results = [process(x) for x in items if limiter.try_consume(x.weight)]
```

## Exceptions

### RateLimitExceeded

```python
class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded.
    
    Base class: Exception
    
    Use this exception to signal that a rate limit has been exceeded
    in your application logic. The TokenBucket class itself doesn't
    raise this—it returns False from allow(). You may raise it in
    your code as needed.
    """
```

#### Usage

```python
from src.rate_limiter.exceptions import RateLimitExceeded

limiter = TokenBucket(capacity=10, tokens_per_second=5)

def protected_operation():
    if not limiter.allow():
        raise RateLimitExceeded("Rate limit exceeded, try again later")
    
    # Perform operation
    return execute()

try:
    result = protected_operation()
except RateLimitExceeded as e:
    print(f"Error: {e}")
```

#### ValueError

The TokenBucket class raises `ValueError` for invalid parameters:

```python
try:
    limiter = TokenBucket(capacity=0, tokens_per_second=5)
except ValueError as e:
    print(f"Invalid parameter: {e}")
    # Output: Invalid parameter: capacity must be positive

try:
    limiter = TokenBucket(capacity=10, tokens_per_second=-5)
except ValueError as e:
    print(f"Invalid parameter: {e}")
    # Output: Invalid parameter: tokens_per_second must be positive

# Also raised by methods:
limiter = TokenBucket(capacity=10, tokens_per_second=5)
try:
    limiter.allow(0)
except ValueError as e:
    print(f"Invalid parameter: {e}")
    # Output: Invalid parameter: tokens must be positive
```

## Configuration Guide

### Choosing Capacity and Rate

The relationship between capacity and rate determines burst behavior:

#### High Capacity, Moderate Rate

```python
limiter = TokenBucket(capacity=1000, tokens_per_second=100)
```
- **Behavior**: Allows large initial burst (1000 ops), then 100/sec
- **Use case**: API with bursty traffic patterns
- **Characteristics**: Client-friendly, recovers quickly

#### Low Capacity, High Rate

```python
limiter = TokenBucket(capacity=10, tokens_per_second=1000)
```
- **Behavior**: Immediate burst of 10, then smooth 1000/sec
- **Use case**: High-throughput system with small entry barrier
- **Characteristics**: Very fair, predictable

#### Capacity Equals Rate

```python
limiter = TokenBucket(capacity=50, tokens_per_second=50)
```
- **Behavior**: No real burst (tokens used faster than added)
- **Use case**: Strict rate limiting
- **Characteristics**: Enforces exact rate limit

#### High Capacity, Low Rate

```python
limiter = TokenBucket(capacity=100, tokens_per_second=1)
```
- **Behavior**: One burst of 100, then must wait
- **Use case**: Batch operations with limits
- **Characteristics**: Unforgiving if burst is wasted

### Common Configurations

**REST API - Generous Burst**
```python
# 10,000 requests per minute with 1000-request burst
limiter = TokenBucket(
    capacity=1000,
    tokens_per_second=10000/60
)
```

**Database Connections**
```python
# 5000 connections per second with 500 conn burst
limiter = TokenBucket(
    capacity=500,
    tokens_per_second=5000
)
```

**File Uploads**
```python
# 10 MB per second (10 tokens = 1MB)
limiter = TokenBucket(
    capacity=100,  # 10 MB burst
    tokens_per_second=100  # 10 MB/sec
)
```

**Email Sending**
```python
# 1 email per second with small burst
limiter = TokenBucket(
    capacity=5,
    tokens_per_second=1
)
```

**Cache Requests**
```python
# 100k requests per second with 50k burst
limiter = TokenBucket(
    capacity=50000,
    tokens_per_second=100000
)
```

## Thread Safety

### Safe Concurrent Access

TokenBucket is thread-safe by design:

```python
from src.rate_limiter.token_bucket import TokenBucket
import threading

limiter = TokenBucket(capacity=100, tokens_per_second=100)

def worker(worker_id, num_requests):
    for i in range(num_requests):
        if limiter.allow():
            print(f"Worker {worker_id}: request {i}")

# Create multiple threads
threads = []
for i in range(10):
    t = threading.Thread(target=worker, args=(i, 100))
    threads.append(t)
    t.start()

# All threads can safely use the same limiter
for t in threads:
    t.join()
```

### Internal Synchronization

- **Lock Type**: `threading.Lock()`
- **Scope**: Protects all state modifications
- **Granularity**: Fine-grained (only held during operation)
- **Deadlock Risk**: Very low (no nested locks)

### Wait() with Multiple Threads

```python
limiter = TokenBucket(capacity=5, tokens_per_second=10)

def worker(name):
    start = time.time()
    limiter.wait(3)
    elapsed = time.time() - start
    print(f"{name}: waited {elapsed:.3f}s")

# Multiple threads waiting for tokens
for i in range(5):
    threading.Thread(target=worker, args=(f"Thread-{i}",)).start()
```

### Best Practices

✅ **DO**: Share single TokenBucket across threads
```python
limiter = TokenBucket(capacity=100, tokens_per_second=50)

# Good: all threads use same limiter
for i in range(10):
    threading.Thread(target=work, args=(limiter,)).start()
```

❌ **DON'T**: Create per-thread limiters
```python
# Bad: defeats the purpose of rate limiting
def worker():
    limiter = TokenBucket(capacity=100, tokens_per_second=50)
    # Each thread has separate bucket!
```

✅ **DO**: Use for thread coordination
```python
# Coordinate rate across multiple threads
limiter = TokenBucket(capacity=50, tokens_per_second=100)

# All threads respect the same limit
results = []
for request in requests:
    if limiter.allow():
        results.append(process(request))
```

## Usage Patterns

### Pattern 1: Non-Blocking with Fallback

```python
limiter = TokenBucket(capacity=10, tokens_per_second=5)

def handle_request(request):
    if limiter.allow():
        return process_request(request)
    else:
        # Graceful degradation
        return serve_from_cache(request)
```

### Pattern 2: Blocking with Timeout

```python
import threading

limiter = TokenBucket(capacity=10, tokens_per_second=5)

def handle_request_with_timeout(request, timeout=5):
    event = threading.Event()
    
    def wait_thread():
        limiter.wait()
        event.set()
    
    thread = threading.Thread(target=wait_thread, daemon=True)
    thread.start()
    
    if event.wait(timeout):
        return process_request(request)
    else:
        return error_response("Timed out waiting for rate limit")
```

### Pattern 3: Weighted Operations

```python
limiter = TokenBucket(capacity=100, tokens_per_second=50)

OPERATION_WEIGHTS = {
    'read': 1,
    'write': 5,
    'delete': 10,
}

def rate_limited_operation(op_type):
    tokens_needed = OPERATION_WEIGHTS.get(op_type, 1)
    if limiter.allow(tokens_needed):
        return execute(op_type)
    else:
        return reject_request(op_type)
```

### Pattern 4: Adaptive Rate Limiting

```python
limiter = TokenBucket(capacity=100, tokens_per_second=50)

def adaptive_handler(request, payload_size):
    # Charge more for larger payloads
    tokens_needed = max(1, payload_size // 1000)
    
    if limiter.allow(tokens_needed):
        return process(request)
    else:
        return rate_limited()
```

### Pattern 5: Multi-Tier Limiting

```python
premium_limiter = TokenBucket(capacity=1000, tokens_per_second=1000)
standard_limiter = TokenBucket(capacity=100, tokens_per_second=100)
free_limiter = TokenBucket(capacity=10, tokens_per_second=10)

def handle_request(request):
    user = get_user(request)
    
    if user.tier == 'premium':
        limiter = premium_limiter
    elif user.tier == 'standard':
        limiter = standard_limiter
    else:
        limiter = free_limiter
    
    if limiter.allow():
        return serve_request(request)
    else:
        return respond_429()
```

### Pattern 6: Request Queuing with Rate Limiting

```python
from queue import Queue
import threading

limiter = TokenBucket(capacity=50, tokens_per_second=100)
request_queue = Queue()

def worker():
    while True:
        request = request_queue.get()
        limiter.wait()
        process_request(request)

# Start worker threads
for _ in range(4):
    threading.Thread(target=worker, daemon=True).start()

# Add requests to queue from main thread
for request in incoming_requests:
    request_queue.put(request)
```

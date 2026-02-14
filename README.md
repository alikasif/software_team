# Token Bucket Rate Limiter

A thread-safe Python implementation of the token bucket algorithm for rate limiting. Control the rate at which operations are performed with millisecond-precision timing and support for both blocking and non-blocking patterns.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Algorithm Explanation](#algorithm-explanation)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Thread Safety](#thread-safety)
- [Performance Tips](#performance-tips)
- [Contributing](#contributing)
- [License](#license)

## Overview

The token bucket rate limiter is a widely-used algorithm that allows you to control the rate of operations in your application. It works by maintaining a "bucket" that can hold a maximum number of tokens. Tokens are added to the bucket at a constant rate. When an operation needs to be performed, tokens are consumed from the bucket. If there aren't enough tokens available, the operation is either rejected or the caller waits until tokens become available.

Key features:
- **Thread-safe**: Safe to use from multiple threads simultaneously
- **Flexible**: Support for both blocking and non-blocking patterns
- **Precise**: Microsecond-level timing accuracy
- **Simple**: Minimal dependencies, easy to integrate

## Installation

### From Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/yourusername/software_team.git
cd software_team
pip install -e .
```

### Basic Usage

```python
from src.rate_limiter.token_bucket import TokenBucket

# Create a rate limiter that allows 10 requests per second
limiter = TokenBucket(capacity=10, tokens_per_second=10)
```

## Quick Start

### 5-Line Basic Example

```python
from src.rate_limiter.token_bucket import TokenBucket

limiter = TokenBucket(capacity=10, tokens_per_second=5)
if limiter.allow():
    print("Request allowed!")
else:
    print("Rate limit exceeded, try again later")
```

### Non-Blocking Pattern

```python
from src.rate_limiter.token_bucket import TokenBucket

limiter = TokenBucket(capacity=5, tokens_per_second=5)

def get_data():
    if limiter.allow():
        # Perform the protected operation
        return fetch_data()
    else:
        # Handle rate limit gracefully
        raise Exception("Rate limited, retry later")
```

### Blocking Pattern

```python
from src.rate_limiter.token_bucket import TokenBucket

limiter = TokenBucket(capacity=5, tokens_per_second=5)

def get_data():
    # Wait until a token is available
    limiter.wait()
    # Perform the protected operation
    return fetch_data()
```

## Algorithm Explanation

### How It Works (Non-Technical)

Imagine a bucket with a hole in the bottom:

1. **Initial State**: The bucket starts full with tokens
2. **Refilling**: Over time, tokens accumulate back into the bucket at a constant rate (e.g., 5 tokens per second)
3. **Consuming**: When you need to perform an operation, you consume tokens from the bucket
4. **Capacity Limit**: The bucket has a maximum capacity—it never holds more tokens than this limit
5. **Blocking**: If you need tokens but the bucket is empty, you can wait for tokens to accumulate

### Key Concepts

**Capacity**: The maximum number of tokens the bucket can hold
- Example: `capacity=10` means the bucket never exceeds 10 tokens
- Allows for "bursts" of operations up to the capacity

**Tokens Per Second**: The rate at which tokens are added to the bucket
- Example: `tokens_per_second=5` means 5 tokens are added every second
- This defines the long-term average rate limit

**Tokens**: Individual units of permission
- Each operation typically costs 1 token
- Can request multiple tokens for heavier operations

### Visual Example

```
Initial state (capacity=5, tokens_per_second=2):
[█████] = 5 tokens available

After consuming 3 tokens:
[██   ] = 2 tokens available

After 1 second passes:
[████ ] = 4 tokens available (2 new tokens added)

After 2 more seconds pass:
[█████] = 5 tokens available (capped at capacity)
```

### Burst Handling

One key advantage of the token bucket algorithm is its ability to handle bursts. With `capacity=10` and `tokens_per_second=2`:

- You can immediately perform up to 10 operations (using all available tokens)
- Then you must wait for tokens to refill before continuing
- This is useful for scenarios where you want to allow occasional spikes but enforce an average rate

## API Reference

### TokenBucket Class

#### Constructor

```python
TokenBucket(capacity: float, tokens_per_second: float)
```

Creates a new token bucket rate limiter.

**Parameters:**
- `capacity` (float): Maximum number of tokens the bucket can hold. Must be positive.
- `tokens_per_second` (float): Rate at which tokens are added to the bucket. Must be positive.

**Raises:**
- `ValueError`: If capacity or tokens_per_second is not positive

**Example:**
```python
# Allow 100 requests per second with burst capacity of 50
limiter = TokenBucket(capacity=50, tokens_per_second=100)

# Allow 1 request per minute
limiter = TokenBucket(capacity=1, tokens_per_second=1/60)

# Allow fractional tokens
limiter = TokenBucket(capacity=2.5, tokens_per_second=0.5)
```

#### allow() Method

```python
allow(tokens: float = 1) -> bool
```

Check if tokens are available and consume them if so. Does not block.

**Parameters:**
- `tokens` (float): Number of tokens to consume. Defaults to 1. Must be positive.

**Returns:**
- `True` if tokens were successfully consumed
- `False` if insufficient tokens are available

**Raises:**
- `ValueError`: If tokens is not positive

**Example:**
```python
limiter = TokenBucket(capacity=10, tokens_per_second=5)

# Check if 1 token is available
if limiter.allow():
    print("Request allowed")
else:
    print("Rate limited")

# Check if 5 tokens are available
if limiter.allow(5):
    print("Batch operation allowed")

# Consume fractional tokens
if limiter.allow(0.5):
    print("Half request allowed")
```

#### wait() Method

```python
wait(tokens: float = 1) -> None
```

Block until tokens are available, then consume them. This method will sleep until enough tokens have accumulated.

**Parameters:**
- `tokens` (float): Number of tokens to consume. Defaults to 1. Must be positive.

**Raises:**
- `ValueError`: If tokens is not positive

**Example:**
```python
limiter = TokenBucket(capacity=5, tokens_per_second=10)

# Wait for 1 token to become available
limiter.wait()
print("Token available, proceeding...")

# Wait for 5 tokens
limiter.wait(5)
print("5 tokens available, proceeding...")

# Wait for burst of 10 tokens (takes ~1 second at 10 tokens/sec)
limiter.wait(10)
print("Large batch allowed")
```

#### try_consume() Method

```python
try_consume(tokens: float = 1) -> bool
```

Alias for `allow()`. Try to consume tokens without blocking.

**Parameters:**
- `tokens` (float): Number of tokens to consume. Defaults to 1.

**Returns:**
- `True` if tokens were successfully consumed
- `False` if insufficient tokens are available

**Example:**
```python
limiter = TokenBucket(capacity=10, tokens_per_second=5)

if limiter.try_consume(2):
    print("Successfully consumed 2 tokens")
```

### RateLimitExceeded Exception

```python
class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass
```

Custom exception for rate limit violations. Can be used in custom implementations that require explicit exception raising.

**Example:**
```python
from src.rate_limiter.exceptions import RateLimitExceeded

try:
    if not limiter.allow():
        raise RateLimitExceeded("Rate limit exceeded")
except RateLimitExceeded:
    print("Too many requests")
```

## Usage Examples

### Example 1: Basic Rate Limiting (Non-Blocking)

Rate limit API requests to 100 per minute with the ability to burst up to 50:

```python
from src.rate_limiter.token_bucket import TokenBucket
import requests

limiter = TokenBucket(capacity=50, tokens_per_second=100/60)

def fetch_data(user_id):
    if not limiter.allow():
        return {"error": "Rate limited, try again in a moment"}
    
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json()

# Usage
result = fetch_data(123)
print(result)
```

### Example 2: Blocking Pattern with wait()

Ensure operations never exceed 10 per second, waiting when necessary:

```python
from src.rate_limiter.token_bucket import TokenBucket
import time

limiter = TokenBucket(capacity=10, tokens_per_second=10)

def process_request(request_id):
    limiter.wait()  # Block until a token is available
    print(f"Processing request {request_id}")
    # Do work...
    time.sleep(0.1)  # Simulate work

# Requests will be processed at a controlled rate
for i in range(100):
    process_request(i)
```

### Example 3: Rate Limiting HTTP Requests

Limit concurrent requests to an external API:

```python
from src.rate_limiter.token_bucket import TokenBucket
import threading
import requests

limiter = TokenBucket(capacity=5, tokens_per_second=2)

def request_handler(url, request_id):
    if limiter.allow():
        try:
            response = requests.get(url, timeout=5)
            print(f"Request {request_id}: {response.status_code}")
        except requests.RequestException as e:
            print(f"Request {request_id} failed: {e}")
    else:
        print(f"Request {request_id} rate limited")

# Simulate multiple concurrent requests
urls = ["https://api.example.com/data"] * 20
threads = []
for i, url in enumerate(urls):
    t = threading.Thread(target=request_handler, args=(url, i))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

### Example 4: Concurrent Usage with Threads

Safe usage across multiple threads:

```python
from src.rate_limiter.token_bucket import TokenBucket
import threading
import time

limiter = TokenBucket(capacity=20, tokens_per_second=100)

def worker(worker_id, num_ops):
    for i in range(num_ops):
        limiter.wait()
        print(f"Worker {worker_id} operation {i}")
        time.sleep(0.01)  # Simulate work

# Create 5 worker threads
threads = []
for i in range(5):
    t = threading.Thread(target=worker, args=(i, 10))
    threads.append(t)
    t.start()

# Wait for all workers to complete
for t in threads:
    t.join()

print("All workers completed")
```

### Example 5: Configuring for Different Scenarios

**Scenario 1: Bursty Traffic**
```python
# Allow occasional bursts up to 100 requests, 
# but enforce 10 requests/sec average
limiter = TokenBucket(capacity=100, tokens_per_second=10)
```

**Scenario 2: Strict Rate Limiting**
```python
# Enforce exactly 5 requests per second with no burst
limiter = TokenBucket(capacity=5, tokens_per_second=5)
```

**Scenario 3: Very Low Rate**
```python
# Allow 1 request every 10 seconds
limiter = TokenBucket(capacity=1, tokens_per_second=0.1)
```

**Scenario 4: Fractional Tokens for Weighted Operations**
```python
# Different operations cost different tokens
limiter = TokenBucket(capacity=100, tokens_per_second=50)

# Light operation: 1 token
if limiter.allow(1):
    light_operation()

# Medium operation: 5 tokens
if limiter.allow(5):
    medium_operation()

# Heavy operation: 20 tokens
if limiter.allow(20):
    heavy_operation()
```

## Thread Safety

The TokenBucket implementation is fully thread-safe and can be safely shared across multiple threads:

- An internal lock (`threading.Lock`) protects all state modifications
- Multiple threads can call `allow()`, `wait()`, and `try_consume()` simultaneously
- The refill mechanism is atomic—pending operations never see inconsistent state
- No race conditions or deadlocks possible

**Safe Usage Example:**
```python
from src.rate_limiter.token_bucket import TokenBucket
import threading

limiter = TokenBucket(capacity=100, tokens_per_second=100)

def worker(worker_id):
    for i in range(50):
        if limiter.allow():
            print(f"Worker {worker_id} got token {i}")

# Safe to create many threads
threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## Performance Tips

### 1. Choose Appropriate Capacity and Rate

```python
# Good: capacity matches expected burst size
limiter = TokenBucket(capacity=50, tokens_per_second=100)

# Less optimal: tiny capacity leads to frequent rate limiting
limiter = TokenBucket(capacity=1, tokens_per_second=100)
```

### 2. Use Non-Blocking Pattern When Possible

```python
# Preferred: non-blocking, allows graceful degradation
if limiter.allow():
    do_work()
else:
    handle_rate_limit()

# Less ideal: blocking can cause thread starvation
limiter.wait()
do_work()
```

### 3. Reuse TokenBucket Instances

```python
# Good: create once, reuse
limiter = TokenBucket(capacity=100, tokens_per_second=50)

def handle_request(request):
    if limiter.allow():
        process(request)

# Bad: creating new instances repeatedly
def handle_request(request):
    limiter = TokenBucket(capacity=100, tokens_per_second=50)
    if limiter.allow():
        process(request)
```

### 4. Consider Memory vs. CPU Trade-offs

```python
# CPU intensive: high refresh rate, many checks
limiter = TokenBucket(capacity=1000000, tokens_per_second=1000000)

# Memory intensive but simpler: low refresh rate
limiter = TokenBucket(capacity=10, tokens_per_second=0.1)
```

### Benchmarks

Typical performance metrics on modern hardware:

- **allow() call**: ~1-5 microseconds (with lock acquisition)
- **wait() call**: ~0.5-2 milliseconds (includes sleep overhead)
- **Memory overhead**: ~500 bytes per TokenBucket instance

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Write tests for new features
2. Ensure all tests pass: `pytest tests/`
3. Follow PEP 8 style guidelines
4. Add docstrings to new public methods
5. Update documentation for API changes

## License

This project is licensed under the MIT License. See LICENSE file for details.

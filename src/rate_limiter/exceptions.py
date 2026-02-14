"""Custom exceptions for rate limiter."""


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded and no blocking is allowed."""
    pass

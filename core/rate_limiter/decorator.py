from functools import wraps
from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from core.rate_limiter.memory import InMemoryRateLimiter
from core.rate_limiter.key_builder import RateLimitKeyBuilder


def rate_limit(
    backend: Optional[InMemoryRateLimiter] = None,
    limit: int = 10,
    window: int = 60,
    key_func: Optional[Callable[[Request], str]] = None,
    use_fingerprint: bool = True,
):
    """
    Decorator for rate limiting individual endpoints with secure key generation

    Args:
        backend: InMemoryRateLimiter instance
        limit: Maximum requests per window
        window: Time window in seconds
        key_func: Custom function to extract rate limit key (optional)
        use_fingerprint: Use browser fingerprint for anonymous users (more secure)

    Example:
        @router.post("/evaluate")
        @rate_limit(backend=rate_limiter, limit=5, window=60)
        async def create_evaluation(request: Request, ...):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                request = kwargs.get("request")

            if not request:
                raise ValueError("Request object not found in function arguments")

            if not backend or not isinstance(backend, InMemoryRateLimiter):
                raise ValueError("InMemoryRateLimiter instance must be provided")

            # Get rate limit key
            if key_func:
                key = key_func(request)
            else:
                key = RateLimitKeyBuilder.build_key(request, use_fingerprint)

            # Check rate limit
            is_allowed, retry_after = await backend.is_allowed(key, limit, window)

            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(retry_after),
                    },
                )

            # Get remaining requests
            remaining = await backend.get_remaining(key, limit)

            # Call original function
            response = await func(*args, **kwargs)

            # Add rate limit headers if response supports it
            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
                response.headers["X-RateLimit-Window"] = str(window)

            return response

        return wrapper

    return decorator

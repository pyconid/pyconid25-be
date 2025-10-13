import asyncio
from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import Mock
from fastapi import Request
from fastapi.responses import JSONResponse
from core.rate_limiter.middleware import RateLimitMiddleware
from core.rate_limiter.memory import InMemoryRateLimiter
from main import app


class TestRateLimitMiddleware(IsolatedAsyncioTestCase):
    def setUp(self):
        self.backend = InMemoryRateLimiter
        self.limit = 5
        self.window = 60

    def create_mock_request(self, path="/test", client_host="192.168.1.1"):
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = path
        request.client = Mock()
        request.client.host = client_host
        request.headers = {
            "User-Agent": "TestAgent",
            "Accept-Language": "en-US",
            "Accept-Encoding": "gzip",
        }
        request.state = Mock()
        return request

    async def test_rate_limit_headers_on_success(self):
        middleware = RateLimitMiddleware(
            app=app,
            backend=self.backend,
            enabled=True,
            limit=self.limit,
            window=self.window,
            use_fingerprint=False,
        )

        request = self.create_mock_request()

        # Mock call_next to return a response
        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # First request
        response = await middleware.dispatch(request, mock_call_next)

        # Check headers
        self.assertIn("X-RateLimit-Limit", response.headers)
        self.assertIn("X-RateLimit-Remaining", response.headers)
        self.assertIn("X-RateLimit-Window", response.headers)

        self.assertEqual(response.headers["X-RateLimit-Limit"], str(self.limit))
        self.assertEqual(response.headers["X-RateLimit-Window"], str(self.window))

        # Remaining should be limit - 1 (4)
        remaining = int(response.headers["X-RateLimit-Remaining"])
        self.assertEqual(remaining, self.limit - 1)

    async def test_rate_limit_remaining_never_negative(self):
        middleware = RateLimitMiddleware(
            app=app,
            backend=self.backend,
            enabled=True,
            limit=self.limit,
            window=self.window,
            use_fingerprint=False,
        )

        request = self.create_mock_request()

        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # Make requests up to the limit
        for i in range(self.limit):
            response = await middleware.dispatch(request, mock_call_next)
            remaining = int(response.headers["X-RateLimit-Remaining"])

            # Remaining should never be negative
            self.assertGreaterEqual(
                remaining, 0, f"Request {i + 1}: Remaining should never be negative"
            )

            # Check specific values
            expected_remaining = self.limit - (i + 1)
            self.assertEqual(
                remaining,
                expected_remaining,
                f"Request {i + 1}: Expected {expected_remaining}, got {remaining}",
            )

        # Next request should be blocked with 429
        response = await middleware.dispatch(request, mock_call_next)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "0")

    async def test_rate_limit_last_request_remaining_zero(self):
        middleware = RateLimitMiddleware(
            app=app,
            backend=self.backend,
            enabled=True,
            limit=3,  # Small limit for easier testing
            window=self.window,
            use_fingerprint=False,
        )

        request = self.create_mock_request()

        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # Request 1: remaining = 2
        response = await middleware.dispatch(request, mock_call_next)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "2")

        # Request 2: remaining = 1
        response = await middleware.dispatch(request, mock_call_next)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "1")

        # Request 3 (last): remaining = 0 (NOT -1!)
        response = await middleware.dispatch(request, mock_call_next)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["X-RateLimit-Remaining"],
            "0",
            "Last allowed request should show remaining=0, not -1",
        )

        # Request 4: blocked with 429
        response = await middleware.dispatch(request, mock_call_next)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "0")

    async def test_rate_limit_blocked_request_headers(self):
        middleware = RateLimitMiddleware(
            app=app,
            backend=self.backend,
            enabled=True,
            limit=2,
            window=self.window,
            use_fingerprint=False,
        )

        request = self.create_mock_request()

        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # Use up the limit
        await middleware.dispatch(request, mock_call_next)
        await middleware.dispatch(request, mock_call_next)

        # Next request should be blocked
        response = await middleware.dispatch(request, mock_call_next)

        self.assertEqual(response.status_code, 429)
        self.assertIn("X-RateLimit-Limit", response.headers)
        self.assertIn("X-RateLimit-Remaining", response.headers)
        self.assertIn("X-RateLimit-Reset", response.headers)
        self.assertIn("Retry-After", response.headers)

        self.assertEqual(response.headers["X-RateLimit-Remaining"], "0")

    async def test_rate_limit_different_keys_independent_headers(self):
        middleware = RateLimitMiddleware(
            app=app,
            backend=self.backend,
            enabled=True,
            limit=3,
            window=self.window,
            use_fingerprint=False,
        )

        request1 = self.create_mock_request(client_host="192.168.1.1")
        request2 = self.create_mock_request(client_host="192.168.1.2")

        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # User 1: Make 2 requests
        response = await middleware.dispatch(request1, mock_call_next)
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "2")

        response = await middleware.dispatch(request1, mock_call_next)
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "1")

        # User 2: Should have full limit (3 requests)
        response = await middleware.dispatch(request2, mock_call_next)
        self.assertEqual(
            response.headers["X-RateLimit-Remaining"],
            "2",
            "Different user should have independent limit",
        )

    async def test_disabled_middleware_no_rate_limiting(self):
        middleware = RateLimitMiddleware(
            app=app,
            backend=self.backend,
            enabled=False,
            limit=1,
            window=self.window,
            use_fingerprint=False,
        )

        request = self.create_mock_request()

        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # Make multiple requests (more than limit)
        for i in range(5):
            response = await middleware.dispatch(request, mock_call_next)
            self.assertEqual(response.status_code, 200)
            # No rate limit headers should be set
            self.assertNotIn("X-RateLimit-Limit", response.headers)

    async def test_excluded_paths_no_rate_limiting(self):
        middleware = RateLimitMiddleware(
            app=app,
            backend=self.backend,
            enabled=True,
            limit=1,
            window=self.window,
            exclude_paths=["/health", "/docs"],
            use_fingerprint=False,
        )

        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # Request to excluded path
        request_health = self.create_mock_request(path="/health")

        # Make multiple requests (more than limit)
        for i in range(5):
            response = await middleware.dispatch(request_health, mock_call_next)
            self.assertEqual(response.status_code, 200)
            # No rate limit headers
            self.assertNotIn("X-RateLimit-Limit", response.headers)

        # Request to non-excluded path should be rate limited
        request_api = self.create_mock_request(path="/api/test")
        response = await middleware.dispatch(request_api, mock_call_next)
        self.assertEqual(response.status_code, 200)
        # Should have rate limit headers
        self.assertIn("X-RateLimit-Limit", response.headers)

    async def test_concurrent_requests_remaining_accurate(self):
        middleware = RateLimitMiddleware(
            app=app,
            backend=self.backend,
            enabled=True,
            limit=10,
            window=self.window,
            use_fingerprint=False,
        )

        request = self.create_mock_request()

        async def mock_call_next(req):
            await asyncio.sleep(0.01)  # Simulate some processing
            return JSONResponse({"status": "ok"})

        # Make concurrent requests
        tasks = [middleware.dispatch(request, mock_call_next) for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)

        # Next request should be blocked
        response = await middleware.dispatch(request, mock_call_next)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "0")

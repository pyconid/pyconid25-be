import asyncio
from unittest.async_case import IsolatedAsyncioTestCase
from core.rate_limiter.memory import InMemoryRateLimiter


class TestInMemoryRateLimiter(IsolatedAsyncioTestCase):
    def setUp(self):
        self.limiter = InMemoryRateLimiter()

    async def test_basic_rate_limiting(self):
        key = "test_user"
        limit = 5
        window = 60

        # Should allow first 5 requests
        for i in range(limit):
            is_allowed, retry_after = await self.limiter.is_allowed(key, limit, window)
            self.assertTrue(is_allowed, f"Request {i + 1} should be allowed")
            self.assertIsNone(retry_after)

        # 6th request should be blocked
        is_allowed, retry_after = await self.limiter.is_allowed(key, limit, window)
        self.assertFalse(is_allowed, "Request beyond limit should be blocked")
        self.assertIsNotNone(retry_after)
        self.assertGreater(retry_after, 0)

    async def test_sliding_window(self):
        key = "sliding_test"
        limit = 3
        window = 2  # 2 seconds

        # Allow 3 requests
        for _ in range(limit):
            is_allowed, _ = await self.limiter.is_allowed(key, limit, window)
            self.assertTrue(is_allowed)

        # 4th request blocked
        is_allowed, retry_after = await self.limiter.is_allowed(key, limit, window)
        self.assertFalse(is_allowed)

        # Wait for window to pass
        await asyncio.sleep(window + 0.1)

        # Should allow new requests after window expires
        is_allowed, retry_after = await self.limiter.is_allowed(key, limit, window)
        self.assertTrue(is_allowed, "Should allow requests after window expires")
        self.assertIsNone(retry_after)

    async def test_different_keys_independent(self):
        limit = 3
        window = 60

        # Fill up limit for key1
        for _ in range(limit):
            is_allowed, _ = await self.limiter.is_allowed("key1", limit, window)
            self.assertTrue(is_allowed)

        # key1 should be blocked
        is_allowed, _ = await self.limiter.is_allowed("key1", limit, window)
        self.assertFalse(is_allowed)

        # key2 should still be allowed (independent limit)
        is_allowed, _ = await self.limiter.is_allowed("key2", limit, window)
        self.assertTrue(is_allowed, "Different keys should have independent limits")

    async def test_get_remaining(self):
        key = "remaining_test"
        limit = 5
        window = 60

        # Initially should have full limit
        remaining = await self.limiter.get_remaining(key, limit)
        self.assertEqual(remaining, limit)

        # After 2 requests
        await self.limiter.is_allowed(key, limit, window)
        await self.limiter.is_allowed(key, limit, window)
        remaining = await self.limiter.get_remaining(key, limit)
        self.assertEqual(remaining, 3)

        # After hitting limit
        for _ in range(3):
            await self.limiter.is_allowed(key, limit, window)
        remaining = await self.limiter.get_remaining(key, limit)
        self.assertEqual(remaining, 0)

    async def test_reset(self):
        key = "reset_test"
        limit = 3
        window = 60

        # Fill up limit
        for _ in range(limit):
            await self.limiter.is_allowed(key, limit, window)

        # Should be blocked
        is_allowed, _ = await self.limiter.is_allowed(key, limit, window)
        self.assertFalse(is_allowed)

        # Reset the key
        await self.limiter.reset(key)

        # Should be allowed again
        is_allowed, _ = await self.limiter.is_allowed(key, limit, window)
        self.assertTrue(is_allowed, "Should allow requests after reset")

        # Remaining should be full limit minus 1
        remaining = await self.limiter.get_remaining(key, limit)
        self.assertEqual(remaining, limit - 1)

    async def test_cleanup_expired(self):
        key1 = "cleanup_key1"
        key2 = "cleanup_key2"
        limit = 3
        window = 1  # 1 second

        # Add some requests for key1 and key2
        await self.limiter.is_allowed(key1, limit, window)
        await self.limiter.is_allowed(key2, limit, window)

        # Wait for window to expire
        await asyncio.sleep(window + 0.1)

        # Run cleanup
        await self.limiter.cleanup_expired(window)

        # Both keys should have no requests stored
        # New requests should be allowed (full limit)
        remaining1 = await self.limiter.get_remaining(key1, limit)
        remaining2 = await self.limiter.get_remaining(key2, limit)
        self.assertEqual(remaining1, limit)
        self.assertEqual(remaining2, limit)

    async def test_retry_after_calculation(self):
        key = "retry_test"
        limit = 2
        window = 10  # 10 seconds

        # Use up limit
        await self.limiter.is_allowed(key, limit, window)
        await self.limiter.is_allowed(key, limit, window)

        # Get retry_after
        is_allowed, retry_after = await self.limiter.is_allowed(key, limit, window)
        self.assertFalse(is_allowed)

        # retry_after should be close to window time
        self.assertGreater(retry_after, 0)
        self.assertLessEqual(retry_after, window)
        # Should be close to window since we just made the requests
        self.assertGreater(retry_after, window - 1)

    async def test_concurrent_requests(self):
        key = "concurrent_test"
        limit = 10
        window = 60

        # Simulate concurrent requests
        tasks = [self.limiter.is_allowed(key, limit, window) for _ in range(20)]
        results = await asyncio.gather(*tasks)

        # Exactly 'limit' requests should be allowed
        allowed_count = sum(1 for is_allowed, _ in results if is_allowed)
        self.assertEqual(
            allowed_count,
            limit,
            f"Expected {limit} allowed requests, got {allowed_count}",
        )

        # The rest should be blocked
        blocked_count = sum(1 for is_allowed, _ in results if not is_allowed)
        self.assertEqual(blocked_count, 10)

    async def test_zero_limit(self):
        key = "zero_limit_test"
        limit = 0
        window = 60

        # Should block immediately
        is_allowed, retry_after = await self.limiter.is_allowed(key, limit, window)
        self.assertFalse(is_allowed)
        self.assertIsNotNone(retry_after)

    async def test_large_limit(self):
        key = "large_limit_test"
        limit = 1000
        window = 60

        # Should allow many requests
        for i in range(limit):
            is_allowed, _ = await self.limiter.is_allowed(key, limit, window)
            self.assertTrue(is_allowed, f"Request {i + 1} should be allowed")

        # Next one should be blocked
        is_allowed, _ = await self.limiter.is_allowed(key, limit, window)
        self.assertFalse(is_allowed)

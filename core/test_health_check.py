from unittest.async_case import IsolatedAsyncioTestCase
from core.health_check import health_check


class HealthCheckTest(IsolatedAsyncioTestCase):
    async def test_health_check(self):
        health_check()

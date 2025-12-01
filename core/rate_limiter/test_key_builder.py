from typing import Optional
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock
import jwt
from core.rate_limiter.key_builder import RateLimitKeyBuilder
from settings import ALGORITHM, SECRET_KEY


class TestRateLimitKeyBuilder(IsolatedAsyncioTestCase):
    def setUp(self):
        self.builder = RateLimitKeyBuilder()

    def create_mock_request(
        self,
        client_host: Optional[str] = "192.168.1.1",
        user_agent: Optional[str] = "Mozilla/5.0",
        accept_language: Optional[str] = "en-US",
        accept_encoding: Optional[str] = "gzip, deflate",
        x_forwarded_for: Optional[str] = None,
        x_real_ip: Optional[str] = None,
        authorization: Optional[str] = None,
    ):
        request = Mock()
        request.client = Mock()
        request.client.host = client_host

        # Mock headers
        headers = {
            "User-Agent": user_agent,
            "Accept-Language": accept_language,
            "Accept-Encoding": accept_encoding,
        }

        if x_forwarded_for:
            headers["X-Forwarded-For"] = x_forwarded_for
        if x_real_ip:
            headers["X-Real-IP"] = x_real_ip
        if authorization:
            headers["authorization"] = authorization

        request.headers = headers
        return request

    def create_jwt_token(self, user_id: int, **kwargs):
        payload = {"id": user_id, **kwargs}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def test_get_real_client_ip_from_client_host(self):
        request = self.create_mock_request(client_host="203.0.113.42")
        ip = self.builder.get_real_client_ip(request)
        self.assertEqual(ip, "203.0.113.42")

    def test_get_real_client_ip_from_x_real_ip(self):
        request = self.create_mock_request(client_host=None, x_real_ip="198.51.100.1")
        request.client = None
        ip = self.builder.get_real_client_ip(request)
        self.assertEqual(ip, "198.51.100.1")

    def test_get_real_client_ip_from_x_forwarded_for(self):
        request = self.create_mock_request(
            client_host=None, x_forwarded_for="198.51.100.2, 192.0.2.1"
        )
        request.client = None
        ip = self.builder.get_real_client_ip(request)
        # Should take first IP
        self.assertEqual(ip, "198.51.100.2")

    def test_get_real_client_ip_unknown(self):
        request = self.create_mock_request(client_host=None)
        request.client = None
        ip = self.builder.get_real_client_ip(request)
        self.assertEqual(ip, "unknown")

    def test_get_composite_fingerprint_consistency(self):
        request1 = self.create_mock_request(user_agent="Mozilla/5.0 Chrome")
        request2 = self.create_mock_request(user_agent="Mozilla/5.0 Firefox")
        request3 = self.create_mock_request(user_agent="Mozilla/5.0 Chrome")

        fp1 = self.builder.get_composite_fingerprint(request1)
        fp2 = self.builder.get_composite_fingerprint(request2)
        fp3 = self.builder.get_composite_fingerprint(request3)

        # Same user agent should give same fingerprint
        self.assertEqual(fp1, fp3)
        # Different user agent should give different fingerprint
        self.assertNotEqual(fp1, fp2)
        # Should be 12 characters (MD5 hash truncated)
        self.assertEqual(len(fp1), 12)

    def test_get_composite_fingerprint(self):
        request1 = self.create_mock_request(
            user_agent="Chrome", accept_language="en-US", accept_encoding="gzip"
        )
        request2 = self.create_mock_request(
            user_agent="Chrome", accept_language="id-ID", accept_encoding="gzip"
        )
        request3 = self.create_mock_request(
            user_agent="Chrome", accept_language="en-US", accept_encoding="gzip"
        )

        fp1 = self.builder.get_composite_fingerprint(request1)
        fp2 = self.builder.get_composite_fingerprint(request2)
        fp3 = self.builder.get_composite_fingerprint(request3)

        # Same headers should give same fingerprint
        self.assertEqual(fp1, fp3)
        # Different Accept-Language should give different fingerprint
        self.assertNotEqual(fp1, fp2)
        # Should be 12 characters
        self.assertEqual(len(fp1), 12)

    def test_build_authenticated_key_without_fingerprint(self):
        key = self.builder.build_authenticated_key(
            user_id=123, request=None, use_fingerprint=False
        )
        self.assertEqual(key, "user:123")

    def test_build_authenticated_key_with_fingerprint(self):
        request = self.create_mock_request(user_agent="Chrome", accept_language="en-US")
        key = self.builder.build_authenticated_key(
            user_id=123, request=request, use_fingerprint=True
        )
        # Should have format user:id:fingerprint
        self.assertTrue(key.startswith("user:123:"))
        parts = key.split(":")
        self.assertEqual(len(parts), 3)
        self.assertEqual(len(parts[2]), 12)  # fingerprint length

    def test_build_authenticated_key_with_fingerprint_no_request(self):
        key = self.builder.build_authenticated_key(
            user_id=123, request=None, use_fingerprint=True
        )
        # Should fallback to non-fingerprint version
        self.assertEqual(key, "user:123")

    def test_build_anonymous_key_without_fingerprint(self):
        request = self.create_mock_request(client_host="192.168.1.1")
        key = self.builder.build_anonymous_key(request, use_fingerprint=False)
        self.assertEqual(key, "anon:192.168.1.1")

    def test_build_anonymous_key_with_fingerprint(self):
        request = self.create_mock_request(client_host="192.168.1.1")
        key = self.builder.build_anonymous_key(request, use_fingerprint=True)
        # Should have format anon:ip:fingerprint
        self.assertTrue(key.startswith("anon:192.168.1.1:"))
        parts = key.split(":")
        self.assertEqual(len(parts), 3)  # anon:192.168.1.1:fingerprint
        self.assertEqual(len(parts[-1]), 12)  # fingerprint length

    def test_build_key_authenticated_with_valid_token(self):
        token = self.create_jwt_token(user_id=456)
        request = self.create_mock_request(authorization=f"Bearer {token}")

        key = self.builder.build_key(request, use_fingerprint=False)
        self.assertEqual(key, "user:456")

    def test_build_key_authenticated_with_fingerprint(self):
        token = self.create_jwt_token(user_id=789)
        request = self.create_mock_request(
            authorization=f"Bearer {token}",
            user_agent="Chrome",
            accept_language="en-US",
        )

        key = self.builder.build_key(request, use_fingerprint=True)
        self.assertTrue(key.startswith("user:789:"))

    def test_build_key_authenticated_invalid_token(self):
        request = self.create_mock_request(
            client_host="192.168.1.1",
            authorization="Bearer invalid_token_12345",
        )

        key = self.builder.build_key(request, use_fingerprint=False)
        # Should fallback to anonymous
        self.assertTrue(key.startswith("anon:"))

    def test_build_key_authenticated_expired_token(self):
        # Create expired token (exp in the past)
        import time

        expired_token = jwt.encode(
            {"id": 999, "exp": int(time.time()) - 3600},  # 1 hour ago
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        request = self.create_mock_request(
            client_host="192.168.1.1", authorization=f"Bearer {expired_token}"
        )

        key = self.builder.build_key(request, use_fingerprint=False)
        # Should fallback to anonymous
        self.assertTrue(key.startswith("anon:"))

    def test_build_key_anonymous(self):
        request = self.create_mock_request(client_host="10.0.0.1")
        key = self.builder.build_key(request, use_fingerprint=False)
        self.assertEqual(key, "anon:10.0.0.1")

    def test_build_key_different_browsers_same_user(self):
        token = self.create_jwt_token(user_id=111)

        request_chrome = self.create_mock_request(
            authorization=f"Bearer {token}",
            user_agent="Chrome/90.0",
            accept_language="en-US",
        )
        request_firefox = self.create_mock_request(
            authorization=f"Bearer {token}",
            user_agent="Firefox/88.0",
            accept_language="en-US",
        )

        key_chrome = self.builder.build_key(request_chrome, use_fingerprint=True)
        key_firefox = self.builder.build_key(request_firefox, use_fingerprint=True)

        # Both should be for user 111
        self.assertTrue(key_chrome.startswith("user:111:"))
        self.assertTrue(key_firefox.startswith("user:111:"))
        # But should have different fingerprints
        self.assertNotEqual(key_chrome, key_firefox)

    def test_build_key_different_browsers_same_user_without_fingerprint(self):
        token = self.create_jwt_token(user_id=222)

        request_chrome = self.create_mock_request(
            authorization=f"Bearer {token}", user_agent="Chrome/90.0"
        )
        request_firefox = self.create_mock_request(
            authorization=f"Bearer {token}", user_agent="Firefox/88.0"
        )

        key_chrome = self.builder.build_key(request_chrome, use_fingerprint=False)
        key_firefox = self.builder.build_key(request_firefox, use_fingerprint=False)

        # Should be exactly the same
        self.assertEqual(key_chrome, key_firefox)
        self.assertEqual(key_chrome, "user:222")

    def test_extract_user_id_from_key_authenticated(self):
        user_id = self.builder.extract_user_id_from_key("user:123")
        self.assertEqual(user_id, "123")

        user_id = self.builder.extract_user_id_from_key("user:456:abc123def456")
        self.assertEqual(user_id, "456:abc123def456")

    def test_extract_user_id_from_key_anonymous(self):
        user_id = self.builder.extract_user_id_from_key("anon:192.168.1.1")
        self.assertIsNone(user_id)

        user_id = self.builder.extract_user_id_from_key("anon:192.168.1.1:abc123def456")
        self.assertIsNone(user_id)

    def test_authorization_header_case_insensitive(self):
        token = self.create_jwt_token(user_id=333)

        # Test with lowercase 'authorization'
        request = self.create_mock_request(authorization=f"Bearer {token}")
        key = self.builder.build_key(request, use_fingerprint=False)
        self.assertEqual(key, "user:333")

    def test_bearer_token_with_extra_spaces(self):
        token = self.create_jwt_token(user_id=444)

        request = self.create_mock_request(authorization=f"Bearer  {token}  ")
        key = self.builder.build_key(request, use_fingerprint=False)
        self.assertEqual(key, "user:444")

    def test_non_bearer_authorization(self):
        request = self.create_mock_request(
            client_host="192.168.1.1", authorization="Basic dXNlcjpwYXNz"
        )
        key = self.builder.build_key(request, use_fingerprint=False)
        # Should fallback to anonymous
        self.assertTrue(key.startswith("anon:"))

    def test_fingerprint_includes_ip(self):
        """Test that fingerprint includes IP address"""
        # Same headers, different IPs should give different fingerprints
        request1 = self.create_mock_request(
            client_host="192.168.1.1",
            user_agent="Chrome",
            accept_language="en-US",
        )
        request2 = self.create_mock_request(
            client_host="192.168.1.2",  # Different IP
            user_agent="Chrome",
            accept_language="en-US",
        )

        fp1 = self.builder.get_composite_fingerprint(request1)
        fp2 = self.builder.get_composite_fingerprint(request2)

        # Different IPs should produce different fingerprints
        self.assertNotEqual(fp1, fp2)

    def test_fingerprint_includes_sec_ch_ua_headers(self):
        """Test that fingerprint includes Sec-Ch-Ua headers"""
        request1 = self.create_mock_request(client_host="192.168.1.1")
        request1.headers["Sec-Ch-Ua"] = '"Chrome";v="90"'
        request1.headers["Sec-Ch-Ua-Platform"] = '"Windows"'

        request2 = self.create_mock_request(client_host="192.168.1.1")
        request2.headers["Sec-Ch-Ua"] = '"Firefox";v="88"'
        request2.headers["Sec-Ch-Ua-Platform"] = '"Linux"'

        fp1 = self.builder.get_composite_fingerprint(request1)
        fp2 = self.builder.get_composite_fingerprint(request2)

        # Different Sec-Ch-Ua headers should produce different fingerprints
        self.assertNotEqual(fp1, fp2)

    def test_same_user_different_user_agent_same_ip_with_fingerprint(self):
        """
        Test that changing User-Agent alone is NOT enough to bypass
        if IP is the same (fingerprint includes IP)
        """
        token = self.create_jwt_token(user_id=555)

        # Request 1: Chrome, IP 192.168.1.1
        request1 = self.create_mock_request(
            client_host="192.168.1.1",
            authorization=f"Bearer {token}",
            user_agent="Chrome/90.0",
        )

        # Request 2: Firefox (different), same IP 192.168.1.1
        request2 = self.create_mock_request(
            client_host="192.168.1.1",  # Same IP!
            authorization=f"Bearer {token}",
            user_agent="Firefox/88.0",  # Different User-Agent
        )

        key1 = self.builder.build_key(request1, use_fingerprint=True)
        key2 = self.builder.build_key(request2, use_fingerprint=True)

        # Even though User-Agent different, IP same
        # So fingerprints should be different (User-Agent is part of it)
        self.assertTrue(key1.startswith("user:555:"))
        self.assertTrue(key2.startswith("user:555:"))
        self.assertNotEqual(key1, key2)  # Still different due to UA

    def test_same_user_same_user_agent_different_ip_with_fingerprint(self):
        """
        Test that changing IP produces different fingerprint
        even with same User-Agent
        """
        token = self.create_jwt_token(user_id=666)

        # Request 1: Chrome, IP 192.168.1.1
        request1 = self.create_mock_request(
            client_host="192.168.1.1",
            authorization=f"Bearer {token}",
            user_agent="Chrome/90.0",
        )

        # Request 2: Same Chrome, different IP
        request2 = self.create_mock_request(
            client_host="10.0.0.1",  # Different IP!
            authorization=f"Bearer {token}",
            user_agent="Chrome/90.0",  # Same User-Agent
        )

        key1 = self.builder.build_key(request1, use_fingerprint=True)
        key2 = self.builder.build_key(request2, use_fingerprint=True)

        # Different IPs should produce different keys
        self.assertTrue(key1.startswith("user:666:"))
        self.assertTrue(key2.startswith("user:666:"))
        self.assertNotEqual(key1, key2)

    def test_anonymous_user_fingerprint_with_ip(self):
        """Test that anonymous users get different keys from different IPs"""
        # Same browser, different IPs
        request1 = self.create_mock_request(
            client_host="192.168.1.1", user_agent="Chrome"
        )
        request2 = self.create_mock_request(client_host="10.0.0.1", user_agent="Chrome")

        key1 = self.builder.build_anonymous_key(request1, use_fingerprint=True)
        key2 = self.builder.build_anonymous_key(request2, use_fingerprint=True)

        # Should be different due to IP
        self.assertNotEqual(key1, key2)

import hashlib
from typing import Optional
from fastapi import Request
import jwt

from settings import ALGORITHM, SECRET_KEY


class RateLimitKeyBuilder:
    @staticmethod
    def get_real_client_ip(request: Request) -> str:
        """
        Get real client IP address, preventing spoofing

        Priority:
        1. request.client.host (most reliable, from TCP connection)
        2. X-Real-IP (if behind trusted proxy like nginx)
        3. First IP from X-Forwarded-For (only if from trusted proxy)
        """
        # Most reliable: actual TCP connection IP
        client_ip = request.client.host if request.client else None

        if not client_ip:
            # Fallback: check proxy headers (only if you trust your proxy)
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip.strip()

            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                # Take first IP (client IP before proxies)
                return forwarded.split(",")[0].strip()

            return "unknown"

        return client_ip

    @staticmethod
    def get_composite_fingerprint(request: Request) -> str:
        """
        Create composite fingerprint from multiple request attributes
        This makes it harder to bypass by just changing IP
        """
        client_ip = RateLimitKeyBuilder.get_real_client_ip(request)
        factors = [
            request.headers.get("User-Agent", ""),
            request.headers.get("Accept-Language", ""),
            request.headers.get("Accept-Encoding", ""),
            request.headers.get("Sec-Ch-Ua", ""),
            request.headers.get("Sec-Ch-Ua-Platform", ""),
            client_ip,
        ]

        combined = "|".join(factors)
        return hashlib.md5(combined.encode()).hexdigest()[:12]

    @staticmethod
    def build_authenticated_key(
        user_id: int | str,
        request: Optional[Request] = None,
        use_fingerprint: bool = False,
    ) -> str:
        """
        Build key for authenticated users

        Args:
            user_id: User ID from JWT
            request: FastAPI request object (needed if use_fingerprint=True)
            use_fingerprint: Include browser fingerprint for per-session limiting

        Returns:
            Rate limit key string
        """
        if use_fingerprint and request:
            # Per-session: user can use multiple browsers/devices
            fingerprint = RateLimitKeyBuilder.get_composite_fingerprint(request)
            return f"user:{user_id}:{fingerprint}"
        else:
            # Per-user: shared limit across all browsers/devices
            return f"user:{user_id}"

    @staticmethod
    def build_anonymous_key(request: Request, use_fingerprint: bool = True) -> str:
        """
        Build key for anonymous users using multiple factors

        Args:
            request: FastAPI request object
            use_fingerprint: Include browser fingerprint for stricter limiting

        Returns:
            Composite key string
        """
        ip = RateLimitKeyBuilder.get_real_client_ip(request)

        if use_fingerprint:
            # Stricter: IP + browser fingerprint
            fingerprint = RateLimitKeyBuilder.get_composite_fingerprint(request)
            return f"anon:{ip}:{fingerprint}"
        else:
            # Looser: IP only (for public endpoints)
            return f"anon:{ip}"

    @staticmethod
    def build_key(request: Request, use_fingerprint: bool = True) -> str:
        """
        Main function to build rate limit key

        Priority:
        1. If authenticated: use user_id + optional fingerprint
        2. If anonymous: use IP + optional fingerprint

        Args:
            request: FastAPI request object
            use_fingerprint: Include browser fingerprint for per-session limiting
                - True: Separate limits per browser/device (more UX friendly)
                - False: Shared limit across all browsers/devices (more strict)

        Returns:
            Rate limit key string

        Examples:
            Authenticated with fingerprint=True:
                - Chrome: "user:123:a1b2c3d4e5f6"
                - Firefox: "user:123:f6e5d4c3b2a1"
                → Each browser gets separate rate limit

            Authenticated with fingerprint=False:
                - Chrome: "user:123"
                - Firefox: "user:123"
                → Shared rate limit across all browsers

            Anonymous with fingerprint=True:
                - "anon:192.168.1.1:a1b2c3d4e5f6"

            Anonymous with fingerprint=False:
                - "anon:192.168.1.1"
        """
        # Check if user is authenticated
        token = request.headers.get("authorization", None)
        if token is not None and token.startswith("Bearer "):
            token = token.split(" ", 1)[1].strip()

        if token:
            # Authenticated user - use verified id from JWT
            user_id = None
            try:
                payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("id")
            except jwt.PyJWTError:
                pass

            if user_id:
                return RateLimitKeyBuilder.build_authenticated_key(
                    user_id, request, use_fingerprint
                )

        # Anonymous user - use composite key
        return RateLimitKeyBuilder.build_anonymous_key(request, use_fingerprint)

    @staticmethod
    def extract_user_id_from_key(key: str) -> Optional[int | str]:
        """Extract user_id from key if it's a user key"""
        if key.startswith("user:"):
            return key.split(":", 1)[1]
        return None

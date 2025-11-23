from schemas.streaming import MuxStreamDetail
import base64
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple

import jwt
import mux_python
from mux_python.rest import ApiException

import settings
from core.log import logger


class MuxService:
    """
    Mux service for managing live streams

    Reference:
    - Mux Secured Streaming: https://www.mux.com/docs/guides/secure-video-playback
    - Mux Webhooks: https://www.mux.com/docs/core/listen-for-webhooks
    - Example Mux Python: https://github.com/muxinc/mux-python/tree/master/examples
    """

    def __init__(self):
        configuration = mux_python.Configuration()
        configuration.username = settings.MUX_TOKEN_ID
        configuration.password = settings.MUX_TOKEN_SECRET

        self.live_streams_api = mux_python.LiveStreamsApi(
            mux_python.ApiClient(configuration)
        )
        self.stream_url = "rtmps://global-live.mux.com:443/app/"

    def create_live_stream(
        self, is_public: bool = True
    ) -> Tuple[str, str, str, Optional[str]]:
        """
        Create a new live stream in Mux

        Args:
            is_public: Whether the stream is public or private

        Returns:
            Tuple of (live_stream_id, stream_key, stream_url, playback_id)

        Raises:
            ApiException: If Mux API call fails
        """
        try:
            playback_policy = (
                mux_python.PlaybackPolicy.PUBLIC
                if is_public
                else mux_python.PlaybackPolicy.SIGNED
            )

            # Create live stream request
            create_live_stream_request = mux_python.CreateLiveStreamRequest(
                playback_policy=[playback_policy],
                new_asset_settings=mux_python.CreateAssetRequest(
                    playback_policy=[playback_policy]
                ),
                reduced_latency=True,
            )

            # Create the live stream
            live_stream = self.live_streams_api.create_live_stream(
                create_live_stream_request
            )

            stream_id = live_stream.data.id
            stream_key = live_stream.data.stream_key


            # Get playback ID
            playback_id = None
            if live_stream.data.playback_ids:
                playback_id = live_stream.data.playback_ids[0].id

            logger.info(f"Created Mux live stream: {stream_id}")

            return stream_id, stream_key, self.stream_url, playback_id

        except ApiException as e:
            logger.error(f"Failed to create Mux live stream: {e}")
            raise

    def get_live_stream(self, stream_id: str) -> MuxStreamDetail:
        """
        Get live stream details from Mux

        Args:
            stream_id: Mux live stream ID

        Returns:
            Live stream details as dict

        Raises:
            ApiException: If Mux API call fails
        """
        try:
            live_stream = self.live_streams_api.get_live_stream(stream_id)
            return MuxStreamDetail(
                id=live_stream.data.id,
                status=live_stream.data.status,
                stream_key=live_stream.data.stream_key,
                playback_ids=[
                    {"id": pid.id, "policy": pid.policy}
                    for pid in live_stream.data.playback_ids or []
                ],
                stream_url=self.stream_url,
            )
        except ApiException as e:
            logger.error(f"Failed to get live stream {stream_id}: {e}")
            raise

    def delete_live_stream(self, stream_id: str) -> None:
        """
        Delete a live stream from Mux

        Args:
            stream_id: Mux live stream ID

        Raises:
            ApiException: If Mux API call fails
        """
        try:
            self.live_streams_api.delete_live_stream(stream_id)
            logger.info(f"Deleted Mux live stream: {stream_id}")
        except ApiException as e:
            logger.error(f"Failed to delete live stream {stream_id}: {e}")
            raise

    def generate_signed_playback_url(
        self,
        playback_id: str,
        user_id: Optional[str] = None,
        expire_minutes: Optional[int] = None,
    ) -> Tuple[str, str, datetime]:
        """
        Generate a signed playback URL for private streams

        Args:
            playback_id: Mux playback ID
            user_id: User ID for tracking (optional)
            expire_minutes: Token expiry in minutes (defaults to STREAM_TOKEN_EXPIRE_MINUTES)

        Returns:
            Tuple of (token, signed_url, expiration_time)

        Raises:
            ValueError: If signing key configuration is missing
        """
        if not settings.MUX_SIGNING_KEY_ID or not settings.MUX_SIGNING_KEY_PRIVATE:
            raise ValueError("Mux signing key configuration is missing")

        # Calculate expiration time
        if expire_minutes is None:
            expire_minutes = settings.STREAM_TOKEN_EXPIRE_MINUTES

        expiration = datetime.now() + timedelta(minutes=expire_minutes)
        exp_timestamp = int(expiration.timestamp())

        # Build JWT payload
        payload = {
            "sub": playback_id,
            "aud": "v",  # 'v' for video, 't' for thumbnail
            "exp": exp_timestamp,
            "kid": settings.MUX_SIGNING_KEY_ID,
        }

        # Add user_id for tracking if provided
        if user_id:
            payload["uid"] = str(user_id)

        # Decode base64 private key from Mux
        # Mux signing keys are base64-encoded RSA private keys
        try:
            private_key = base64.b64decode(settings.MUX_SIGNING_KEY_PRIVATE)
        except Exception:
            # If already in PEM format, use as-is
            private_key = settings.MUX_SIGNING_KEY_PRIVATE

        # Sign the JWT
        token = jwt.encode(payload, private_key, algorithm="RS256")

        # Build the signed URL
        signed_url = f"https://stream.mux.com/{playback_id}.m3u8?token={token}"

        logger.info(
            f"Generated signed URL for playback {playback_id}, expires at {expiration}"
        )

        return token, signed_url, expiration

    def generate_signed_thumbnail_url(
        self,
        playback_id: str,
        expire_minutes: Optional[int] = None,
        width: int = 1920,
        height: int = 1080,
        fit_mode: str = "smartcrop",
    ) -> Tuple[str, str, datetime]:
        """
        Generate a signed thumbnail URL for private streams

        Args:
            playback_id: Mux playback ID
            expire_minutes: Token expiry in minutes
            width: Thumbnail width
            height: Thumbnail height
            fit_mode: Fit mode (smartcrop, preserve, crop, pad)

        Returns:
            Tuple of (token, signed_url, expiration_time)

        Raises:
            ValueError: If signing key configuration is missing
        """
        if not settings.MUX_SIGNING_KEY_ID or not settings.MUX_SIGNING_KEY_PRIVATE:
            raise ValueError("Mux signing key configuration is missing")

        # Calculate expiration time
        if expire_minutes is None:
            expire_minutes = settings.STREAM_TOKEN_EXPIRE_MINUTES

        expiration = datetime.now() + timedelta(minutes=expire_minutes)
        exp_timestamp = int(expiration.timestamp())

        payload = {
            "sub": playback_id,
            "aud": "t",  # 't' for thumbnail
            "exp": exp_timestamp,
            "kid": settings.MUX_SIGNING_KEY_ID
        }

        # Decode base64 private key from Mux
        try:
            private_key = base64.b64decode(settings.MUX_SIGNING_KEY_PRIVATE)
        except Exception:
            # If already in PEM format, use as-is
            private_key = settings.MUX_SIGNING_KEY_PRIVATE

        token = jwt.encode(payload, private_key, algorithm="RS256")

        signed_url = f"https://image.mux.com/{playback_id}/thumbnail.jpg?token={token}&width={width}&height={height}&fit_mode={fit_mode}"

        return token, signed_url, expiration

    def get_public_playback_url(self, playback_id: str) -> str:
        """
        Get public playback URL (HLS manifest)

        Args:
            playback_id: Mux playback ID

        Returns:
            Public playback URL
        """
        return f"https://stream.mux.com/{playback_id}.m3u8"

    def get_public_thumbnail_url(
        self,
        playback_id: str,
        width: int = 1920,
        height: int = 1080,
        fit_mode: str = "smartcrop",
    ) -> str:
        """
        Get public thumbnail URL

        Args:
            playback_id: Mux playback ID
            width: Thumbnail width
            height: Thumbnail height
            fit_mode: Fit mode

        Returns:
            Public thumbnail URL
        """
        return f"https://image.mux.com/{playback_id}/thumbnail.jpg?width={width}&height={height}&fit_mode={fit_mode}"

    def verify_webhook_signature(
        self, payload: bytes, signature: str, timestamp: str
    ) -> bool:
        """
        Verify Mux webhook signature

        Args:
            payload: Raw webhook payload
            signature: Signature from Mux-Signature header
            timestamp: Timestamp from Mux-Signature header

        Returns:
            True if signature is valid, False otherwise
        """
        if not settings.MUX_WEBHOOK_SECRET:
            logger.warning("MUX_WEBHOOK_SECRET not configured, skipping verification")
            return True

        try:
            # Extract timestamp and signatures
            # Format: t=timestamp,v1=signature1,v1=signature2,...
            parts = signature.split(",")
            ts = None
            signatures = []

            for part in parts:
                if part.startswith("t="):
                    ts = part.split("=")[1]
                elif part.startswith("v1="):
                    signatures.append(part.split("=")[1])

            if not ts or not signatures:
                logger.error("Invalid signature format")
                return False

            # Check timestamp (prevent replay attacks)
            current_time = int(time.time())
            if abs(current_time - int(ts)) > 300:  # 5 minutes tolerance
                logger.error("Webhook timestamp too old")
                return False

            # Compute expected signature
            signed_payload = f"{ts}.{payload.decode('utf-8')}"
            expected_signature = hmac.new(
                settings.MUX_WEBHOOK_SECRET.encode(),
                signed_payload.encode(),
                hashlib.sha256,
            ).hexdigest()

            # Compare signatures (constant-time comparison)
            for sig in signatures:
                if hmac.compare_digest(expected_signature, sig):
                    return True

            logger.error("Webhook signature mismatch")
            return False

        except Exception as e:
            logger.error(f"Failed to verify webhook signature: {e}")
            return False


mux_service = MuxService()

from datetime import datetime, timedelta
import traceback
import httpx
from typing import Dict, Any, Optional

from pytz import timezone

from core.log import logger
from models.Ticket import Ticket
from settings import FRONTEND_BASE_URL, MAYAR_PAYMENT_EXPIRE_HOURS, TZ


class MayarService:
    def __init__(self, api_key: str, base_url: str = "https://api.mayar.id"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def create_payment(
        self,
        ticket: Ticket,
        customer_email: str,
        customer_name: str,
        customer_phone: str = "",
        tx_internal_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Make a new payment on Mayar.

        Args:
            ticket: Ticket object containing ticket details
            customer_email: Customer email
            customer_name: Customer name
            expiredAt: Payment expiration time
            customer_phone: Customer phone number (optional)
            tx_internal_id: Internal transaction ID for tracking (optional)

        Returns:
            Dict contains responses from the Mayar API in the following format:
            {
                "statusCode": 200,
                "messages": "success",
                "data": {
                    "id": "e890d24a-cfc0-4915-83d2-3166b9ffba9e",
                    "transactionId": "040d5adb-1496-45de-8435-5cab16526a8c",
                    "link": "https://andiak.myr.id/invoices/ohsjrd3wko"
                }
            }

        Raises:
            httpx.HTTPError: If the request fails
        """
        endpoint = f"{self.base_url}/v1/invoice/create"
        redirect_url = (
            f"{FRONTEND_BASE_URL}/payment/{tx_internal_id if tx_internal_id else ''}"
        )
        expired_at = datetime.now(tz=timezone(TZ)) + timedelta(
            hours=MAYAR_PAYMENT_EXPIRE_HOURS
        )

        items = [
            {
                "quantity": 1,
                "rate": ticket.price,
                "description": ticket.name,
            }
        ]
        description = ticket.description if ticket.description else ticket.name

        payload = {
            "name": customer_name,
            "email": customer_email,
            "mobile": customer_phone,
            "description": description,
            "redirectUrl": redirect_url,
            "expiredAt": expired_at.isoformat(),
            "items": items,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()

                logger.info(f"Payment created successfully: {result}")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Mayar API returned error {e.response.status_code}: {e.response.text}"
            )
            logger.debug(f"Request URL: {e.request.url}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request to Mayar failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during payment creation: {repr(e)}")
            logger.debug(traceback.format_exc())
            raise

    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Checking payment status from Mayar.

        Args:
            payment_id: Payment ID from Mayar

        Returns:
            The dictionary contains payment information, including the current status.

        Raises:
            httpx.HTTPError: If the request fails
        """
        endpoint = f"{self.base_url}/v1/invoice/{payment_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()

                logger.info(f"Payment status retrieved: {result}")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Mayar API returned error {e.response.status_code}: {e.response.text}"
            )
            logger.debug(f"Request URL: {e.request.url}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request to Mayar failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during payment status retrieval: {repr(e)}")
            logger.debug(traceback.format_exc())
            raise

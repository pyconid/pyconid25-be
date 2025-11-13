from unittest.mock import patch, MagicMock, AsyncMock
import alembic.config
from unittest import IsolatedAsyncioTestCase
import uuid
from datetime import datetime, timedelta
from pytz import timezone

from fastapi.testclient import TestClient
from models import engine, db, get_db_sync, get_db_sync_for_test
from models.User import User
from models.Ticket import Ticket
from models.Payment import PaymentStatus
from models.Token import Token
from models.Voucher import Voucher
from core.security import generate_hash_password
from repository import payment as paymentRepo
from main import app
from settings import TZ, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
import jwt


class TestPayment(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        alembic_args = ["upgrade", "head"]
        alembic.config.main(argv=alembic_args)
        # connect to the database
        self.connection = engine.connect()

        # begin a non-ORM transaction
        self.trans = self.connection.begin()

        # bind an individual Session to the connection, selecting
        # "create_savepoint" join_transaction_mode
        self.db = db(bind=self.connection, join_transaction_mode="create_savepoint")

        # Create test user
        self.test_user = User(
            username="paymentuser",
            email="payment@example.com",
            phone="+628123456789",
            first_name="test",
            last_name="user",
            password=generate_hash_password("password"),
            is_active=True,
        )
        self.db.add(self.test_user)
        self.db.commit()

        # Create test token manually
        expire = datetime.now(tz=timezone(TZ)) + timedelta(
            minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload = {
            "id": str(self.test_user.id),
            "username": self.test_user.username,
            "exp": expire,
        }
        token_str = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        test_token_model = Token(
            user_id=self.test_user.id, token=token_str, expired_at=expire
        )
        self.db.add(test_token_model)
        self.db.commit()
        self.test_token = token_str

        # Create test ticket
        self.test_ticket = Ticket(
            id=uuid.uuid4(),
            name="Test Conference Ticket",
            price=500000,
            user_participant_type="In Person",
            is_sold_out=False,
            is_active=True,
            description="Test ticket for payment",
        )
        self.db.add(self.test_ticket)
        self.db.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        self.client = TestClient(app)

    async def test_create_payment_success(self):
        mock_mayar_response = {
            "statusCode": 200,
            "messages": "success",
            "data": {
                "id": "mayar-id-123",
                "transactionId": "mayar-tx-456",
                "link": "https://mayar.id/pay/test-link",
            },
        }

        with patch("routes.payment.MayarService") as MockMayarService:
            mock_service = MagicMock()
            mock_service.create_payment = AsyncMock(return_value=mock_mayar_response)
            MockMayarService.return_value = mock_service

            response = self.client.post(
                "/payment/",
                json={"ticket_id": str(self.test_ticket.id)},
                headers={"Authorization": f"Bearer {self.test_token}"},
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()

            self.assertIn("id", data)
            self.assertIn("payment_link", data)
            self.assertEqual(data["payment_link"], "https://mayar.id/pay/test-link")
            self.assertEqual(data["amount"], 500000)
            self.assertEqual(data["ticket"]["name"], "Test Conference Ticket")

            mock_service.create_payment.assert_called_once()

    async def test_create_payment_unauthorized(self):
        response = self.client.post(
            "/payment/",
            json={"ticket_id": str(self.test_ticket.id)},
        )

        self.assertEqual(response.status_code, 401)

    async def test_create_payment_without_email(self):
        user_no_email = User(
            username="noemail",
            password=generate_hash_password("password"),
            phone="+628123456789",
            is_active=True,
        )
        self.db.add(user_no_email)
        self.db.commit()

        self.db.commit()

        # Create token
        expire = datetime.now(tz=timezone(TZ)) + timedelta(
            minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload = {
            "id": str(user_no_email.id),
            "username": user_no_email.username,
            "exp": expire,
        }
        token_no_email = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        token_model = Token(
            user_id=user_no_email.id, token=token_no_email, expired_at=expire
        )
        self.db.add(token_model)
        self.db.commit()

        response = self.client.post(
            "/payment/",
            json={"ticket_id": str(self.test_ticket.id)},
            headers={"Authorization": f"Bearer {token_no_email}"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("email", data["message"].lower())

    async def test_create_payment_without_phone(self):
        user_no_phone = User(
            username="nophone",
            email="nophone@example.com",
            password=generate_hash_password("password"),
            is_active=True,
        )
        self.db.add(user_no_phone)
        self.db.commit()

        self.db.commit()

        # Create token
        expire = datetime.now(tz=timezone(TZ)) + timedelta(
            minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload = {
            "id": str(user_no_phone.id),
            "username": user_no_phone.username,
            "exp": expire,
        }
        token_no_phone = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        token_model = Token(
            user_id=user_no_phone.id, token=token_no_phone, expired_at=expire
        )
        self.db.add(token_model)
        self.db.commit()

        response = self.client.post(
            "/payment/",
            json={"ticket_id": str(self.test_ticket.id)},
            headers={"Authorization": f"Bearer {token_no_phone}"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("phone", data["message"].lower())

    async def test_create_payment_ticket_not_found(self):
        response = self.client.post(
            "/payment/",
            json={"ticket_id": str(uuid.uuid4())},
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["message"], "Ticket not found.")

    async def test_create_payment_ticket_sold_out(self):
        sold_out_ticket = Ticket(
            id=uuid.uuid4(),
            name="Sold Out Ticket",
            price=100000,
            user_participant_type="In Person",
            is_sold_out=True,
            is_active=True,
            description="This ticket is sold out",
        )
        self.db.add(sold_out_ticket)
        self.db.commit()

        response = self.client.post(
            "/payment/",
            json={"ticket_id": str(sold_out_ticket.id)},
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["message"], "Ticket is sold out.")

    async def test_create_payment_mayar_service_error(self):
        with patch("routes.payment.MayarService") as MockMayarService:
            mock_service = MagicMock()
            mock_service.create_payment = AsyncMock(
                side_effect=Exception("Mayar API error")
            )
            MockMayarService.return_value = mock_service

            response = self.client.post(
                "/payment/",
                json={"ticket_id": str(self.test_ticket.id)},
                headers={"Authorization": f"Bearer {self.test_token}"},
            )

            self.assertEqual(response.status_code, 500)
            data = response.json()
            self.assertIn("detail", data)

    async def test_list_payments(self):
        paymentRepo.create_payment(
            db=self.db,
            user_id=str(self.test_user.id),
            ticket_id=str(self.test_ticket.id),
            payment_link="https://mayar.id/pay/link1",
            amount=500000,
            description="Payment 1",
            status=PaymentStatus.UNPAID,
            mayar_id="mayar-id-1",
            mayar_transaction_id="mayar-tx-1",
        )
        paymentRepo.create_payment(
            db=self.db,
            user_id=str(self.test_user.id),
            ticket_id=str(self.test_ticket.id),
            payment_link="https://mayar.id/pay/link2",
            amount=500000,
            description="Payment 2",
            status=PaymentStatus.PAID,
            mayar_id="mayar-id-2",
            mayar_transaction_id="mayar-tx-2",
        )

        self.db.commit()

        response = self.client.get(
            "/payment/",
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 2)
        self.assertTrue(
            any(p["status"] == PaymentStatus.UNPAID.value for p in data["results"])
        )
        self.assertTrue(
            any(p["status"] == PaymentStatus.PAID.value for p in data["results"])
        )

    async def test_list_payments_unauthorized(self):
        response = self.client.get("/payment/")

        self.assertEqual(response.status_code, 401)

    async def test_get_payment_detail_success(self):
        payment = paymentRepo.create_payment(
            db=self.db,
            user_id=str(self.test_user.id),
            ticket_id=str(self.test_ticket.id),
            payment_link="https://mayar.id/pay/test",
            amount=500000,
            description="Test payment",
            status=PaymentStatus.UNPAID,
            mayar_id="mayar-id-test",
            mayar_transaction_id="mayar-tx-test",
        )

        self.db.commit()

        mock_mayar_status_response = {
            "statusCode": 200,
            "messages": "success",
            "data": {
                "id": "mayar-id-test",
                "transactionId": "mayar-tx-test",
                "status": "unpaid",
            },
        }

        with (
            patch("routes.payment.MayarService") as MockMayarService,
            patch("repository.payment.get_payment_by_id") as mock_get_payment,
        ):
            mock_service = MagicMock()
            mock_service.get_payment_status = AsyncMock(
                return_value=mock_mayar_status_response
            )
            MockMayarService.return_value = mock_service
            mock_get_payment.return_value = payment

            response = self.client.get(
                f"/payment/{payment.id}",
                headers={"Authorization": f"Bearer {self.test_token}"},
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["id"], str(payment.id))
            self.assertEqual(data["status"], PaymentStatus.UNPAID.value)
            self.assertEqual(data["amount"], 500000)

    async def test_get_payment_detail_with_status_update(self):
        payment = paymentRepo.create_payment(
            db=self.db,
            user_id=str(self.test_user.id),
            ticket_id=str(self.test_ticket.id),
            payment_link="https://mayar.id/pay/test",
            amount=500000,
            description="Test payment",
            status=PaymentStatus.UNPAID,
            mayar_id="mayar-id-test",
            mayar_transaction_id="mayar-tx-test",
        )

        self.db.commit()

        mock_mayar_status_response = {
            "statusCode": 200,
            "messages": "success",
            "data": {
                "id": "mayar-id-test",
                "transactionId": "mayar-tx-test",
                "status": "paid",
            },
        }

        with (
            patch("routes.payment.MayarService") as MockMayarService,
            patch("repository.payment.get_payment_by_id") as mock_get_payment,
        ):
            mock_service = MagicMock()
            mock_service.get_payment_status = AsyncMock(
                return_value=mock_mayar_status_response
            )
            MockMayarService.return_value = mock_service
            mock_get_payment.return_value = payment

            response = self.client.get(
                f"/payment/{payment.id}",
                headers={"Authorization": f"Bearer {self.test_token}"},
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], PaymentStatus.PAID.value)

    async def test_get_payment_detail_not_found(self):
        response = self.client.get(
            f"/payment/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["message"], "Payment not found")

    async def test_get_payment_detail_forbidden(self):
        other_user = User(
            username="otheruser",
            email="other@example.com",
            phone="+628987654321",
            password=generate_hash_password("password"),
            is_active=True,
        )
        self.db.add(other_user)
        self.db.commit()

        payment = paymentRepo.create_payment(
            db=self.db,
            user_id=str(other_user.id),
            ticket_id=str(self.test_ticket.id),
            payment_link="https://mayar.id/pay/test",
            amount=500000,
            description="Other user payment",
            status=PaymentStatus.UNPAID,
        )

        response = self.client.get(
            f"/payment/{payment.id}",
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("access", data["message"].lower())

    async def test_payment_webhook_success(self):
        payment = paymentRepo.create_payment(
            db=self.db,
            user_id=str(self.test_user.id),
            ticket_id=str(self.test_ticket.id),
            payment_link="https://mayar.id/pay/webhook-test",
            amount=500000,
            description="Webhook test payment",
            status=PaymentStatus.UNPAID,
            mayar_id="mayar-webhook-id",
            mayar_transaction_id="mayar-webhook-tx",
        )
        self.db.commit()

        webhook_payload = {
            "event": "payment.received",
            "data": {
                "id": "mayar-webhook-id",
                "transactionId": "mayar-webhook-tx",
                "status": "success",
            },
        }

        with patch("routes.payment.MAYAR_WEBHOOK_SECRET", "test-webhook-secret"):
            response = self.client.post(
                "/payment/webhook",
                json=webhook_payload,
                headers={"x-callback-token": "test-webhook-secret"},
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["message"], "Webhook processed successfully")
            self.assertEqual(payment.status, PaymentStatus.PAID)
            self.assertEqual(
                self.test_user.participant_type, self.test_ticket.user_participant_type
            )

    async def test_payment_webhook_invalid_token(self):
        webhook_payload = {
            "event": "payment.received",
            "data": {"id": "test-id", "status": "success"},
        }

        with patch("routes.payment.MAYAR_WEBHOOK_SECRET", "correct-secret"):
            response = self.client.post(
                "/payment/webhook",
                json=webhook_payload,
                headers={"x-callback-token": "wrong-secret"},
            )

            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertEqual(data["message"], "Invalid request token")

    async def test_payment_webhook_missing_token(self):
        webhook_payload = {
            "event": "payment.received",
            "data": {"id": "test-id", "status": "success"},
        }

        response = self.client.post(
            "/payment/webhook",
            json=webhook_payload,
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["message"], "Missing X-Callback-Token header")

    async def test_payment_webhook_payment_not_found(self):
        webhook_payload = {
            "event": "payment.received",
            "data": {
                "id": "non-existent-id",
                "transactionId": "non-existent-tx",
                "status": "success",
            },
        }

        with patch("routes.payment.MAYAR_WEBHOOK_SECRET", "test-webhook-secret"):
            response = self.client.post(
                "/payment/webhook",
                json=webhook_payload,
                headers={"x-callback-token": "test-webhook-secret"},
            )

            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertEqual(data["message"], "Payment not found")

    async def test_create_payment_with_valid_voucher(self):
        test_voucher = Voucher(
            code="TESTDISCOUNT50K",
            value=50000,
            quota=10,
            is_active=True,
        )
        self.db.add(test_voucher)
        self.db.commit()

        mock_mayar_response = {
            "statusCode": 200,
            "messages": "success",
            "data": {
                "id": "mayar-id-voucher",
                "transactionId": "mayar-tx-voucher",
                "link": "https://mayar.id/pay/test-link-voucher",
            },
        }

        with patch("routes.payment.MayarService") as MockMayarService:
            mock_service = MagicMock()
            mock_service.create_payment = AsyncMock(return_value=mock_mayar_response)
            MockMayarService.return_value = mock_service

            response = self.client.post(
                "/payment/",
                json={
                    "ticket_id": str(self.test_ticket.id),
                    "voucher_code": "TESTDISCOUNT50K",
                },
                headers={"Authorization": f"Bearer {self.test_token}"},
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()

            # Check that amount is reduced by voucher value
            self.assertEqual(data["amount"], 450000)  # 500000 - 50000

            # Check that voucher is in response
            self.assertIsNotNone(data["voucher"])
            self.assertEqual(data["voucher"]["code"], "TESTDISCOUNT50K")
            self.assertEqual(data["voucher"]["value"], 50000)

            # Check that voucher quota is reduced
            self.db.refresh(test_voucher)
            self.assertEqual(test_voucher.quota, 9)

    async def test_create_payment_with_voucher_making_amount_zero(self):
        test_voucher = Voucher(
            code="VOUCHERFREE",
            value=600000,
            quota=5,
            is_active=True,
        )
        self.db.add(test_voucher)
        self.db.commit()

        response = self.client.post(
            "/payment/",
            json={
                "ticket_id": str(self.test_ticket.id),
                "voucher_code": "VOUCHERFREE",
            },
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check that amount is 0
        self.assertEqual(data["amount"], 0)

        # Check that payment_link is None (no mayar transaction)
        self.assertIsNone(data["payment_link"])

        # Check that voucher is in response
        self.assertIsNotNone(data["voucher"])
        self.assertEqual(data["voucher"]["code"], "VOUCHERFREE")
        self.assertEqual(data["voucher"]["value"], 600000)

        # Check that voucher quota is reduced
        self.db.refresh(test_voucher)
        self.assertEqual(test_voucher.quota, 4)

        # Check that user participant type is updated
        self.db.refresh(self.test_user)
        self.assertEqual(
            self.test_user.participant_type, self.test_ticket.user_participant_type
        )

    async def test_create_payment_with_voucher_value_exceeds_price_should_be_zero_not_negative(
        self,
    ):
        # Create a voucher with value much higher than ticket price
        excessive_voucher = Voucher(
            code="EXCESSIVE1000K",
            value=1000000,
            quota=10,
            is_active=True,
        )
        self.db.add(excessive_voucher)
        self.db.commit()

        response = self.client.post(
            "/payment/",
            json={
                "ticket_id": str(self.test_ticket.id),
                "voucher_code": "EXCESSIVE1000K",
            },
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # CRITICAL: Ensure amount is exactly 0, NOT negative
        self.assertEqual(data["amount"], 0)
        self.assertGreaterEqual(data["amount"], 0, "Amount should never be negative")

        # Payment should be completed immediately without Mayar
        self.assertIsNone(data["payment_link"])

        # Verify voucher information
        self.assertIsNotNone(data["voucher"])
        self.assertEqual(data["voucher"]["code"], "EXCESSIVE1000K")
        self.assertEqual(data["voucher"]["value"], 1000000)

    async def test_create_payment_with_voucher_not_found(self):
        response = self.client.post(
            "/payment/",
            json={
                "ticket_id": str(self.test_ticket.id),
                "voucher_code": "NONEXISTENT",
            },
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["message"], "Voucher not found.")

    async def test_create_payment_with_inactive_voucher(self):
        inactive_voucher = Voucher(
            code="INACTIVEVOUCHER",
            value=50000,
            quota=10,
            is_active=False,
        )
        self.db.add(inactive_voucher)
        self.db.commit()

        response = self.client.post(
            "/payment/",
            json={
                "ticket_id": str(self.test_ticket.id),
                "voucher_code": "INACTIVEVOUCHER",
            },
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["message"], "Voucher is not active.")

    async def test_create_payment_with_voucher_quota_exhausted(self):
        exhausted_voucher = Voucher(
            code="EXHAUSTEDVOUCHER",
            value=50000,
            quota=0,
            is_active=True,
        )
        self.db.add(exhausted_voucher)
        self.db.commit()

        response = self.client.post(
            "/payment/",
            json={
                "ticket_id": str(self.test_ticket.id),
                "voucher_code": "EXHAUSTEDVOUCHER",
            },
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["message"], "Voucher quota has been exhausted.")

    async def test_create_payment_with_voucher_email_whitelist_authorized(self):
        whitelist_voucher = Voucher(
            code="WHITELISTVOUCHER",
            value=100000,
            quota=5,
            is_active=True,
            email_whitelist={"emails": ["payment@example.com", "other@example.com"]},
        )
        self.db.add(whitelist_voucher)
        self.db.commit()

        mock_mayar_response = {
            "statusCode": 200,
            "messages": "success",
            "data": {
                "id": "mayar-id-whitelist",
                "transactionId": "mayar-tx-whitelist",
                "link": "https://mayar.id/pay/test-link-whitelist",
            },
        }

        with patch("routes.payment.MayarService") as MockMayarService:
            mock_service = MagicMock()
            mock_service.create_payment = AsyncMock(return_value=mock_mayar_response)
            MockMayarService.return_value = mock_service

            response = self.client.post(
                "/payment/",
                json={
                    "ticket_id": str(self.test_ticket.id),
                    "voucher_code": "WHITELISTVOUCHER",
                },
                headers={"Authorization": f"Bearer {self.test_token}"},
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["amount"], 400000)  # 500000 - 100000

            # Check that voucher is in response
            self.assertIsNotNone(data["voucher"])
            self.assertEqual(data["voucher"]["code"], "WHITELISTVOUCHER")
            self.assertEqual(data["voucher"]["value"], 100000)

    async def test_create_payment_with_voucher_email_whitelist_unauthorized(self):
        whitelist_voucher = Voucher(
            code="RESTRICTEDVOUCHER",
            value=100000,
            quota=5,
            is_active=True,
            email_whitelist={"emails": ["authorized@example.com", "speaker@mail.com"]},
        )
        self.db.add(whitelist_voucher)
        self.db.commit()

        response = self.client.post(
            "/payment/",
            json={
                "ticket_id": str(self.test_ticket.id),
                "voucher_code": "RESTRICTEDVOUCHER",
            },
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["message"], "You are not authorized to use this voucher.")

    async def test_create_payment_with_voucher_participant_type_override(self):
        speaker_voucher = Voucher(
            code="VOUCHERSPEAKER",
            value=500000,
            quota=3,
            type="Speaker",
            is_active=True,
        )
        self.db.add(speaker_voucher)
        self.db.commit()

        response = self.client.post(
            "/payment/",
            json={
                "ticket_id": str(self.test_ticket.id),
                "voucher_code": "VOUCHERSPEAKER",
            },
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check that amount is 0
        self.assertEqual(data["amount"], 0)

        # Check that voucher is in response
        self.assertIsNotNone(data["voucher"])
        self.assertEqual(data["voucher"]["code"], "VOUCHERSPEAKER")
        self.assertEqual(data["voucher"]["value"], 500000)

        # Check that user participant type is Speaker (from voucher), not from ticket
        self.db.refresh(self.test_user)
        self.assertEqual(self.test_user.participant_type, "Speaker")

    async def test_create_payment_with_voucher_exactly_matches_price(self):
        exact_voucher = Voucher(
            code="EXACT500K",
            value=500000,
            quota=5,
            is_active=True,
        )
        self.db.add(exact_voucher)
        self.db.commit()

        response = self.client.post(
            "/payment/",
            json={
                "ticket_id": str(self.test_ticket.id),
                "voucher_code": "EXACT500K",
            },
            headers={"Authorization": f"Bearer {self.test_token}"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Amount should be exactly 0
        self.assertEqual(data["amount"], 0)
        self.assertIsNone(data["payment_link"])

        # Verify voucher
        self.assertIsNotNone(data["voucher"])
        self.assertEqual(data["voucher"]["value"], 500000)

    async def test_create_payment_with_voucher_last_quota(self):
        last_quota_voucher = Voucher(
            code="LASTQUOTA",
            value=100000,
            quota=1,
            is_active=True,
        )
        self.db.add(last_quota_voucher)
        self.db.commit()

        mock_mayar_response = {
            "statusCode": 200,
            "messages": "success",
            "data": {
                "id": "mayar-id-last-quota",
                "transactionId": "mayar-tx-last-quota",
                "link": "https://mayar.id/pay/test-link-last-quota",
            },
        }

        with patch("routes.payment.MayarService") as MockMayarService:
            mock_service = MagicMock()
            mock_service.create_payment = AsyncMock(return_value=mock_mayar_response)
            MockMayarService.return_value = mock_service

            # First request should succeed
            response = self.client.post(
                "/payment/",
                json={
                    "ticket_id": str(self.test_ticket.id),
                    "voucher_code": "LASTQUOTA",
                },
                headers={"Authorization": f"Bearer {self.test_token}"},
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["amount"], 400000)  # 500000 - 100000

            # Verify quota is now 0
            self.db.refresh(last_quota_voucher)
            self.assertEqual(last_quota_voucher.quota, 0)

            # Second request should fail with quota exhausted
            response2 = self.client.post(
                "/payment/",
                json={
                    "ticket_id": str(self.test_ticket.id),
                    "voucher_code": "LASTQUOTA",
                },
                headers={"Authorization": f"Bearer {self.test_token}"},
            )

            self.assertEqual(response2.status_code, 400)
            data2 = response2.json()
            self.assertEqual(data2["message"], "Voucher quota has been exhausted.")

    async def test_create_payment_with_voucher_quota_enforcement(self):
        # Create voucher with quota = 2
        race_voucher = Voucher(
            code="RACEVOUCHER",
            value=100000,
            quota=2,  # Only 2 quota available
            is_active=True,
        )
        self.db.add(race_voucher)
        self.db.commit()

        mock_mayar_response = {
            "statusCode": 200,
            "messages": "success",
            "data": {
                "id": "mayar-id-race",
                "transactionId": "mayar-tx-race",
                "link": "https://mayar.id/pay/test-link-race",
            },
        }

        with patch("routes.payment.MayarService") as MockMayarService:
            mock_service = MagicMock()
            mock_service.create_payment = AsyncMock(return_value=mock_mayar_response)
            MockMayarService.return_value = mock_service

            responses = []

            # Make 4 sequential requests - only first 2 should succeed
            for i in range(4):
                response = self.client.post(
                    "/payment/",
                    json={
                        "ticket_id": str(self.test_ticket.id),
                        "voucher_code": "RACEVOUCHER",
                    },
                    headers={"Authorization": f"Bearer {self.test_token}"},
                )
                responses.append(response)

            # Count successful and failed responses
            success_count = sum(1 for r in responses if r.status_code == 200)
            failed_count = sum(1 for r in responses if r.status_code == 400)

            # CRITICAL: Only first 2 should succeed, last 2 should fail
            self.assertEqual(
                success_count, 2, "Only two requests should succeed with quota=2"
            )
            self.assertEqual(
                failed_count, 2, "Two requests should fail due to quota exhausted"
            )

            # Verify responses are in correct order
            self.assertEqual(
                responses[0].status_code, 200, "First request should succeed"
            )
            self.assertEqual(
                responses[1].status_code, 200, "Second request should succeed"
            )
            self.assertEqual(responses[2].status_code, 400, "Third request should fail")
            self.assertEqual(
                responses[3].status_code, 400, "Fourth request should fail"
            )

            # Verify quota is now 0 (not negative)
            self.db.refresh(race_voucher)
            self.assertEqual(race_voucher.quota, 0, "Quota should be exactly 0")
            self.assertGreaterEqual(
                race_voucher.quota, 0, "Quota should never be negative"
            )

            # Verify error messages for failed requests
            for i in [2, 3]:
                data = responses[i].json()
                self.assertEqual(
                    data["message"],
                    "Voucher quota has been exhausted.",
                    f"Request {i + 1} should have quota exhausted error",
                )

            # Verify successful payments have correct amount
            for i in [0, 1]:
                data = responses[i].json()
                self.assertEqual(
                    data["amount"],
                    400000,  # 500000 - 100000
                    f"Request {i + 1} should have correct discounted amount",
                )

    async def test_payment_webhook_with_voucher_participant_type(self):
        speaker_voucher = Voucher(
            code="WEBHOOKSPEAKER",
            value=200000,
            quota=3,
            type="Keynote Speaker",
            is_active=True,
        )
        self.db.add(speaker_voucher)
        self.db.commit()

        payment = paymentRepo.create_payment(
            db=self.db,
            user_id=str(self.test_user.id),
            ticket_id=str(self.test_ticket.id),
            payment_link="https://mayar.id/pay/webhook-voucher-test",
            amount=300000,
            description="Webhook voucher test payment",
            status=PaymentStatus.UNPAID,
            mayar_id="mayar-webhook-voucher-id",
            mayar_transaction_id="mayar-webhook-voucher-tx",
            voucher_id=str(speaker_voucher.id),
        )
        self.db.commit()

        webhook_payload = {
            "event": "payment.received",
            "data": {
                "id": "mayar-webhook-voucher-id",
                "transactionId": "mayar-webhook-voucher-tx",
                "status": "success",
            },
        }

        with patch("routes.payment.MAYAR_WEBHOOK_SECRET", "test-webhook-secret"):
            response = self.client.post(
                "/payment/webhook",
                json=webhook_payload,
                headers={"x-callback-token": "test-webhook-secret"},
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["message"], "Webhook processed successfully")
            self.assertEqual(payment.status, PaymentStatus.PAID)

            # Check that user participant type is from voucher, not ticket
            self.db.refresh(self.test_user)
            self.assertEqual(self.test_user.participant_type, "Keynote Speaker")

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()

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

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()

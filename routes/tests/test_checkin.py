import uuid
from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase
from schemas.user_profile import ParticipantType, TShirtSize

import alembic.config
import jwt
from fastapi.testclient import TestClient
from pytz import timezone

from core.security import generate_hash_password
from main import app
from models import db, engine, get_db_sync, get_db_sync_for_test
from models.Payment import Payment, PaymentStatus
from models.Ticket import Ticket
from models.Token import Token
from models.User import User
from settings import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY, TZ


class TestCheckIn(IsolatedAsyncioTestCase):
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
            username="checkinuser",
            email="checkinuser@example.com",
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

        self.test_payment = Payment(
            id=uuid.uuid4(),
            user_id=self.test_user.id,
            ticket_id=self.test_ticket.id,
            payment_link="https://mayar.id/pay/test-link",
            status=PaymentStatus.PAID,
            created_at=datetime.now(tz=timezone(TZ)),
            mayar_id="mayar-test-id",
            mayar_transaction_id="mayar-test-tx",
            amount=500000,
            description="Test payment",
        )
        self.db.add(self.test_payment)
        self.db.commit()
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.db.close()
        self.trans.rollback()
        self.connection.close()

    def test_get_user_data_by_payment_id(self):
        """Test successful retrieval of user data by payment ID"""
        response = self.client.get(f"/ticket/checkin/{self.test_payment.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("data", data)
        self.assertEqual(data["data"]["email"], self.test_user.email)
        self.assertEqual(data["data"]["first_name"], self.test_user.first_name)
        self.assertEqual(data["data"]["last_name"], self.test_user.last_name)

    def test_get_user_data_by_payment_id_not_found(self):
        """Test 404 response when payment ID does not exist"""
        non_existent_id = uuid.uuid4()
        response = self.client.get(f"/ticket/checkin/{non_existent_id}")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("message", data)

    def test_get_user_data_by_payment_id_invalid(self):
        """Test response when payment ID format is invalid"""
        response = self.client.get("/ticket/checkin/invalid-uuid-format")
        self.assertIn(response.status_code, [404, 500])

    def test_get_user_data_with_no_tshirt_size(self):
        """Test retrieval when user has no t-shirt size set"""
        response = self.client.get(f"/ticket/checkin/{self.test_payment.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("data", data)
        self.assertIsNone(data["data"].get("t_shirt_size"))

    def test_get_user_data_with_tshirt_size(self):
        """Test retrieval when user has t-shirt size set"""
        self.test_user.t_shirt_size = TShirtSize.L
        self.db.commit()
        response = self.client.get(f"/ticket/checkin/{self.test_payment.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["t_shirt_size"], TShirtSize.L)

    def test_get_user_data_with_attendance_day1(self):
        """Test retrieval when user has checked in for day 1"""
        self.test_user.attendance_day_1 = True
        self.db.commit()
        response = self.client.get(f"/ticket/checkin/{self.test_payment.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["data"]["checked_in_day1"])

    def test_get_user_data_with_attendance_day2(self):
        """Test retrieval when user has checked in for day 2"""
        self.test_user.attendance_day_2 = True
        self.db.commit()
        response = self.client.get(f"/ticket/checkin/{self.test_payment.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["data"]["checked_in_day2"])

    def test_get_user_data_with_participant_type(self):
        """Test retrieval when user has participant type set"""
        self.test_user.participant_type = ParticipantType.IN_PERSON
        self.db.commit()
        response = self.client.get(f"/ticket/checkin/{self.test_payment.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["participant_type"], ParticipantType.IN_PERSON)

    def test_get_user_data_response_structure(self):
        """Test that response contains all required fields"""
        response = self.client.get(f"/ticket/checkin/{self.test_payment.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        required_fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "t_shirt_size",
            "participant_type",
            "checked_in_day1",
            "checked_in_day2",
        ]
        for field in required_fields:
            self.assertIn(field, data["data"])

    def test_get_user_data_with_unpaid_payment(self):
        """Test retrieval with unpaid payment status"""
        unpaid_payment = Payment(
            id=uuid.uuid4(),
            user_id=self.test_user.id,
            ticket_id=self.test_ticket.id,
            payment_link="https://mayar.id/pay/unpaid-link",
            status=PaymentStatus.UNPAID,
            created_at=datetime.now(tz=timezone(TZ)),
            mayar_id="mayar-unpaid-id",
            mayar_transaction_id="mayar-unpaid-tx",
            amount=500000,
            description="Unpaid payment",
        )
        self.db.add(unpaid_payment)
        self.db.commit()
        response = self.client.get(f"/ticket/checkin/{unpaid_payment.id}")
        self.assertEqual(response.status_code, 200)

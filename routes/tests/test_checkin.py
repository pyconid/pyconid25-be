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
from models.User import MANAGEMENT_PARTICIPANT, VOLUNTEER_PARTICIPANT, User
from schemas.checkin import CheckinDayEnum
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
            participant_type="Student",
        )
        self.db.add(self.test_user)
        self.db.commit()

        # Create test token manually for management user
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
        self.test_user_token = token_str

        # Create managemnt user for check-in
        self.management_user = User(
            username="staffuser",
            email="staff@example.com",
            phone="+628123456790",
            first_name="staff",
            last_name="user",
            password=generate_hash_password("password"),
            is_active=True,
            participant_type=MANAGEMENT_PARTICIPANT,
        )
        self.db.add(self.management_user)
        self.db.commit()

        # Create test token manually for management user
        expire = datetime.now(tz=timezone(TZ)) + timedelta(
            minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload = {
            "id": str(self.management_user.id),
            "username": self.management_user.username,
            "exp": expire,
        }
        token_str = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        test_token_model = Token(
            user_id=self.management_user.id, token=token_str, expired_at=expire
        )
        self.db.add(test_token_model)
        self.db.commit()
        self.management_token = token_str

        # Create volunteer user for check-in
        self.volunteer_user = User(
            username="staffuser-volunteer",
            email="staff-volunteer@example.com",
            phone="+628123456790",
            first_name="volunteer",
            last_name="user",
            password=generate_hash_password("password"),
            is_active=True,
            participant_type=VOLUNTEER_PARTICIPANT,
        )
        self.db.add(self.volunteer_user)
        self.db.commit()

        # Create test token manually for management user
        expire = datetime.now(tz=timezone(TZ)) + timedelta(
            minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload = {
            "id": str(self.volunteer_user.id),
            "username": self.volunteer_user.username,
            "exp": expire,
        }
        token_str = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        test_token_model = Token(
            user_id=self.volunteer_user.id, token=token_str, expired_at=expire
        )
        self.db.add(test_token_model)
        self.db.commit()
        self.volunteer_token = token_str

        # Create organizer user for check-in
        self.organizer_user = User(
            username="staffuser-organizer",
            email="staff-organizer@example.com",
            phone="+628123456790",
            first_name="organizer",
            last_name="user",
            password=generate_hash_password("password"),
            is_active=True,
            participant_type=ParticipantType.ORGANIZER,
        )
        self.db.add(self.organizer_user)
        self.db.commit()

        # Create test token manually for management user
        expire = datetime.now(tz=timezone(TZ)) + timedelta(
            minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload = {
            "id": str(self.organizer_user.id),
            "username": self.organizer_user.username,
            "exp": expire,
        }
        token_str = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        test_token_model = Token(
            user_id=self.organizer_user.id, token=token_str, expired_at=expire
        )
        self.db.add(test_token_model)
        self.db.commit()
        self.organizer_token = token_str

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
        self.assertEqual(response.status_code, 404)

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
        print(response.json())
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
        self.test_user.participant_type = ParticipantType.IN_PERSON.value
        self.db.commit()
        response = self.client.get(f"/ticket/checkin/{self.test_payment.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            data["data"]["participant_type"], ParticipantType.IN_PERSON.value
        )

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

    # Check-in Tests
    def test_checkin_user_day1_success(self):
        """Test successful check-in for day 1"""
        response = self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("data", data)
        self.assertTrue(data["data"]["checked_in_day1"])
        self.assertIn("message", data)
        self.assertEqual(data["message"], "User check-in successful")

    def test_checkin_user_day2_success(self):
        """Test successful check-in for day 2"""
        response = self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day2.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("data", data)
        self.assertTrue(data["data"]["checked_in_day2"])

    def test_checkin_user_unauthorized(self):
        """Test check-in with invalid/missing token"""
        response = self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_checkin_user_payment_not_found(self):
        """Test check-in with non-existent payment ID"""
        non_existent_id = uuid.uuid4()
        response = self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(non_existent_id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("No user found", data["message"])

    def test_checkin_user_unpaid_payment(self):
        """Test check-in with unpaid payment"""
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

        response = self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(unpaid_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response.status_code, 402)
        data = response.json()
        self.assertIn("message", data)

    def test_checkin_updates_attendance_timestamp(self):
        """Test that check-in updates the attendance timestamp"""
        response = self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response.status_code, 200)

        # Verify in database
        self.db.refresh(self.test_user)
        self.assertTrue(self.test_user.attendance_day_1)
        self.assertIsNotNone(self.test_user.attendance_day_1_at)
        self.assertEqual(
            self.test_user.attendance_day_1_updated_by, self.management_user.id
        )

    def test_checkin_multiple_days(self):
        """Test check-in for both days"""
        # Check-in day 1
        response1 = self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response1.status_code, 200)

        # Check-in day 2
        response2 = self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day2.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response2.status_code, 200)

        # Verify both days are checked in
        self.db.refresh(self.test_user)
        self.assertTrue(self.test_user.attendance_day_1)
        self.assertTrue(self.test_user.attendance_day_2)

    # Reset Check-in Tests
    def test_reset_checkin_user_day1_success(self):
        """Test successful reset check-in for day 1"""
        # First check-in
        self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )

        # Then reset
        response = self.client.patch(
            "/ticket/checkin/reset",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("data", data)
        self.assertFalse(data["data"]["checked_in_day1"])
        self.assertEqual(data["message"], "Reset user check-in successful")

    def test_reset_checkin_user_day2_success(self):
        """Test successful reset check-in for day 2"""
        # First check-in
        self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day2.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )

        # Then reset
        response = self.client.patch(
            "/ticket/checkin/reset",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day2.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["data"]["checked_in_day2"])

    def test_reset_checkin_user_unauthorized(self):
        """Test reset check-in with invalid/missing token"""
        response = self.client.patch(
            "/ticket/checkin/reset",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_reset_checkin_user_payment_not_found(self):
        """Test reset check-in with non-existent payment ID"""
        non_existent_id = uuid.uuid4()
        response = self.client.patch(
            "/ticket/checkin/reset",
            json={
                "payment_id": str(non_existent_id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("No user found", data["message"])

    def test_reset_checkin_without_prior_checkin(self):
        """Test reset check-in when user hasn't checked in yet"""
        response = self.client.patch(
            "/ticket/checkin/reset",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["data"]["checked_in_day1"])

    def test_reset_checkin_preserves_other_day(self):
        """Test that resetting one day doesn't affect the other day"""
        # Check-in both days
        self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day2.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )

        # Reset day 1
        response = self.client.patch(
            "/ticket/checkin/reset",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["data"]["checked_in_day1"])
        self.assertTrue(data["data"]["checked_in_day2"])

    def test_checkin_updates_staff_user_tracking(self):
        """Test that check-in tracks which staff member performed it"""
        response = self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.management_token}"},
        )
        self.assertEqual(response.status_code, 200)

        # Verify staff user is recorded
        self.db.refresh(self.test_user)
        self.assertEqual(
            self.test_user.attendance_day_1_updated_by, self.management_user.id
        )

    def test_checkin_updates_volunteer_user(self):
        response = self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.volunteer_token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_reset_checkin_volunteer_user(self):
        response = self.client.patch(
            "/ticket/checkin/reset",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.volunteer_token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_checkin_updates_organizer_user(self):
        response = self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.organizer_token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_reset_checkin_organizer_user(self):
        response = self.client.patch(
            "/ticket/checkin/reset",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.organizer_token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_checkin_updates_forbidden_user(self):
        response = self.client.patch(
            "/ticket/checkin",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.test_user_token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_reset_checkin_forbidden_user(self):
        response = self.client.patch(
            "/ticket/checkin/reset",
            json={
                "payment_id": str(self.test_payment.id),
                "day": CheckinDayEnum.day1.value,
            },
            headers={"Authorization": f"Bearer {self.test_user_token}"},
        )
        self.assertEqual(response.status_code, 403)

from unittest.mock import AsyncMock, patch
import alembic.config
from fastapi.testclient import TestClient
from unittest import IsolatedAsyncioTestCase

from sqlalchemy import func, select
from core.security import generate_hash_password, validated_password
from models import engine, db, get_db_sync, get_db_sync_for_test
from main import app
from models.EmailVerification import EmailVerification
from models.ResetPassword import ResetPassword
from models.User import User
from settings import FRONTEND_BASE_URL


class TestAuthEmail(IsolatedAsyncioTestCase):
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

    @patch("routes.auth.send_email_verfication", new_callable=AsyncMock)
    async def test_signup(self, mock_send_email_verfication):
        # Given
        new_user = User(
            username="someuser",
            password=generate_hash_password("password"),
            is_active=True,
        )
        self.db.add(new_user)
        self.db.commit()
        mock_send_email_verfication.return_value = None
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1 - create new verification
        response = client.post(
            "/auth/email/signup/",
            json={
                "username": "testuser",
                "email": "user@local.com",
                "password": "password",
            },
        )

        # Expect 1
        self.assertEqual(response.status_code, 204)
        stmt = select(EmailVerification).where(
            EmailVerification.email == "user@local.com",
            EmailVerification.username == "testuser",
        )
        email_verification = self.db.execute(stmt).scalar()
        self.assertIsNotNone(email_verification)
        self.assertTrue(validated_password(email_verification.password, "password"))
        activation_link = f"{FRONTEND_BASE_URL}/email-verification/?token={email_verification.verification_code}"
        mock_send_email_verfication.assert_called_once_with(
            recipient=email_verification.email, activation_link=activation_link
        )

        # When 2 - Only one verification per email
        response = client.post(
            "/auth/email/signup/",
            json={
                "username": "testuser",
                "email": "user@local.com",
                "password": "new_password",
            },
        )

        # Expect 2
        self.assertEqual(response.status_code, 204)
        stmt = select(func.count(EmailVerification.id)).where(
            EmailVerification.email == "user@local.com",
            EmailVerification.username == "testuser",
        )
        email_verification = self.db.execute(stmt).scalar()
        self.assertEqual(email_verification, 1)
        stmt = select(EmailVerification).where(
            EmailVerification.email == "user@local.com",
            EmailVerification.username == "testuser",
        )
        email_verification = self.db.execute(stmt).scalar()
        self.assertIsNotNone(email_verification)
        self.assertTrue(validated_password(email_verification.password, "new_password"))

        # When 3 - verify email with invalid code
        response = client.get(
            "/auth/email/verified/",
            params={
                "token": "invalid_code",
            },
        )

        # Expect 3
        self.assertEqual(response.status_code, 400)

        # When 4 - verify email with valid code
        response = client.get(
            "/auth/email/verified/",
            params={
                "token": email_verification.verification_code,
            },
        )

        # Expect 4
        self.assertEqual(response.status_code, 200)
        stmt = select(EmailVerification).where(
            EmailVerification.email == "user@local.com",
            EmailVerification.username == "testuser",
        )
        email_verification = self.db.execute(stmt).scalar()
        self.assertIsNone(email_verification)

        # When 5 - login with email
        response = client.post(
            "/auth/email/signin/",
            json={
                "email": "user@local.com",
                "password": "new_password",
            },
        )

        # Expect 5
        self.assertEqual(response.status_code, 200)

    @patch("routes.auth.send_reset_password_email", new_callable=AsyncMock)
    async def test_reset_password(self, mock_send_reset_password_email):
        # Given
        new_user = User(
            username="someuser",
            email="someuser@local.com",
            password=generate_hash_password("password"),
            is_active=True,
        )
        self.db.add(new_user)
        self.db.commit()
        mock_send_reset_password_email.return_value = None
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1 - request reset password with invalid email
        response = client.post(
            "/auth/email/forgot-password/",
            json={
                "email": "invalid_email@local.com",
            },
        )
        # Expect 1
        self.assertEqual(response.status_code, 400)

        # When 2 - request reset password with valid email
        response = client.post(
            "/auth/email/forgot-password/",
            json={
                "email": "someuser@local.com",
            },
        )
        # Expect 2
        self.assertEqual(response.status_code, 200)
        stmt = select(ResetPassword).where(ResetPassword.user == new_user)
        reset_password = self.db.execute(stmt).scalar()
        self.assertIsNotNone(reset_password)
        reset_link = f"{FRONTEND_BASE_URL}/reset-password/?token={reset_password.token}"
        mock_send_reset_password_email.assert_called_once_with(
            recipient=new_user.email, reset_link=reset_link
        )

        # When 3 - reset password with invalid token
        response = client.post(
            "/auth/email/reset-password/",
            json={
                "token": "invalid_token",
                "new_password": "new_password",
            },
        )
        # Expect 3
        self.assertEqual(response.status_code, 400)

        # When 4 - reset password with valid token
        response = client.post(
            "/auth/email/reset-password/",
            json={
                "token": reset_password.token,
                "new_password": "new_password",
            },
        )
        # Expect 4
        self.assertEqual(response.status_code, 200)
        stmt = select(ResetPassword).where(ResetPassword.user == new_user)
        reset_password = self.db.execute(stmt).scalar()
        self.assertIsNone(reset_password)
        self.assertTrue(new_user.password != generate_hash_password("new_password"))

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()

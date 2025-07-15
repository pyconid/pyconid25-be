from unittest.mock import patch
import alembic.config
from unittest import IsolatedAsyncioTestCase

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select
from core.security import generate_hash_password
from models import engine, db, get_db_sync, get_db_sync_for_test
from models.Account import Account
from models.Token import Token
from models.User import User
from main import app


class TestAuth(IsolatedAsyncioTestCase):
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

    async def test_login_then_logout(self):
        # Given
        new_user = User(
            username="testuser",
            password=generate_hash_password("password"),
            is_active=True,
        )
        self.db.add(new_user)
        self.db.commit()
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1
        response = client.post(
            "/auth/login/", json={"username": "testuser", "password": "password"}
        )

        # Expect 1
        self.assertEqual(response.status_code, 200)
        user_id = response.json().get("id", None)
        self.assertEqual(user_id, str(new_user.id))
        token = response.json().get("token", None)
        self.assertIsNotNone(token)
        session = self.db.query(Token).where(Token.user_id == user_id).scalar()
        self.assertIsNotNone(session)

        # When 2
        response = client.post(
            "/auth/login/", json={"username": "testuser", "password": "wrongpassword"}
        )

        # Expect 2
        self.assertEqual(response.status_code, 400)

        # When 3
        response = client.get(
            "/auth/me/",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect 3
        self.assertEqual(response.status_code, 200)

        # When 4
        response = client.post(
            "/auth/logout/",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect 4
        self.assertEqual(response.status_code, 200)
        stmt = select(Token).where(Token.user_id == new_user.id)
        token = self.db.execute(stmt).scalar()
        self.assertIsNone(token)

        # When 5
        response = client.get(
            "/auth/me/",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect 5
        self.assertEqual(response.status_code, 401)

    async def test_github_oauth_flow_new_user(self):
        mock_user = User(
            username="test@example.com",
            password=generate_hash_password(""),
            is_active=True,
        )
        self.db.add(mock_user)
        self.db.flush()

        mock_account = Account(
            user_id=mock_user.id,
            provider="github",
            provider_id="12345",
            provider_email="test@example.com",
            provider_username="testuser",
            provider_name="Test User",
            access_token="github_access_token_123",
            refresh_token="github_refresh_token_456",
        )
        self.db.add(mock_account)
        self.db.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        with patch("core.oauth_service.OAuthService.handle_callback") as mock_callback:
            mock_callback.return_value = {
                "user": mock_user,
                "account": mock_account,
                "is_new_user": True,
                "provider_user_info": {
                    "id": "12345",
                    "username": "testuser",
                    "email": "test@example.com",
                    "name": "Test User",
                    "avatar_url": "https://github.com/avatar.png",
                    "provider": "github",
                },
            }

            response = client.get(
                "/auth/github/callback/?code=auth_code&state=random_state",
                follow_redirects=False,
            )

            self.assertEqual(response.status_code, 307)

            redirect_url = response.headers.get("location", "")
            self.assertIn("token=", redirect_url)
            self.assertIn("refresh_token=", redirect_url)
            self.assertIn("user_id=", redirect_url)
            self.assertIn("is_new_user=true", redirect_url)

            stmt = select(Token).where(Token.user_id == mock_user.id)
            jwt_token = self.db.execute(stmt).scalar()
            self.assertIsNotNone(jwt_token)

            stmt = select(Account).where(Account.user_id == mock_user.id)
            saved_account = self.db.execute(stmt).scalar()
            self.assertIsNotNone(saved_account)
            self.assertEqual(saved_account.access_token, "github_access_token_123")
            self.assertEqual(saved_account.provider, "github")

    async def test_oauth_callback_error_handling(self):
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        response = client.get(
            "/auth/github/callback/?error=access_denied", follow_redirects=False
        )

        self.assertEqual(response.status_code, 307)
        redirect_url = response.headers.get("location", "")
        self.assertIn("error=access_denied", redirect_url)

        response = client.get("/auth/github/callback/", follow_redirects=False)

        self.assertEqual(response.status_code, 307)
        redirect_url = response.headers.get("location", "")
        self.assertIn("error=missing_code", redirect_url)

    async def test_github_verified_endpoint(self):
        user = User(
            username="existing@example.com",
            password=generate_hash_password(""),
            is_active=True,
        )
        self.db.add(user)
        self.db.flush()

        account = Account(
            user_id=user.id,
            provider="github",
            provider_id="54321",
            provider_email="existing@example.com",
            provider_username="existinguser",
            provider_name="Existing User",
        )
        self.db.add(account)
        self.db.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        with patch(
            "core.oauth_service.OAuthService.verify_github_cookie"
        ) as mock_verify:
            mock_verify.return_value = {"user": user, "account": account}

            response = client.post(
                "/auth/github/verified/", json={"github_cookie": "fake_github_cookie"}
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()

            self.assertEqual(data["id"], str(user.id))
            self.assertEqual(data["github_username"], "existinguser")
            self.assertIn("token", data)
            self.assertIn("refresh_token", data)
            self.assertEqual(data["username"], user.username)
            self.assertEqual(data["is_active"], user.is_active)

    async def test_github_verified_invalid_cookie(self):
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        with patch(
            "core.oauth_service.OAuthService.verify_github_cookie"
        ) as mock_verify:
            mock_verify.side_effect = HTTPException(
                status_code=400, detail="Invalid GitHub session"
            )

            response = client.post(
                "/auth/github/verified/", json={"github_cookie": "invalid_cookie"}
            )

            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertEqual(data["message"], "Invalid GitHub session")

    async def test_github_verified_account_not_found(self):
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        with patch(
            "core.oauth_service.OAuthService.verify_github_cookie"
        ) as mock_verify:
            mock_verify.side_effect = HTTPException(
                status_code=400, detail="Account not found"
            )

            response = client.post(
                "/auth/github/verified/",
                json={"github_cookie": "valid_cookie_but_no_account"},
            )

            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertEqual(data["message"], "Account not found")

    async def test_oauth_signin_endpoint(self):
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        with patch("core.oauth_service.OAuthService.initiate_oauth") as mock_initiate:
            mock_initiate.return_value = (
                "https://github.com/login/oauth/authorize?client_id=..."
            )

            response = client.post("/auth/github/signin/")

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("redirect_url", data)
            self.assertTrue(data["redirect_url"].startswith("https://github.com"))

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()

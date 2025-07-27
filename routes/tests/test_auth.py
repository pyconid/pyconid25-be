from unittest.mock import MagicMock, patch
import alembic.config
from unittest import IsolatedAsyncioTestCase

from fastapi.testclient import TestClient
from sqlalchemy import select
from core.security import generate_hash_password
from models import engine, db, get_db_sync, get_db_sync_for_test
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

    async def test_oauth_signin_endpoint(self):
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        with patch(
            "core.oauth_github_service.oauth_github_service.initiate_oauth"
        ) as mock_initiate:
            mock_initiate.return_value = "https://github.com/login/oauth/authorize?client_id=test&redirect_uri=..."

            response = client.post("/auth/github/signin/")

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("redirect", data)
            self.assertTrue(data["redirect"].startswith("https://github.com"))

    async def test_oauth_verified_endpoint_new_user(self):
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        mock_oauth_client = MagicMock()

        async def mock_authorize_access_token(request):
            return {
                "access_token": "github_access_token_123",
                "refresh_token": "github_refresh_token_456",
                "token_type": "bearer",
                "scope": "user:email",
            }

        mock_oauth_client.authorize_access_token = mock_authorize_access_token

        mock_user_response = MagicMock()
        mock_user_response.json.return_value = {
            "id": 12345,
            "login": "testuser",
            "email": "test@example.com",
            "name": "Test User",
        }

        mock_emails_response = MagicMock()
        mock_emails_response.status_code = 200
        mock_emails_response.json.return_value = [
            {"email": "test@example.com", "primary": True, "verified": True}
        ]

        async def mock_get(url, token=None):
            if "user/emails" in url:
                return mock_emails_response
            return mock_user_response

        mock_oauth_client.get = mock_get

        mock_oauth = MagicMock()
        mock_oauth.github = mock_oauth_client

        with patch("core.oauth_github_service.oauth_github_service.oauth", mock_oauth):
            response = client.post(
                "/auth/github/verified/?code=auth_code&state=random_state"
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()

            self.assertIn("token", data)
            self.assertIn("refresh_token", data)
            self.assertIn("id", data)
            self.assertEqual(data["username"], "testuser")
            self.assertTrue(data["is_new_user"])
            self.assertEqual(data["github_username"], "testuser")

            stmt = select(User).where(User.username == "testuser")
            created_user = self.db.execute(stmt).scalar()
            self.assertIsNotNone(created_user)
            self.assertTrue(created_user.is_active)
            self.assertEqual(created_user.github_username, "testuser")
            self.assertEqual(created_user.github_id, "12345")

    async def test_oauth_verified_endpoint_existing_user(self):
        existing_user = User(
            username="existing@example.com",
            password=generate_hash_password(""),
            github_id="54321",
            github_username="existinguser",
            is_active=True,
        )
        self.db.add(existing_user)
        self.db.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        mock_oauth_client = MagicMock()

        async def mock_authorize_access_token(request):
            return {
                "access_token": "new_github_access_token",
                "refresh_token": "new_github_refresh_token",
                "token_type": "bearer",
                "scope": "user:email",
            }

        mock_oauth_client.authorize_access_token = mock_authorize_access_token

        mock_user_response = MagicMock()
        mock_user_response.json.return_value = {
            "id": 54321,
            "login": "existinguser",
            "email": "existing@example.com",
            "name": "Updated Name",
        }

        mock_emails_response = MagicMock()
        mock_emails_response.status_code = 200
        mock_emails_response.json.return_value = [
            {"email": "existing@example.com", "primary": True, "verified": True}
        ]

        async def mock_get(url, token=None):
            if "user/emails" in url:
                return mock_emails_response
            return mock_user_response

        mock_oauth_client.get = mock_get

        mock_oauth = MagicMock()
        mock_oauth.github = mock_oauth_client

        with patch("core.oauth_github_service.oauth_github_service.oauth", mock_oauth):
            response = client.post(
                "/auth/github/verified/?code=auth_code&state=random_state"
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()

            self.assertIn("token", data)
            self.assertIn("refresh_token", data)
            self.assertEqual(data["id"], str(existing_user.id))
            self.assertEqual(data["username"], "existing@example.com")
            self.assertFalse(data["is_new_user"])
            self.assertEqual(data["github_username"], "existinguser")

    async def test_oauth_verified_missing_code(self):
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        response = client.post("/auth/github/verified/")

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["message"], "Code not found")

    async def test_oauth_verified_token_exchange_failure(self):
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        mock_oauth_client = MagicMock()

        async def mock_authorize_access_token_fail(request):
            raise Exception("Token exchange failed")

        mock_oauth_client.authorize_access_token = mock_authorize_access_token_fail

        mock_oauth = MagicMock()
        mock_oauth.github = mock_oauth_client

        with patch("core.oauth_github_service.oauth_github_service.oauth", mock_oauth):
            response = client.post(
                "/auth/github/verified/?code=invalid_code&state=random_state"
            )

            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertIn(
                "OAuth verification for github failed: Token exchange failed",
                str(data["message"]),
            )

    async def test_oauth_verified_user_info_fetch_failure(self):
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        mock_oauth_client = MagicMock()

        async def mock_authorize_access_token(request):
            return {"access_token": "github_access_token_123", "token_type": "bearer"}

        mock_oauth_client.authorize_access_token = mock_authorize_access_token

        async def mock_get_fail(url, token=None):
            mock_response = MagicMock()
            mock_response.json.side_effect = Exception("API Error")
            return mock_response

        mock_oauth_client.get = mock_get_fail

        mock_oauth = MagicMock()
        mock_oauth.github = mock_oauth_client

        with patch("core.oauth_github_service.oauth_github_service.oauth", mock_oauth):
            response = client.post(
                "/auth/github/verified/?code=auth_code&state=random_state"
            )

            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertIn(
                "OAuth verification for github failed: API Error",
                str(data["message"]),
            )

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()

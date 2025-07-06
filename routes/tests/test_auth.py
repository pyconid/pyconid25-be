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

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()

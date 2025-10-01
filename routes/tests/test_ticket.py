from fastapi.testclient import TestClient
from models import engine, db, get_db_sync, get_db_sync_for_test
from models.Ticket import Ticket
from main import app
import alembic.config
import uuid
from unittest import TestCase


class TestTicket(TestCase):
    @classmethod
    def setUpClass(cls):
        alembic_args = ["upgrade", "head"]
        alembic.config.main(argv=alembic_args)

    def setUp(self):
        self.connection = engine.connect()
        self.trans = self.connection.begin()
        self.session = db(
            bind=self.connection, join_transaction_mode="create_savepoint"
        )

        ticket = Ticket(
            id=uuid.uuid4(),
            name="Test Ticket",
            price=123456,
            user_participant_type="In Person",
            is_sold_out=False,
            is_active=True,
            description="Ini deskripsi test ticket",
        )
        self.session.add(ticket)
        self.session.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.session)
        self.client = TestClient(app)

    def tearDown(self):
        self.session.close()
        self.trans.rollback()
        self.connection.close()

    def test_list_ticket(self):
        response = self.client.get("/ticket/")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert any(
            t["name"] == "Test Ticket"
            and t.get("description") == "Ini deskripsi test ticket"
            for t in data["results"]
        )

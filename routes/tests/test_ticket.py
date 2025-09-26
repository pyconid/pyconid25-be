from fastapi.testclient import TestClient
from models import engine, db, get_db_sync, get_db_sync_for_test
from models.Ticket import Ticket
from main import app
import alembic.config
import uuid


def setup_module(module):
    alembic_args = ["upgrade", "head"]
    alembic.config.main(argv=alembic_args)


def test_list_ticket():
    connection = engine.connect()
    trans = connection.begin()
    session = db(bind=connection, join_transaction_mode="create_savepoint")

    ticket = Ticket(
        id=uuid.uuid4(),
        name="Test Ticket",
        price=123456,
        user_participant_type="In Person",
        is_sold_out=False,
        is_active=True,
    )
    session.add(ticket)
    session.commit()

    app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=session)
    client = TestClient(app)

    # Test endpoint
    response = client.get("/ticket/")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert any(t["name"] == "Test Ticket" for t in data["results"])

    # Cleanup
    session.close()
    trans.rollback()
    connection.close()

import alembic.config
from unittest import IsolatedAsyncioTestCase

from fastapi.testclient import TestClient
from models import engine, db, get_db_sync, get_db_sync_for_test
from models.OrganizerType import OrganizerType
from main import app
from schemas.organizer_type import OrganizerTypeAllResponse, organizer_type_all_response_from_models


class TestOrganizerType(IsolatedAsyncioTestCase):
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

    async def test_get_organizer_type_all(self):
        # Given
        ot1 = OrganizerType(name="Committee Member")
        self.db.add(ot1)
        ot2 = OrganizerType(name="Volunteer")
        self.db.add(ot2)
        self.db.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.get("/organizer-type/")
        data = response.json()

        # Then
        self.assertDictEqual(
            data,
            organizer_type_all_response_from_models([ot1, ot2]).model_dump(),
        )

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()
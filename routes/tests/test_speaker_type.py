import alembic.config
from unittest import IsolatedAsyncioTestCase

from fastapi.testclient import TestClient
from models import engine, db, get_db_sync, get_db_sync_for_test
from models.SpeakerType import SpeakerType
from main import app
from schemas.speaker_type import SpeakerTypeAllResponse


class TestSpeakerType(IsolatedAsyncioTestCase):
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

    async def test_get_speaker_type_all(self):
        # Given
        st1 = SpeakerType(name="Keynote Speaker")
        self.db.add(st1)
        st2 = SpeakerType(name="Regular Speaker")
        self.db.add(st2)
        self.db.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.get("/speaker-type/")
        data = response.json()

        # Then
        self.assertDictEqual(
            data,
            SpeakerTypeAllResponse(
                results=[
                    SpeakerTypeAllResponse.SpeakerTypeItem(
                        id=str(speaker_type.id), name=speaker_type.name
                    )
                    for speaker_type in [st1, st2]
                ]
            ).model_dump(),
        )

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()

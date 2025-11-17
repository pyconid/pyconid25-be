import alembic.config
from unittest import IsolatedAsyncioTestCase

from fastapi.testclient import TestClient
from pytz import timezone
from sqlalchemy import select
from core.security import generate_token_from_user
from models import engine, db, get_db_sync, get_db_sync_for_test
from models.Speaker import Speaker
from models.SpeakerType import SpeakerType
from models.User import MANAGEMENT_PARTICIPANT, User
from main import app
from schemas.speaker import SpeakerDetailResponse


class TestSpeaker(IsolatedAsyncioTestCase):
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

    async def test_get_speaker_by_id(self):
        # Given
        user_management = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="admin",
            participant_type=MANAGEMENT_PARTICIPANT,
        )
        user_non_management = User(
            id="019a8bcd-d8d9-7e2a-8ca4-3aedfd1270a1",
            username="admin",
            participant_type=None,
        )
        st = SpeakerType(name="Keynote Speaker")
        self.db.add(st)
        speaker = Speaker(
            id="123e4567-e89b-12d3-a456-426614174000",
            name="John Doe",
            bio="A keynote speaker",
            photo_url="http://example.com/photo.jpg",
            email="John@gmail.com",
            instagram_link="http://instagram.com/johndoe",
            x_link="http://x.com/johndoe",
            speaker_type=st,
        )
        self.db.add(speaker)
        self.db.commit()
        (token, _) = await generate_token_from_user(db=self.db, user=user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1
        response = client.get(
            f"/speaker/{speaker.id}", headers={"Authorization": f"Bearer {token}"}
        )

        # Expect 1
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            SpeakerDetailResponse(
                id=str(speaker.id),
                name=speaker.name,
                bio=speaker.bio,
                photo_url=speaker.photo_url,
                email=speaker.email,
                instagram_link=speaker.instagram_link,
                x_link=speaker.x_link,
                created_at=speaker.created_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=speaker.updated_at.astimezone(
                    timezone("Asia/Jakarta")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                speaker_type=SpeakerDetailResponse.DetailSpeakerType(
                    id=str(speaker.speaker_type.id),
                    name=speaker.speaker_type.name,
                )
                if speaker.speaker_type
                else None,
            ).model_dump(),
        )

        # When 2
        (token, _) = await generate_token_from_user(
            db=self.db, user=user_non_management
        )
        response = client.get(
            f"/speaker/{speaker.id}", headers={"Authorization": f"Bearer {token}"}
        )

        # Expect 2
        self.assertEqual(response.status_code, 403)

    async def test_create_speaker_and_get_speaker_photo(self):
        # Given
        user_management = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="admin",
            participant_type=MANAGEMENT_PARTICIPANT,
        )
        user_non_management = User(
            id="019a8bcd-d8d9-7e2a-8ca4-3aedfd1270a1",
            username="admin",
            participant_type=None,
        )
        st = SpeakerType(name="Keynote Speaker")
        self.db.add(st)
        self.db.commit()
        (token, _) = await generate_token_from_user(db=self.db, user=user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1
        response = client.post(
            "/speaker/",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "name": "Jane Doe",
                "bio": "An updated keynote speaker",
                "email": "hello@gmail.com",
                "instagram_link": "http://instagram.com/janedoe",
                "x_link": "http://x.com/janedoe",
                "speaker_type_id": str(st.id),
            },
            files={"photo": open("./routes/tests/data/bandungpy.jpg", "rb")},
        )

        # Expect 1
        self.assertEqual(response.status_code, 200)
        stmt = select(Speaker).where(Speaker.name == "Jane Doe")
        speaker = self.db.execute(stmt).scalar()
        self.assertIsNotNone(speaker)
        self.assertEqual(speaker.name, "Jane Doe")
        self.assertEqual(speaker.bio, "An updated keynote speaker")
        self.assertIsNotNone(speaker.photo_url)
        self.assertEqual(speaker.email, "hello@gmail.com")
        self.assertEqual(speaker.instagram_link, "http://instagram.com/janedoe")
        self.assertEqual(speaker.x_link, "http://x.com/janedoe")
        self.assertEqual(speaker.speaker_type.id, st.id)

        # When 2
        (token, _) = await generate_token_from_user(
            db=self.db, user=user_non_management
        )
        response = client.post(
            "/speaker/",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "name": "Jane Doe",
                "bio": "An updated keynote speaker",
                "email": "hello@gmail.com",
                "instagram_link": "http://instagram.com/janedoe",
                "x_link": "http://x.com/janedoe",
                "speaker_type_id": str(st.id),
            },
            files={"photo": open("./routes/tests/data/bandungpy.jpg", "rb")},
        )

        # Expect 2
        self.assertEqual(response.status_code, 403)

        # When 3
        response = client.get(f"/speaker/photo/{speaker.photo_url}")

        # Expect 3
        self.assertEqual(response.status_code, 200)

    async def test_update_speaker(self):
        # Given
        user_management = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="admin",
            participant_type=MANAGEMENT_PARTICIPANT,
        )
        user_non_management = User(
            id="019a8bcd-d8d9-7e2a-8ca4-3aedfd1270a1",
            username="admin",
            participant_type=None,
        )
        st = SpeakerType(name="Keynote Speaker")
        self.db.add(st)
        speaker = Speaker(
            id="123e4567-e89b-12d3-a456-426614174000",
            name="John Doe",
            bio="A keynote speaker",
            photo_url="http://example.com/photo.jpg",
            email="John@gmail.com",
            instagram_link="http://instagram.com/johndoe",
            x_link="http://x.com/johndoe",
            speaker_type=st,
        )
        self.db.add(speaker)
        self.db.commit()
        (token, _) = await generate_token_from_user(db=self.db, user=user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1
        response = client.put(
            f"/speaker/{speaker.id}",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "name": "Jane Doe",
                "bio": "An updated keynote speaker",
                "email": "hello@gmail.com",
                "instagram_link": "http://instagram.com/janedoe",
                "x_link": "http://x.com/janedoe",
                "speaker_type_id": str(st.id),
            },
            files={"photo": open("./routes/tests/data/bandungpy.jpg", "rb")},
        )

        # Expect 1
        self.assertEqual(response.status_code, 200)
        self.assertEqual(speaker.name, "Jane Doe")
        self.assertEqual(speaker.bio, "An updated keynote speaker")
        self.assertIsNotNone(speaker.photo_url)
        self.assertEqual(speaker.email, "hello@gmail.com")
        self.assertEqual(speaker.instagram_link, "http://instagram.com/janedoe")
        self.assertEqual(speaker.x_link, "http://x.com/janedoe")
        self.assertEqual(speaker.speaker_type.id, st.id)

        # When 2
        (token, _) = await generate_token_from_user(
            db=self.db, user=user_non_management
        )
        response = client.put(
            f"/speaker/{speaker.id}",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "name": "Jane Doe",
                "bio": "An updated keynote speaker",
                "email": "hello@gmail.com",
                "instagram_link": "http://instagram.com/janedoe",
                "x_link": "http://x.com/janedoe",
                "speaker_type_id": str(st.id),
            },
            files={"photo": open("./routes/tests/data/bandungpy.jpg", "rb")},
        )

        # Expect 2
        self.assertEqual(response.status_code, 403)

    async def test_delete_speaker(self):
        # Given
        user_management = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="admin",
            participant_type=MANAGEMENT_PARTICIPANT,
        )
        user_non_management = User(
            id="019a8bcd-d8d9-7e2a-8ca4-3aedfd1270a1",
            username="admin",
            participant_type=None,
        )
        st = SpeakerType(name="Keynote Speaker")
        self.db.add(st)
        speaker_id = "123e4567-e89b-12d3-a456-426614174000"
        speaker = Speaker(
            id=speaker_id,
            name="John Doe",
            bio="A keynote speaker",
            photo_url="http://example.com/photo.jpg",
            email="John@gmail.com",
            instagram_link="http://instagram.com/johndoe",
            x_link="http://x.com/johndoe",
            speaker_type=st,
        )
        self.db.add(speaker)
        self.db.commit()
        (token, _) = await generate_token_from_user(db=self.db, user=user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1
        response = client.delete(
            f"/speaker/{speaker_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect 1
        self.assertEqual(response.status_code, 204)
        stmt = select(Speaker).where(Speaker.id == speaker_id)
        speaker = self.db.execute(stmt).scalar()
        self.assertIsNone(speaker)

        # When 2
        (token, _) = await generate_token_from_user(
            db=self.db, user=user_non_management
        )
        response = client.delete(
            "/speaker/123e4567-e89b-12d3-a456-426614174000",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect 2
        self.assertEqual(response.status_code, 403)

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()

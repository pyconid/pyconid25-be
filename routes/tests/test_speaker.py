import shutil
import uuid
from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase

import alembic.config
from fastapi.testclient import TestClient
from sqlalchemy import select

from core.security import generate_token_from_user
from main import app
from models import db, engine, get_db_sync, get_db_sync_for_test
from models.Room import Room
from models.Schedule import Schedule
from models.ScheduleType import ScheduleType
from models.Speaker import Speaker
from models.SpeakerType import SpeakerType
from models.User import MANAGEMENT_PARTICIPANT, User
from schemas.speaker import SpeakerDetailResponse
from settings import FILE_STORAGE_PATH


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

    async def test_get_all_speaker(self):
        # Given
        user_management = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="admin",
            participant_type=MANAGEMENT_PARTICIPANT,
        )
        self.db.add(user_management)
        st = SpeakerType(name="Keynote Speaker")
        self.db.add(st)
        user_1 = User(
            username="John Doe",
            first_name="John",
            last_name="Doe",
            bio="A keynote speaker",
            profile_picture="http://example.com/photo.jpg",
            email="john@pycon.id",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
        )
        self.db.add(user_1)
        speaker1 = Speaker(
            user=user_1,
            speaker_type=st,
        )
        self.db.add(speaker1)
        self.db.commit()
        user_2 = User(
            username="Jane Doe",
            first_name="Jane",
            last_name="Doe",
            bio="A keynote speaker",
            profile_picture="http://example.com/photo.jpg",
            email="jane@pycon.id",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
        )
        self.db.add(user_1)
        speaker2 = Speaker(
            user=user_2,
            speaker_type=st,
        )
        self.db.add(speaker2)
        self.db.commit()
        (token, _) = await generate_token_from_user(db=self.db, user=user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.get(
            "/speaker/",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect
        self.assertEqual(response.status_code, 200)

    async def test_get_speaker_by_id(self):
        # Given
        user_management = User(
            username="admin",
            participant_type=MANAGEMENT_PARTICIPANT,
        )
        self.db.add(user_management)
        user_non_management = User(
            username="admin",
            participant_type=None,
        )
        self.db.add(user_non_management)
        st = SpeakerType(name="Keynote Speaker")
        self.db.add(st)
        user = User(
            username="John Doe",
            first_name="John",
            last_name="Doe",
            bio="A keynote speaker",
            profile_picture="http://example.com/photo.jpg",
            email="John@gmail.com",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
        )
        self.db.add(user)
        speaker = Speaker(
            user=user,
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
                user=SpeakerDetailResponse.DetailUser(
                    id=str(speaker.user.id),
                    first_name=speaker.user.first_name,
                    last_name=speaker.user.last_name,
                    username=speaker.user.username,
                    bio=speaker.user.bio,
                    profile_picture=speaker.user.profile_picture,
                    email=speaker.user.email,
                    instagram_username=speaker.user.instagram_username,
                    twitter_username=speaker.user.twitter_username,
                ),
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

    async def test_create_speaker(self):
        # Given
        user_management = User(
            username="admin",
            participant_type=MANAGEMENT_PARTICIPANT,
        )
        self.db.add(user_management)
        user_non_management = User(
            username="admin non management",
            participant_type=None,
        )
        self.db.add(user_non_management)
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
            json={
                "user_id": str(user_non_management.id),
                "speaker_type_id": str(st.id),
            },
            # files={"photo": open("./routes/tests/data/bandungpy.jpg", "rb")},
        )

        # Expect 1
        self.assertEqual(response.status_code, 200)
        stmt = select(Speaker).where(Speaker.user_id == user_non_management.id)
        speaker = self.db.execute(stmt).scalar()
        self.assertIsNotNone(speaker)
        self.assertEqual(speaker.speaker_type_id, st.id)

        # When 2
        (token, _) = await generate_token_from_user(
            db=self.db, user=user_non_management
        )
        response = client.post(
            "/speaker/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": str(user_non_management.id),
                "speaker_type_id": str(st.id),
            },
            # files={"photo": open("./routes/tests/data/bandungpy.jpg", "rb")},
        )

        # Expect 2
        self.assertEqual(response.status_code, 403)

    async def test_update_speaker(self):
        # Given
        user_management = User(
            username="admin",
            participant_type=MANAGEMENT_PARTICIPANT,
        )
        self.db.add(user_management)
        user_non_management = User(
            username="admin",
            participant_type=None,
        )
        self.db.add(user_non_management)
        st = SpeakerType(name="Keynote Speaker")
        self.db.add(st)
        user = User(
            username="John Doe",
            first_name="John",
            last_name="Doe",
            bio="A keynote speaker",
            profile_picture="http://example.com/photo.jpg",
            email="John@gmail.com",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
        )
        self.db.add(user)
        speaker = Speaker(
            user=user,
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
            json={
                "user_id": str(user_non_management.id),
                "speaker_type_id": str(st.id),
            },
            # files={"photo": open("./routes/tests/data/bandungpy.jpg", "rb")},
        )

        # Expect 1
        self.assertEqual(response.status_code, 200)
        self.assertEqual(speaker.speaker_type_id, st.id)
        self.assertEqual(speaker.user_id, user_non_management.id)

        # When 2
        (token, _) = await generate_token_from_user(
            db=self.db, user=user_non_management
        )
        response = client.put(
            f"/speaker/{speaker.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": str(user_non_management.id),
                "speaker_type_id": str(st.id),
            },
            # files={"photo": open("./routes/tests/data/bandungpy.jpg", "rb")},
        )

        # Expect 2
        self.assertEqual(response.status_code, 403)

    async def test_delete_speaker(self):
        # Given
        user_management = User(
            username="admin",
            participant_type=MANAGEMENT_PARTICIPANT,
        )
        self.db.add(user_management)
        user_non_management = User(
            username="admin",
            participant_type=None,
        )
        self.db.add(user_non_management)
        st = SpeakerType(name="Keynote Speaker")
        self.db.add(st)
        user = User(
            username="John Doe",
            first_name="John",
            last_name="Doe",
            bio="A keynote speaker",
            profile_picture="http://example.com/photo.jpg",
            email="John@gmail.com",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
        )
        speaker = Speaker(
            id=uuid.uuid4(),
            user=user,
            speaker_type=st,
        )
        self.db.add(speaker)
        self.db.commit()
        (token, _) = await generate_token_from_user(db=self.db, user=user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1
        response = client.delete(
            f"/speaker/{str(speaker.id)}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect 1
        self.assertEqual(response.status_code, 204)
        stmt = select(Speaker).where(Speaker.id == speaker.id)
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

    async def test_get_speaker_profile_picture(self):
        # Given
        user = User(
            username="John Doe",
            first_name="John",
            last_name="Doe",
            bio="A keynote speaker",
            profile_picture=None,
            email="John@gmail.com",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
        )
        st = SpeakerType(name="Keynote Speaker")
        self.db.add(st)
        speaker = Speaker(
            id=uuid.uuid4(),
            user=user,
            speaker_type=st,
        )
        self.db.add(speaker)
        self.db.commit()
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1
        response = client.get(
            f"/speaker/{str(speaker.id)}/profile-picture/",
        )

        # Expect 1
        self.assertEqual(response.status_code, 404)

        # Given 2
        shutil.copyfile(
            "./routes/tests/data/bandungpy.jpg",
            f"./{FILE_STORAGE_PATH}/bandungpy.jpg",
        )
        user.profile_picture = "bandungpy.jpg"
        self.db.add(user)
        self.db.commit()

        # When 2
        response = client.get(
            f"/speaker/{str(speaker.id)}/profile-picture/",
        )

        # Expect 2
        self.assertEqual(response.status_code, 200)

    async def test_get_speaker_public(self):
        # Given: 2 speaker
        st = SpeakerType(name="Public Speaker")
        self.db.add(st)

        user_1 = User(
            username="public_user_1",
            first_name="Alice",
            last_name="Smith",
            bio="Public speaker 1",
            profile_picture="http://example.com/photo1.jpg",
            email="alice@pycon.id",
            instagram_username="http://instagram.com/alice",
            twitter_username="http://x.com/alice",
        )
        self.db.add(user_1)
        speaker1 = Speaker(
            user=user_1,
            speaker_type=st,
        )
        self.db.add(speaker1)

        user_2 = User(
            username="public_user_2",
            first_name="Bob",
            last_name="Jones",
            bio="Public speaker 2",
            profile_picture="http://example.com/photo2.jpg",
            email="bob@pycon.id",
            instagram_username="http://instagram.com/bob",
            twitter_username="http://x.com/bob",
        )
        self.db.add(user_2)
        speaker2 = Speaker(
            user=user_2,
            speaker_type=st,
        )
        self.db.add(speaker2)

        self.db.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.get("/speaker/public")

        # Expect
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertIn("results", body)
        self.assertEqual(len(body["results"]), 2)

        usernames = {s["user"]["username"] for s in body["results"]}
        self.assertSetEqual(usernames, {"public_user_1", "public_user_2"})

    async def test_get_schedule_by_speaker(self):
        # Given
        st = SpeakerType(name="Schedule Speaker")
        self.db.add(st)

        user = User(
            username="schedule_user",
            first_name="Schedule",
            last_name="Speaker",
            bio="Speaker with schedule",
            profile_picture="http://example.com/photo.jpg",
            email="schedule@pycon.id",
            instagram_username="http://instagram.com/schedule",
            twitter_username="http://x.com/schedule",
        )
        self.db.add(user)

        speaker = Speaker(
            id=uuid.uuid4(),
            user=user,
            speaker_type=st,
        )
        self.db.add(speaker)
        self.db.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When: speaker not have schedule
        response = client.get(f"/speaker/{str(speaker.id)}/schedule/")
        self.assertEqual(response.status_code, 404)

        # Given: create schedule for speaker
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        room = Room(name="Main Hall")
        self.db.add(room)
        self.db.flush()

        schedule_type = ScheduleType(name="Talk")
        self.db.add(schedule_type)
        self.db.flush()

        schedule = Schedule(
            id=uuid.uuid4(),
            title="Opening Keynote",
            description="Opening session",
            speaker_id=speaker.id,
            room_id=room.id,
            schedule_type_id=schedule_type.id,
            start=start_time,
            end=end_time,
        )
        self.db.add(schedule)
        self.db.commit()

        response = client.get(f"/speaker/{str(speaker.id)}/schedule/")
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(str(schedule.id), body["id"])
        self.assertEqual(schedule.title, body["title"])

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()

import uuid
import alembic.config
from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from fastapi.testclient import TestClient

from core.security import generate_token_from_user
from models import engine, db, get_db_sync, get_db_sync_for_test
from models.User import MANAGEMENT_PARTICIPANT, User
from models.Speaker import Speaker
from models.SpeakerType import SpeakerType
from models.Room import Room
from models.ScheduleType import ScheduleType
from models.Schedule import Schedule
from models.Stream import Stream, StreamStatus
from main import app


class TestSchedule(IsolatedAsyncioTestCase):
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

        # Create test data
        self.user_management = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="admin",
            participant_type=MANAGEMENT_PARTICIPANT,
        )
        self.db.add(self.user_management)

        self.user_non_management = User(
            username="regular_user",
            participant_type=None,
        )
        self.db.add(self.user_non_management)

        self.speaker_type = SpeakerType(name="Keynote Speaker")
        self.db.add(self.speaker_type)

        self.room = Room(name="Main Hall")
        self.db.add(self.room)

        self.schedule_type = ScheduleType(name="Talk")
        self.db.add(self.schedule_type)

        self.user_speaker = User(
            username="speaker_user",
            first_name="Jane",
            last_name="Doe",
            bio="Expert speaker",
            email="jane@example.com",
            share_my_email_and_phone_number=True,
            share_my_job_and_company=False,
            share_my_public_social_media=False,
        )
        self.db.add(self.user_speaker)

        self.speaker = Speaker(
            user=self.user_speaker,
            speaker_type=self.speaker_type,
        )
        self.db.add(self.speaker)

        self.db.commit()

    @patch("core.mux_service.mux_service.create_live_stream")
    async def test_create_schedule_success(self, mock_create_stream):
        # Given
        mock_create_stream.return_value = (
            "mux_stream_123",
            "stream_key_123",
            "playback_id_123",
        )

        token, _ = await generate_token_from_user(db=self.db, user=self.user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        payload = {
            "title": "Python Best Practices",
            "speaker_id": str(self.speaker.id),
            "room_id": str(self.room.id),
            "schedule_type_id": str(self.schedule_type.id),
            "description": "Learn Python best practices",
            "presentation_language": "English",
            "slide_language": "English",
            "slide_link": "https://slides.example.com",
            "tags": ["python", "best-practices"],
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
        }

        # When
        response = client.post(
            "/schedule/",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["title"], "Python Best Practices")
        self.assertEqual(data["speaker"]["id"], str(self.speaker.id))
        mock_create_stream.assert_called_once_with(is_public=True)

    async def test_create_schedule_unauthorized(self):
        # Given
        token, _ = await generate_token_from_user(
            db=self.db, user=self.user_non_management
        )
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        payload = {
            "title": "Test Schedule",
            "speaker_id": str(self.speaker.id),
            "room_id": str(self.room.id),
            "schedule_type_id": str(self.schedule_type.id),
            "description": "Test",
            "presentation_language": "English",
            "slide_language": "English",
            "tags": [],
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
        }

        # When
        response = client.post(
            "/schedule/",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect
        self.assertEqual(response.status_code, 403)

    async def test_update_schedule_success(self):
        # Given
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        schedule = Schedule(
            title="Original Title",
            speaker_id=self.speaker.id,
            room_id=self.room.id,
            schedule_type_id=self.schedule_type.id,
            description="Original description",
            presentation_language="English",
            slide_language="English",
            tags=["python"],
            start=start_time,
            end=end_time,
        )
        self.db.add(schedule)
        self.db.commit()

        token, _ = await generate_token_from_user(db=self.db, user=self.user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        payload = {
            "title": "Updated Title",
            "room_id": str(self.room.id),
            "speaker_id": str(self.speaker.id),
            "schedule_type_id": str(self.schedule_type.id),
            "description": "Updated description",
            "presentation_language": "English",
            "slide_language": "English",
            "tags": ["python", "update"],
            "start": str(start_time),
            "end": str(end_time),
        }

        # When
        response = client.put(
            f"/schedule/{schedule.id}",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Updated Title")
        self.assertEqual(data["description"], "Updated description")

    async def test_update_schedule_not_found(self):
        # Given
        token, _ = await generate_token_from_user(db=self.db, user=self.user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        non_existent_id = str(uuid.uuid4())
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        payload = {
            "title": "Updated Title",
            "room_id": str(self.room.id),
            "speaker_id": str(self.speaker.id),
            "schedule_type_id": str(self.schedule_type.id),
            "start": str(start_time),
            "end": str(end_time),
        }

        # When
        response = client.put(
            f"/schedule/{non_existent_id}",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        print(response.json())

        # Expect
        self.assertEqual(response.status_code, 404)

    @patch("core.mux_service.mux_service.delete_live_stream")
    async def test_delete_schedule_success(self, mock_delete_stream):
        # Given
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        schedule = Schedule(
            title="Schedule to Delete",
            speaker_id=self.speaker.id,
            room_id=self.room.id,
            schedule_type_id=self.schedule_type.id,
            description="Test description",
            presentation_language="English",
            slide_language="English",
            tags=["python"],
            start=start_time,
            end=end_time,
        )
        self.db.add(schedule)
        self.db.commit()

        stream = Stream(
            schedule_id=schedule.id,
            is_public=True,
            mux_live_stream_id="mux_stream_123",
            mux_playback_id="playback_123",
            mux_stream_key="stream_key_123",
            status=StreamStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(stream)
        self.db.commit()

        token, _ = await generate_token_from_user(db=self.db, user=self.user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.delete(
            f"/schedule/{schedule.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect
        self.assertEqual(response.status_code, 204)
        mock_delete_stream.assert_called_once_with("mux_stream_123")

    async def test_get_schedule_by_id_success(self):
        # Given
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        schedule = Schedule(
            title="Test Schedule",
            speaker_id=self.speaker.id,
            room_id=self.room.id,
            schedule_type_id=self.schedule_type.id,
            description="Test description",
            presentation_language="English",
            slide_language="English",
            tags=["python"],
            start=start_time,
            end=end_time,
        )
        self.db.add(schedule)
        self.db.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.get(f"/schedule/{schedule.id}")

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Test Schedule")
        self.assertEqual(data["speaker"]["user"]["email"], "jane@example.com")
        self.assertIsNone(data["speaker"]["user"]["company"])

    async def test_get_schedule_by_id_not_found(self):
        # Given
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)
        non_existent_id = str(uuid.uuid4())

        # When
        response = client.get(f"/schedule/{non_existent_id}")

        # Expect
        self.assertEqual(response.status_code, 404)

    async def test_get_schedule_cms(self):
        # Given
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        schedule = Schedule(
            title="CMS Test Schedule",
            speaker_id=self.speaker.id,
            room_id=self.room.id,
            schedule_type_id=self.schedule_type.id,
            description="Test description",
            presentation_language="English",
            slide_language="English",
            tags=["python"],
            start=start_time,
            end=end_time,
        )
        self.db.add(schedule)
        self.db.commit()

        stream = Stream(
            schedule_id=schedule.id,
            is_public=True,
            mux_live_stream_id="mux_stream_123",
            mux_playback_id="playback_123",
            mux_stream_key="stream_key_123",
            status=StreamStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(stream)
        self.db.commit()

        token, _ = await generate_token_from_user(db=self.db, user=self.user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.get(
            "/schedule/cms",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["count"], 0)
        self.assertEqual(data["results"][0]["title"], "CMS Test Schedule")
        self.assertEqual(data["results"][0]["stream_key"], "stream_key_123")

    async def test_get_mux_stream_by_schedule_id_success(self):
        # Given
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        schedule = Schedule(
            title="Stream Test Schedule",
            speaker_id=self.speaker.id,
            room_id=self.room.id,
            schedule_type_id=self.schedule_type.id,
            description="Test description",
            presentation_language="English",
            slide_language="English",
            tags=["python"],
            start=start_time,
            end=end_time,
        )
        self.db.add(schedule)
        self.db.commit()

        stream = Stream(
            schedule_id=schedule.id,
            is_public=True,
            mux_live_stream_id="mux_stream_123",
            mux_playback_id="playback_123",
            mux_stream_key="stream_key_123",
            status=StreamStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(stream)
        self.db.commit()

        token, _ = await generate_token_from_user(db=self.db, user=self.user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.get(
            f"/schedule/{schedule.id}/stream",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["stream_id"], str(stream.id))
        self.assertEqual(data["stream_key"], "stream_key_123")
        self.assertEqual(data["playback_id"], "playback_123")

    async def test_get_mux_stream_by_schedule_id_unauthorized(self):
        # Given
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        schedule = Schedule(
            title="Stream Test Schedule",
            speaker_id=self.speaker.id,
            room_id=self.room.id,
            schedule_type_id=self.schedule_type.id,
            description="Test description",
            presentation_language="English",
            slide_language="English",
            tags=["python"],
            start=start_time,
            end=end_time,
        )
        self.db.add(schedule)
        self.db.commit()

        token, _ = await generate_token_from_user(
            db=self.db, user=self.user_non_management
        )
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.get(
            f"/schedule/{schedule.id}/stream",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect
        self.assertEqual(response.status_code, 403)

    @patch("core.mux_service.mux_service.create_live_stream")
    @patch("core.mux_service.mux_service.delete_live_stream")
    async def test_recreate_stream_success(
        self, mock_delete_stream, mock_create_stream
    ):
        # Given
        mock_create_stream.return_value = (
            "new_mux_stream_123",
            "new_stream_key_123",
            "new_playback_id_123",
        )

        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        schedule = Schedule(
            title="Recreate Stream Test",
            speaker_id=self.speaker.id,
            room_id=self.room.id,
            schedule_type_id=self.schedule_type.id,
            description="Test description",
            presentation_language="English",
            slide_language="English",
            tags=["python"],
            start=start_time,
            end=end_time,
        )
        self.db.add(schedule)
        self.db.commit()

        stream = Stream(
            schedule_id=schedule.id,
            is_public=True,
            mux_live_stream_id="old_mux_stream_123",
            mux_playback_id="old_playback_123",
            mux_stream_key="old_stream_key_123",
            status=StreamStatus.ENDED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(stream)
        self.db.commit()

        token, _ = await generate_token_from_user(db=self.db, user=self.user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.post(
            f"/schedule/{schedule.id}/recreate-stream",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect
        self.assertEqual(response.status_code, 204)
        mock_delete_stream.assert_called_once_with("old_mux_stream_123")
        mock_create_stream.assert_called_once_with(is_public=True)

    @patch("core.mux_service.mux_service.create_live_stream")
    @patch("core.mux_service.mux_service.delete_live_stream")
    async def test_recreate_stream_when_streaming(
        self, mock_delete_stream, mock_create_stream
    ):
        # Given
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        schedule = Schedule(
            title="Streaming Schedule",
            speaker_id=self.speaker.id,
            room_id=self.room.id,
            schedule_type_id=self.schedule_type.id,
            description="Test description",
            presentation_language="English",
            slide_language="English",
            tags=["python"],
            start=start_time,
            end=end_time,
        )
        self.db.add(schedule)
        self.db.commit()

        stream = Stream(
            schedule_id=schedule.id,
            is_public=True,
            mux_live_stream_id="mux_stream_123",
            mux_playback_id="playback_123",
            mux_stream_key="stream_key_123",
            status=StreamStatus.STREAMING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(stream)
        self.db.commit()

        token, _ = await generate_token_from_user(db=self.db, user=self.user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.post(
            f"/schedule/{schedule.id}/recreate-stream",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect
        self.assertEqual(response.status_code, 400)
        mock_delete_stream.assert_not_called()
        mock_create_stream.assert_not_called()

    async def test_get_schedule_list(self):
        # Given
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        schedule1 = Schedule(
            title="Schedule 1",
            speaker_id=self.speaker.id,
            room_id=self.room.id,
            schedule_type_id=self.schedule_type.id,
            description="Test description 1",
            presentation_language="English",
            slide_language="English",
            tags=["python"],
            start=start_time,
            end=end_time,
        )
        self.db.add(schedule1)

        schedule2 = Schedule(
            title="Schedule 2",
            speaker_id=self.speaker.id,
            room_id=self.room.id,
            schedule_type_id=self.schedule_type.id,
            description="Test description 2",
            presentation_language="English",
            slide_language="English",
            tags=["django"],
            start=start_time + timedelta(hours=2),
            end=end_time + timedelta(hours=2),
        )
        self.db.add(schedule2)
        self.db.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.get("/schedule/", params={"page_size": 10, "page": 1})

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["count"], 0)
        self.assertGreaterEqual(len(data["results"]), 2)

    async def test_get_schedule_list_with_search(self):
        # Given
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)

        schedule1 = Schedule(
            title="Python Advanced",
            speaker_id=self.speaker.id,
            room_id=self.room.id,
            schedule_type_id=self.schedule_type.id,
            description="Advanced Python topics",
            presentation_language="English",
            slide_language="English",
            tags=["python"],
            start=start_time,
            end=end_time,
        )
        self.db.add(schedule1)

        schedule2 = Schedule(
            title="Django Basics",
            speaker_id=self.speaker.id,
            room_id=self.room.id,
            schedule_type_id=self.schedule_type.id,
            description="Basic Django",
            presentation_language="English",
            slide_language="English",
            tags=["django"],
            start=start_time + timedelta(hours=2),
            end=end_time + timedelta(hours=2),
        )
        self.db.add(schedule2)
        self.db.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.get(
            "/schedule", params={"page_size": 10, "page": 1, "search": "Python"}
        )

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["count"], 0)

    def tearDown(self) -> None:
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()

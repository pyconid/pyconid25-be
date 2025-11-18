# import uuid
# from unittest import IsolatedAsyncioTestCase
# from fastapi.testclient import TestClient
# from alembic import config as alembic_config
# from datetime import timedelta
# import datetime
# from main import app
# from models.Speaker import Speaker
# from models.Schedule import Schedule
# from models import engine, db, get_db_sync, get_db_sync_for_test
# from models.SpeakerType import SpeakerType


# class TestSpeakerAndSchedule(IsolatedAsyncioTestCase):
#     def setUp(self) -> None:
#         """Setup database and alembic migration."""
#         alembic_args = ["upgrade", "head"]
#         alembic_config.main(argv=alembic_args)
#         self.connection = engine.connect()
#         self.trans = self.connection.begin()
#         self.db = db(bind=self.connection, join_transaction_mode="create_savepoint")

#         # Override dependency supaya pakai session test ini
#         app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
#         self.client = TestClient(app)

#     def tearDown(self) -> None:
#         """Rollback transaction after each test."""
#         self.trans.rollback()
#         self.connection.close()

#     # --------------------------------------------------
#     # 🧪 SPEAKER TEST
#     # --------------------------------------------------
#     async def test_get_speaker_pagination(self):
#         """Test get_speaker endpoint with pagination and search"""
#         st = SpeakerType(id=uuid.uuid4(), name="Keynote Speaker")
#         self.db.add(st)
#         # Given — buat 3 speaker dummy
#         speaker1 = Speaker(
#             id=uuid.uuid4(),
#             name="Fachri Najm",
#             bio="AI Researcher",
#             email="fachri@example.com",
#             photo_url="https://example.com/fachri.jpg",
#             instagram_link="https://instagram.com/fachri",
#             x_link="https://x.com/fachri",
#             is_keynote_speaker=True,
#             speaker_type=st,
#         )
#         speaker2 = Speaker(
#             id=uuid.uuid4(),
#             name="Andi Wijaya",
#             bio="Backend Developer",
#             email="andi@example.com",
#             photo_url="https://example.com/andi.jpg",
#             is_keynote_speaker=False,
#         )
#         self.db.add_all([speaker1, speaker2])
#         self.db.commit()

#         # When — panggil endpoint /speaker/ tanpa search
#         response = self.client.get("/speaker/?page=1&page_size=10")
#         data = response.json()

#         # Then
#         self.assertEqual(response.status_code, 200)
#         self.assertIn("results", data)
#         self.assertGreaterEqual(len(data["results"]), 2)
#         self.assertIn("page", data)
#         self.assertEqual(data["page"], 1)

#     async def test_get_speaker_with_search(self):
#         """Test get_speaker endpoint with search query"""
#         # Given — 1 speaker
#         speaker = Speaker(
#             id=uuid.uuid4(),
#             name="Jane Doe",
#             bio="Data Scientist",
#             email="jane@example.com",
#             photo_url="https://example.com/jane.jpg",
#         )
#         self.db.add(speaker)
#         self.db.commit()

#         # When
#         response = self.client.get("/speaker/?page=1&page_size=10&search=Jane")
#         data = response.json()

#         # Then
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(len(data["results"]), 1)
#         self.assertEqual(data["results"][0]["name"], "Jane Doe")

#     # --------------------------------------------------
#     # 🧪 SCHEDULE TEST
#     # --------------------------------------------------
#     async def test_get_schedule_with_speaker_relation(self):
#         """Test get_schedule endpoint with joined speaker data"""
#         # Given
#         speaker = Speaker(
#             id=uuid.uuid4(),
#             name="John Smith",
#             bio="Keynote Speaker",
#             email="john@example.com",
#             photo_url="https://example.com/john.jpg",
#             is_keynote_speaker=True,
#         )
#         self.db.add(speaker)
#         self.db.commit()

#         schedule = Schedule(
#             id=uuid.uuid4(),
#             topic="AI in 2025",
#             description="Exploring the future of AI",
#             speaker_id=speaker.id,
#             start=datetime.datetime.now(datetime.timezone.utc),
#             end=datetime.datetime.now(datetime.timezone.utc) + timedelta(hours=1),
#         )
#         self.db.add(schedule)
#         self.db.commit()

#         # When
#         response = self.client.get("/schedule/?page=1&page_size=5")
#         data = response.json()

#         # Then
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(data["page"], 1)
#         self.assertIn("results", data)
#         self.assertEqual(len(data["results"]), 1)

#         schedule_item = data["results"][0]
#         self.assertIn("speaker", schedule_item)
#         self.assertEqual(schedule_item["speaker"]["name"], "John Smith")

#     async def test_get_schedule_with_search(self):
#         """Test search filter on schedule endpoint"""
#         speaker = Speaker(
#             id=uuid.uuid4(),
#             name="Nadia Rahma",
#             bio="ML Engineer",
#             email="nadia@example.com",
#             photo_url="https://example.com/nadia.jpg",
#         )
#         self.db.add(speaker)
#         self.db.commit()

#         schedule = Schedule(
#             id=uuid.uuid4(),
#             topic="Deep Learning Trends",
#             description="What's new in DL",
#             speaker_id=speaker.id,
#             start=datetime.datetime.now(datetime.timezone.utc),
#             end=datetime.datetime.now(datetime.timezone.utc) + timedelta(hours=2),
#         )
#         self.db.add(schedule)
#         self.db.commit()

#         response = self.client.get("/schedule/?page=1&page_size=10&search=Deep")
#         data = response.json()

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(len(data["results"]), 1)
#         self.assertEqual(data["results"][0]["topic"], "Deep Learning Trends")

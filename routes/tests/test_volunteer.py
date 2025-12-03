import shutil
import uuid
import alembic.config
from unittest import IsolatedAsyncioTestCase

from fastapi.testclient import TestClient
from sqlalchemy import select
from core.security import generate_token_from_user
from models import engine, db, get_db_sync, get_db_sync_for_test
from models.Volunteer import Volunteer
from models.User import MANAGEMENT_PARTICIPANT, User
from main import app
from schemas.volunteer import VolunteerDetailResponse
from settings import FILE_STORAGE_PATH


class TestVolunteer(IsolatedAsyncioTestCase):
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

    async def test_get_all_volunteer_public(self):
        # Given
        user_management = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="admin",
        )
        self.db.add(user_management)
        user_1 = User(
            username="John Doe",
            first_name="John",
            last_name="Doe",
            bio="A keynote volunteer",
            profile_picture="http://example.com/photo.jpg",
            email="john@pycon.id",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
            share_my_public_social_media=True,
        )
        self.db.add(user_1)
        volunteer1 = Volunteer(
            user=user_1,
        )
        self.db.add(volunteer1)
        self.db.commit()
        user_2 = User(
            username="Jane Doe",
            first_name="Jane",
            last_name="Doe",
            bio="A keynote volunteer",
            profile_picture="http://example.com/photo.jpg",
            email="jane@pycon.id",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
            share_my_public_social_media=False,
        )
        self.db.add(user_1)
        volunteer2 = Volunteer(
            user=user_2,
        )
        self.db.add(volunteer2)
        self.db.commit()
        (token, _) = await generate_token_from_user(db=self.db, user=user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.get(
            "/volunteer/public/",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect
        self.assertEqual(response.status_code, 200)

    async def test_get_all_volunteer(self):
        # Given
        user_management = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="admin",
            participant_type=MANAGEMENT_PARTICIPANT,
        )
        self.db.add(user_management)
        user_1 = User(
            username="John Doe",
            first_name="John",
            last_name="Doe",
            bio="A keynote volunteer",
            profile_picture="http://example.com/photo.jpg",
            email="john@pycon.id",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
            share_my_public_social_media=True,
        )
        self.db.add(user_1)
        volunteer1 = Volunteer(
            user=user_1,
        )
        self.db.add(volunteer1)
        self.db.commit()
        user_2 = User(
            username="Jane Doe",
            first_name="Jane",
            last_name="Doe",
            bio="A keynote volunteer",
            profile_picture="http://example.com/photo.jpg",
            email="jane@pycon.id",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
            share_my_public_social_media=False,
        )
        self.db.add(user_1)
        volunteer2 = Volunteer(
            user=user_2,
        )
        self.db.add(volunteer2)
        self.db.commit()
        (token, _) = await generate_token_from_user(db=self.db, user=user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When
        response = client.get(
            "/volunteer/",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect
        self.assertEqual(response.status_code, 200)

    async def test_get_volunteer_by_id(self):
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
        user = User(
            username="John Doe",
            first_name="John",
            last_name="Doe",
            bio="A keynote volunteer",
            profile_picture="http://example.com/photo.jpg",
            email="John@gmail.com",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
            share_my_public_social_media=False,
        )
        self.db.add(user)
        volunteer = Volunteer(
            user=user,
        )
        self.db.add(volunteer)
        self.db.commit()
        (token, _) = await generate_token_from_user(db=self.db, user=user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1
        response = client.get(
            f"/volunteer/{volunteer.id}", headers={"Authorization": f"Bearer {token}"}
        )

        # Expect 1
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            VolunteerDetailResponse(
                id=str(volunteer.id),
                user=VolunteerDetailResponse.DetailUser(
                    id=str(volunteer.user.id),
                    first_name=volunteer.user.first_name,
                    last_name=volunteer.user.last_name,
                    username=volunteer.user.username,
                    bio=volunteer.user.bio,
                    email=volunteer.user.email,
                    website=volunteer.user.website
                    if volunteer.user.share_my_public_social_media
                    else None,
                    facebook_username=volunteer.user.facebook_username
                    if volunteer.user.share_my_public_social_media
                    else None,
                    linkedin_username=volunteer.user.linkedin_username
                    if volunteer.user.share_my_public_social_media
                    else None,
                    twitter_username=volunteer.user.twitter_username
                    if volunteer.user.share_my_public_social_media
                    else None,
                    instagram_username=volunteer.user.instagram_username
                    if volunteer.user.share_my_public_social_media
                    else None,
                    profile_picture=volunteer.user.profile_picture,
                ),
            ).model_dump(),
        )

        # When 2
        (token, _) = await generate_token_from_user(
            db=self.db, user=user_non_management
        )
        response = client.get(
            f"/volunteer/{volunteer.id}", headers={"Authorization": f"Bearer {token}"}
        )

        # Expect 2
        self.assertEqual(response.status_code, 403)

    async def test_create_volunteer(self):
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
        self.db.commit()
        (token, _) = await generate_token_from_user(db=self.db, user=user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1
        response = client.post(
            "/volunteer/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": str(user_non_management.id),
            },
            # files={"photo": open("./routes/tests/data/bandungpy.jpg", "rb")},
        )

        # Expect 1
        self.assertEqual(response.status_code, 200)
        stmt = select(Volunteer).where(Volunteer.user_id == user_non_management.id)
        volunteer = self.db.execute(stmt).scalar()
        self.assertIsNotNone(volunteer)

        # When 2
        (token, _) = await generate_token_from_user(
            db=self.db, user=user_non_management
        )
        response = client.post(
            "/volunteer/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": str(user_non_management.id),
            },
            # files={"photo": open("./routes/tests/data/bandungpy.jpg", "rb")},
        )

        # Expect 2
        self.assertEqual(response.status_code, 403)

    async def test_update_volunteer(self):
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
        user = User(
            username="John Doe",
            first_name="John",
            last_name="Doe",
            bio="A keynote volunteer",
            profile_picture="http://example.com/photo.jpg",
            email="John@gmail.com",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
        )
        self.db.add(user)
        volunteer = Volunteer(
            user=user,
        )
        self.db.add(volunteer)
        self.db.commit()
        (token, _) = await generate_token_from_user(db=self.db, user=user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1
        response = client.put(
            f"/volunteer/{volunteer.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": str(user_non_management.id),
            },
            # files={"photo": open("./routes/tests/data/bandungpy.jpg", "rb")},
        )

        # Expect 1
        self.assertEqual(response.status_code, 200)
        self.assertEqual(volunteer.user_id, user_non_management.id)

        # When 2
        (token, _) = await generate_token_from_user(
            db=self.db, user=user_non_management
        )
        response = client.put(
            f"/volunteer/{volunteer.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": str(user_non_management.id),
            },
            # files={"photo": open("./routes/tests/data/bandungpy.jpg", "rb")},
        )

        # Expect 2
        self.assertEqual(response.status_code, 403)

    async def test_delete_volunteer(self):
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
        user = User(
            username="John Doe",
            first_name="John",
            last_name="Doe",
            bio="A keynote volunteer",
            profile_picture="http://example.com/photo.jpg",
            email="John@gmail.com",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
        )
        volunteer = Volunteer(
            id=uuid.uuid4(),
            user=user,
        )
        self.db.add(volunteer)
        self.db.commit()
        (token, _) = await generate_token_from_user(db=self.db, user=user_management)
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1
        response = client.delete(
            f"/volunteer/{str(volunteer.id)}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect 1
        self.assertEqual(response.status_code, 204)
        stmt = select(Volunteer).where(Volunteer.id == volunteer.id)
        volunteer = self.db.execute(stmt).scalar()
        self.assertIsNone(volunteer)

        # When 2
        (token, _) = await generate_token_from_user(
            db=self.db, user=user_non_management
        )
        response = client.delete(
            "/volunteer/123e4567-e89b-12d3-a456-426614174000",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect 2
        self.assertEqual(response.status_code, 403)

    async def test_get_volunteer_profile_picture(self):
        # Given
        user = User(
            username="John Doe",
            first_name="John",
            last_name="Doe",
            bio="A keynote volunteer",
            profile_picture=None,
            email="John@gmail.com",
            instagram_username="http://instagram.com/johndoe",
            twitter_username="http://x.com/johndoe",
        )
        volunteer = Volunteer(
            id=uuid.uuid4(),
            user=user,
        )
        self.db.add(volunteer)
        self.db.commit()
        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)
        client = TestClient(app)

        # When 1
        response = client.get(
            f"/volunteer/{str(volunteer.id)}/profile-picture/",
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
            f"/volunteer/{str(volunteer.id)}/profile-picture/",
        )

        # Expect 2
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()

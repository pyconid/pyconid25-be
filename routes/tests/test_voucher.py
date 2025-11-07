from fastapi.testclient import TestClient
from models import engine, db, get_db_sync, get_db_sync_for_test
from models.Voucher import Voucher
from main import app
import alembic.config
import uuid
from unittest import TestCase


class TestVoucher(TestCase):
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

        self.test_voucher_id = uuid.uuid4()
        voucher = Voucher(
            id=self.test_voucher_id,
            code="TEST2025",
            value=50000,
            type="Speaker",
            email_whitelist={"emails": ["test@example.com", "user@example.com"]},
            quota=100,
            is_active=True,
        )
        self.session.add(voucher)
        self.session.commit()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.session)
        self.client = TestClient(app)

    def tearDown(self):
        self.session.close()
        self.trans.rollback()
        self.connection.close()

    def test_create_voucher(self):
        response = self.client.post(
            "/voucher/",
            json={
                "code": "NEWCODE2025",
                "value": 100000,
                "quota": 50,
                "type": "Speaker",
                "email_whitelist": {"emails": ["new@example.com"]},
                "is_active": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "NEWCODE2025"
        assert data["value"] == 100000
        assert data["quota"] == 50
        assert data["type"] == "Speaker"
        assert data["is_active"] is False

    def test_create_voucher_with_invalid_participant_type(self):
        """Test that creating voucher with invalid participant type is rejected"""
        response = self.client.post(
            "/voucher/",
            json={
                "code": "INVALID2025",
                "value": 50000,
                "quota": 20,
                "type": "invalid_type",
                "is_active": False,
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert any("type" in str(error).lower() for error in data["detail"])

    def test_create_voucher_with_random_string_type(self):
        """Test that creating voucher with random string type is rejected"""
        response = self.client.post(
            "/voucher/",
            json={
                "code": "RANDOM2025",
                "quota": 15,
                "type": "random_string",
            },
        )
        assert response.status_code == 422

    def test_create_voucher_with_valid_participant_type(self):
        """Test that creating voucher with valid ParticipantType enum works"""
        valid_types = [
            "Non Participant",
            "In Person Participant",
            "Online Participant",
            "Keynote Speaker",
            "Speaker",
            "Organizer",
            "Volunteer",
            "Sponsor",
            "Community",
            "Patron",
        ]

        for idx, participant_type in enumerate(valid_types):
            response = self.client.post(
                "/voucher/",
                json={
                    "code": f"VALID{idx:02d}",
                    "quota": 10,
                    "type": participant_type,
                },
            )
            assert response.status_code == 200, f"Failed for type: {participant_type}"
            data = response.json()
            assert data["type"] == participant_type

    def test_create_voucher_minimal(self):
        response = self.client.post(
            "/voucher/",
            json={
                "code": "MINIMAL2025",
                "quota": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "MINIMAL2025"
        assert data["value"] == 0
        assert data["quota"] == 10
        assert data["is_active"] is False

    def test_update_voucher_status(self):
        response = self.client.patch(
            f"/voucher/{self.test_voucher_id}/status",
            json={"is_active": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["code"] == "TEST2025"

    def test_update_voucher_status_not_found(self):
        random_id = uuid.uuid4()
        response = self.client.patch(
            f"/voucher/{random_id}/status",
            json={"is_active": True},
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_update_voucher_whitelist(self):
        new_whitelist = {"emails": ["updated@example.com", "another@example.com"]}
        response = self.client.patch(
            f"/voucher/{self.test_voucher_id}/whitelist",
            json={"email_whitelist": new_whitelist},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email_whitelist"] == new_whitelist
        assert data["code"] == "TEST2025"

    def test_update_voucher_whitelist_not_found(self):
        random_id = uuid.uuid4()
        response = self.client.patch(
            f"/voucher/{random_id}/whitelist",
            json={"email_whitelist": {"emails": ["test@example.com"]}},
        )
        assert response.status_code == 404

    def test_update_voucher_quota(self):
        response = self.client.patch(
            f"/voucher/{self.test_voucher_id}/quota",
            json={"quota": 200},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quota"] == 200
        assert data["code"] == "TEST2025"

    def test_update_voucher_quota_not_found(self):
        random_id = uuid.uuid4()
        response = self.client.patch(
            f"/voucher/{random_id}/quota",
            json={"quota": 50},
        )
        assert response.status_code == 404

    def test_update_voucher_value(self):
        response = self.client.patch(
            f"/voucher/{self.test_voucher_id}/value",
            json={"value": 75000},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == 75000
        assert data["code"] == "TEST2025"

    def test_update_voucher_value_not_found(self):
        random_id = uuid.uuid4()
        response = self.client.patch(
            f"/voucher/{random_id}/value",
            json={"value": 10000},
        )
        assert response.status_code == 404

    def test_update_voucher_type(self):
        response = self.client.patch(
            f"/voucher/{self.test_voucher_id}/type",
            json={"type": "Volunteer"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "Volunteer"
        assert data["code"] == "TEST2025"

    def test_update_voucher_type_with_invalid_type(self):
        """Test that updating voucher type with invalid type is rejected"""
        response = self.client.patch(
            f"/voucher/{self.test_voucher_id}/type",
            json={"type": "invalid_type"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_update_voucher_type_not_found(self):
        random_id = uuid.uuid4()
        response = self.client.patch(
            f"/voucher/{random_id}/type",
            json={"type": "Speaker"},
        )
        assert response.status_code == 404

    def test_list_vouchers_default_pagination(self):
        response = self.client.get("/voucher/")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "page" in data
        assert "page_size" in data
        assert "count" in data
        assert "page_count" in data
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["results"]) >= 1
        assert any(v["code"] == "TEST2025" for v in data["results"])

    def test_list_vouchers_with_pagination(self):
        for i in range(15):
            voucher = Voucher(
                id=uuid.uuid4(),
                code=f"VOUCHER{i:03d}",
                value=1000 * i,
                quota=10,
                is_active=True,
            )
            self.session.add(voucher)
        self.session.commit()

        response = self.client.get("/voucher/?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["results"]) == 5
        assert data["count"] >= 15

        response_page2 = self.client.get("/voucher/?page=2&page_size=5")
        assert response_page2.status_code == 200
        data_page2 = response_page2.json()
        assert data_page2["page"] == 2
        assert len(data_page2["results"]) == 5

    def test_list_vouchers_with_search(self):
        voucher1 = Voucher(
            id=uuid.uuid4(),
            code="SEARCH2025",
            value=10000,
            quota=50,
            is_active=True,
        )
        voucher2 = Voucher(
            id=uuid.uuid4(),
            code="ANOTHER2025",
            value=20000,
            quota=30,
            is_active=True,
        )
        self.session.add(voucher1)
        self.session.add(voucher2)
        self.session.commit()

        response = self.client.get("/voucher/?search=SEARCH")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) >= 1
        assert any(v["code"] == "SEARCH2025" for v in data["results"])
        assert all("SEARCH" in v["code"] for v in data["results"])

    def test_list_vouchers_empty_result(self):
        response = self.client.get("/voucher/?search=NONEXISTENT")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert len(data["results"]) == 0
        assert data["page_count"] == 0

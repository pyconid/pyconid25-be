import alembic.config
from unittest import IsolatedAsyncioTestCase

from fastapi.testclient import TestClient
from models import engine, db, get_db_sync, get_db_sync_for_test
from models.Country import Country
from models.State import State
from models.City import City
from main import app


class TestLocations(IsolatedAsyncioTestCase):
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

        # Setup sample data
        self._setup_sample_data()

        app.dependency_overrides[get_db_sync] = get_db_sync_for_test(db=self.db)

    def _setup_sample_data(self):
        self.db.query(City).delete()
        self.db.query(State).delete()
        self.db.query(Country).delete()
        self.db.commit()

        countries = [
            Country(id=102, name="Indonesia", iso2="ID", iso3="IDN"),
            Country(id=231, name="United States", iso2="US", iso3="USA"),
            Country(id=44, name="United Kingdom", iso2="GB", iso3="GBR"),
        ]
        for country in countries:
            self.db.merge(country)

        states = [
            State(id=1836, name="Jakarta", country_id=102, country_code="ID"),
            State(id=1837, name="West Java", country_id=102, country_code="ID"),
            State(id=1416, name="California", country_id=231, country_code="US"),
        ]
        for state in states:
            self.db.merge(state)

        cities = [
            City(id=38932, name="Jakarta Pusat", state_id=1836, country_id=102),
            City(id=38933, name="Jakarta Selatan", state_id=1836, country_id=102),
            City(id=38934, name="Bandung", state_id=1837, country_id=102),
        ]
        for city in cities:
            self.db.merge(city)

        self.db.commit()

    async def test_get_countries_all(self):
        # Given
        client = TestClient(app)

        # When
        response = client.get("/locations/countries/")

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 3)
        self.assertIn("Indonesia", [c["name"] for c in data["results"]])

    async def test_get_countries_with_search(self):
        # Given
        client = TestClient(app)

        # When
        response = client.get("/locations/countries/?search=indo")

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data["results"]
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(
            any("Indonesia" in country["name"] for country in results),
            "Should find Indonesia",
        )

    async def test_get_countries_with_limit(self):
        # Given
        client = TestClient(app)

        # When
        response = client.get("/locations/countries/?limit=2")

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data["results"]), 2)
        self.assertEqual(data["limit"], 2)

    async def test_get_states_by_country(self):
        # Given
        client = TestClient(app)

        # When
        response = client.get("/locations/states/?country_id=102")

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data["results"]
        self.assertEqual(len(results), 2)
        self.assertTrue(
            all(state["country_id"] == 102 for state in results),
            "All states should belong to Indonesia",
        )
        state_names = [s["name"] for s in results]
        self.assertIn("Jakarta", state_names)
        self.assertIn("West Java", state_names)

    async def test_get_states_with_search(self):
        # Given
        client = TestClient(app)

        # When
        response = client.get("/locations/states/?country_id=102&search=jak")

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data["results"]
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(
            all("Jakarta" in state["name"] for state in results),
            "All results should contain 'Jakarta'",
        )

    async def test_get_states_invalid_country(self):
        # Given
        client = TestClient(app)

        # When
        response = client.get("/locations/states/?country_id=999")

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 0)

    async def test_get_states_missing_country_id(self):
        # Given
        client = TestClient(app)

        # When
        response = client.get("/locations/states/")

        # Expect
        self.assertEqual(response.status_code, 422)

    async def test_get_cities_by_state(self):
        # Given
        client = TestClient(app)

        # When
        response = client.get("/locations/cities/?state_id=1836")

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data["results"]
        self.assertEqual(len(results), 2)
        self.assertTrue(
            all(city["state_id"] == 1836 for city in results),
            "All cities should belong to Jakarta",
        )
        city_names = [c["name"] for c in results]
        self.assertIn("Jakarta Pusat", city_names)
        self.assertIn("Jakarta Selatan", city_names)

    async def test_get_cities_with_search(self):
        # Given
        client = TestClient(app)

        # When
        response = client.get("/locations/cities/?state_id=1836&search=pusat")

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data["results"]
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(
            all("Pusat" in city["name"] for city in results),
            "All results should contain 'Pusat'",
        )

    async def test_get_cities_invalid_state(self):
        # Given
        client = TestClient(app)

        # When
        response = client.get("/locations/cities/?state_id=9999")

        # Expect
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 0)

    async def test_get_cities_missing_state_id(self):
        # Given
        client = TestClient(app)

        # When
        response = client.get("/locations/cities/")

        # Expect
        self.assertEqual(response.status_code, 422)

    async def test_cascading_dropdown_flow(self):
        # Given
        client = TestClient(app)

        # When 1: Get countries
        response = client.get("/locations/countries/?search=Indonesia")
        self.assertEqual(response.status_code, 200)
        countries = response.json()["results"]
        self.assertGreaterEqual(len(countries), 1)
        indonesia = countries[0]
        self.assertEqual(indonesia["id"], 102)

        # When 2: Get states for Indonesia
        response = client.get(f"/locations/states/?country_id={indonesia['id']}")
        self.assertEqual(response.status_code, 200)
        states = response.json()["results"]
        self.assertGreaterEqual(len(states), 1)
        jakarta = next(s for s in states if s["name"] == "Jakarta")
        self.assertEqual(jakarta["id"], 1836)

        # When 3: Get cities for Jakarta
        response = client.get(f"/locations/cities/?state_id={jakarta['id']}")
        self.assertEqual(response.status_code, 200)
        cities = response.json()["results"]
        self.assertGreaterEqual(len(cities), 1)

        # Expect
        self.assertTrue(
            any(city["name"] == "Jakarta Pusat" for city in cities),
            "Should find Jakarta Pusat",
        )

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()
        app.dependency_overrides.clear()

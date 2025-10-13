import alembic.config
from models.City import City
from models.Country import Country
from models.State import State
from validators.location import LocationValidationError, validate_location_hierarchy

from unittest import IsolatedAsyncioTestCase
from models import engine, db


class TestLocationValidation(IsolatedAsyncioTestCase):
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

    def _setup_sample_data(self):
        # Countries
        countries = [
            Country(id=102, name="Indonesia", iso2="ID", iso3="IDN", phone_code="62"),
            Country(
                id=231, name="United States", iso2="US", iso3="USA", phone_code="1"
            ),
        ]
        for country in countries:
            self.db.merge(country)

        # States
        states = [
            State(id=1836, name="Jakarta", country_id=102, country_code="ID"),
            State(id=1837, name="West Java", country_id=102, country_code="ID"),
            State(id=1416, name="California", country_id=231, country_code="US"),
        ]
        for state in states:
            self.db.merge(state)

        # Cities
        cities = [
            City(id=38932, name="Jakarta Pusat", state_id=1836, country_id=102),
            City(id=38933, name="Jakarta Selatan", state_id=1836, country_id=102),
            City(id=38934, name="Bandung", state_id=1837, country_id=102),
            City(id=129957, name="San Francisco", state_id=1416, country_id=231),
        ]
        for city in cities:
            self.db.merge(city)

        self.db.commit()

    async def test_valid_country_only(self):
        # Given & When
        try:
            validate_location_hierarchy(db=self.db, country_id=102)
            success = True
        except LocationValidationError:
            success = False

        # Expect
        self.assertTrue(success, "Valid country should pass validation")

    async def test_invalid_country(self):
        # Given & When & Expect
        with self.assertRaises(LocationValidationError) as context:
            validate_location_hierarchy(db=self.db, country_id=999)

        self.assertIn("Invalid country_id", str(context.exception))

    async def test_valid_country_and_state(self):
        # Given & When
        try:
            validate_location_hierarchy(
                db=self.db,
                country_id=102,  # Indonesia
                state_id=1836,  # Jakarta
            )
            success = True
        except LocationValidationError:
            success = False

        # Expect
        self.assertTrue(success, "Valid country + state should pass validation")

    async def test_state_not_in_country(self):
        # Given & When & Expect
        with self.assertRaises(LocationValidationError) as context:
            validate_location_hierarchy(
                db=self.db,
                country_id=102,  # Indonesia
                state_id=1416,  # California (US state, bukan Indonesia!)
            )

        self.assertIn("state_id does not belong to country_id", str(context.exception))

    async def test_invalid_state(self):
        # Given & When & Expect
        with self.assertRaises(LocationValidationError) as context:
            validate_location_hierarchy(db=self.db, country_id=102, state_id=9999)

        self.assertIn("Invalid state_id", str(context.exception))

    async def test_valid_full_hierarchy(self):
        # Given & When
        try:
            validate_location_hierarchy(
                db=self.db,
                country_id=102,  # Indonesia
                state_id=1836,  # Jakarta
                city_id=38932,  # Jakarta Pusat
            )
            success = True
        except LocationValidationError:
            success = False

        # Expect
        self.assertTrue(
            success, "Valid full hierarchy (country+state+city) should pass validation"
        )

    async def test_city_not_in_state(self):
        # Given & When & Expect
        with self.assertRaises(LocationValidationError) as context:
            validate_location_hierarchy(
                db=self.db,
                country_id=231,  # USA
                state_id=1416,  # California
                city_id=38932,  # Jakarta Pusat (Indonesia city!)
            )

        self.assertIn("city_id does not belong to state_id", str(context.exception))

    async def test_invalid_city(self):
        # Given & When & Expect
        with self.assertRaises(LocationValidationError) as context:
            validate_location_hierarchy(
                db=self.db, country_id=102, state_id=1836, city_id=999999
            )

        self.assertIn("Invalid city_id", str(context.exception))

    async def test_city_without_state(self):
        # Given & When & Expect
        with self.assertRaises(LocationValidationError):
            validate_location_hierarchy(
                db=self.db,
                country_id=102,
                state_id=None,  # Missing state!
                city_id=38932,
            )

    async def test_valid_with_zipcode(self):
        # Given & When
        try:
            validate_location_hierarchy(
                db=self.db,
                country_id=102,  # Indonesia
                state_id=1836,  # Jakarta
                city_id=38932,  # Jakarta Pusat
                zip_code="12950",  # Valid Jakarta zip code
            )
            success = True
        except LocationValidationError:
            success = False

        # Expect
        self.assertTrue(success, "Valid location with zip code should pass validation")

    def tearDown(self):
        self.db.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()

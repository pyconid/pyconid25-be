from models import factory_session
from seeders.initial_country_city_state import initial_country_city_state_seeders


def initial_seeders():
    with factory_session() as session:
        initial_country_city_state_seeders(db=session, is_commit=True)
        # uncomment jika ingin develop dengan data speaker dan schedule
        # initial_speakers_seeders(db=session, is_commit=True)
        # initial_schedules_seeders(db=session, is_commit=True)

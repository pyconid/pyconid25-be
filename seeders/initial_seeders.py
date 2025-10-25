from models import factory_session
from seeders.initial_country_city_state import initial_country_city_state_seeders


def initial_seeders():
    with factory_session() as session:
        initial_country_city_state_seeders(db=session, is_commit=True)

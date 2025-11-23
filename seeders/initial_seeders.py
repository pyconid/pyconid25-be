from seeders.initial_schedule_type import initial_schedule_type
from seeders.initial_room import initial_room
from models import factory_session

from seeders.initial_country_city_state import initial_country_city_state_seeders
from seeders.initial_speaker_type import initial_speaker_type


def initial_seeders():
    with factory_session() as session:
        initial_country_city_state_seeders(db=session, is_commit=True)
        initial_speaker_type(db=session, is_commit=True)
        initial_room(db=session, is_commit=True)
        initial_schedule_type(db=session, is_commit=True)
        # uncomment jika ingin develop dengan data speaker dan schedule
        # initial_speakers_seeders(db=session, is_commit=True)
        # initial_schedules_seeders(db=session, is_commit=True)

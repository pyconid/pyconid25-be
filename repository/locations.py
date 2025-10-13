from typing import Optional
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from models.City import City
from models.Country import Country
from models.State import State


def get_country_by_id(db: Session, id: int):
    query = select(Country).where(Country.id == id)
    result = db.execute(query).scalar_one_or_none()
    return result


def get_all_countries(
    db: Session, search: Optional[str] = None, limit: Optional[int] = None
):
    query = select(Country)
    if search:
        search_filters = [
            Country.name.ilike(f"%{search}%"),
            Country.iso2.ilike(f"%{search}%"),
        ]
        query = query.where(or_(*search_filters))

    if limit is not None:
        query = query.limit(limit)

    query = query.order_by(Country.name.asc(), Country.id.asc())
    result = db.execute(query).scalars().all()
    return result


def get_state_by_id(db: Session, id: int, country_id: Optional[int] = None):
    query = select(State).where(State.id == id)
    if country_id:
        query = query.where(State.country_id == country_id)

    result = db.execute(query).scalar_one_or_none()
    return result


def get_all_states(
    db: Session,
    country_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
):
    query = select(State)
    if country_id:
        query = query.where(State.country_id == country_id)
    if search:
        search_filters = [
            State.name.ilike(f"%{search}%"),
            State.iso2.ilike(f"%{search}%"),
            State.country_code.ilike(f"%{search}%"),
        ]
        query = query.where(or_(*search_filters))

    if limit is not None:
        query = query.limit(limit)

    query = query.order_by(State.name.asc(), State.id.asc())
    result = db.execute(query).scalars().all()
    return result


def get_city_by_id(
    db: Session,
    id: int,
    state_id: Optional[int] = None,
    country_id: Optional[int] = None,
):
    query = select(City).where(City.id == id)
    if state_id:
        query = query.where(City.state_id == state_id)
    if country_id:
        query = query.where(City.country_id == country_id)

    result = db.execute(query).scalar_one_or_none()
    return result


def get_all_cities(
    db: Session,
    state_id: Optional[int] = None,
    country_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
):
    query = select(City)
    if state_id:
        query = query.where(City.state_id == state_id)
    if country_id:
        query = query.where(City.country_id == country_id)
    if search:
        search_filters = [
            City.name.ilike(f"%{search}%"),
            City.state_code.ilike(f"%{search}%"),
            City.country_code.ilike(f"%{search}%"),
        ]
        query = query.where(or_(*search_filters))

    if limit is not None:
        query = query.limit(limit)

    query = query.order_by(City.name.asc(), City.id.asc())
    result = db.execute(query).scalars().all()
    return result

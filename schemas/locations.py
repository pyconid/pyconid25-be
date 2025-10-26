from typing import List, Optional

from fastapi import Query
from pydantic import BaseModel


class CountryDropdownQuery(BaseModel):
    search: Optional[str] = Query(
        None, description="Search by country name or ISO2 code"
    )
    limit: Optional[int] = Query(None, ge=1, description="Limit results")


class CountryDropdownResponse(BaseModel):
    class Country(BaseModel):
        id: int
        name: str
        iso2: Optional[str] = None

    limit: Optional[int] = None
    results: List[Country]


class StateDropdownQuery(BaseModel):
    country_id: int = Query(..., description="Filter states by country ID")
    search: Optional[str] = Query(None, description="Search by state name")
    limit: Optional[int] = Query(None, ge=1, description="Limit results")


class StateDropdownResponse(BaseModel):
    class State(BaseModel):
        id: int
        name: str
        country_id: int

    limit: Optional[int] = None
    results: List[State]


class CityDropdownQuery(BaseModel):
    state_id: int = Query(..., description="Filter cities by state ID")
    search: Optional[str] = Query(None, description="Search by city name")
    limit: Optional[int] = Query(None, ge=1, description="Limit results")


class CityDropdownResponse(BaseModel):
    class City(BaseModel):
        id: int
        name: str
        state_id: int
        country_id: int

    limit: Optional[int] = None
    results: List[City]

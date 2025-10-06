import traceback
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.responses import InternalServerError, Ok, common_response
from models import get_db_sync
from schemas.common import InternalServerErrorResponse
from schemas.dropdown import (
    CityDropdownQuery,
    CountryDropdownQuery,
    CountryDropdownResponse,
    StateDropdownQuery,
    StateDropdownResponse,
    CityDropdownResponse,
    EnumDropdownItem,
    IndustryCategoryDropdownResponse,
    JobCategoryDropdownResponse,
)
from schemas.user_profile import (
    IndustryCategory,
    JobCategory,
)
from repository import locations as locationRepo

router = APIRouter(prefix="/dropdown", tags=["Dropdown"])


@router.get(
    "/countries/",
    responses={
        "200": {"model": CountryDropdownResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_countries(
    query: CountryDropdownQuery = Depends(),
    db: Session = Depends(get_db_sync),
):
    try:
        countries = locationRepo.get_all_countries(
            db=db, search=query.search, limit=query.limit
        )
        return common_response(
            Ok(
                data={
                    "limit": query.limit,
                    "results": [
                        {"id": country.id, "name": country.name, "iso2": country.iso2}
                        for country in countries
                    ],
                }
            )
        )
    except Exception as e:
        traceback.print_exc()
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/states/",
    responses={
        "200": {"model": StateDropdownResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_states(
    query: StateDropdownQuery = Depends(),
    db: Session = Depends(get_db_sync),
):
    try:
        states = locationRepo.get_all_states(
            db=db,
            country_id=query.country_id,
            search=query.search,
            limit=query.limit,
        )

        return common_response(
            Ok(
                data={
                    "limit": query.limit,
                    "results": [
                        {
                            "id": state.id,
                            "name": state.name,
                            "country_id": state.country_id,
                        }
                        for state in states
                    ],
                }
            )
        )
    except Exception as e:
        traceback.print_exc()
        return common_response(InternalServerError(error=str(e)))


@router.get(
    "/cities/",
    responses={
        "200": {"model": CityDropdownResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_cities(
    query: CityDropdownQuery = Depends(),
    db: Session = Depends(get_db_sync),
):
    try:
        cities = locationRepo.get_all_cities(
            db=db,
            state_id=query.state_id,
            search=query.search,
            limit=query.limit,
        )

        return common_response(
            Ok(
                data={
                    "limit": query.limit,
                    "results": [
                        {
                            "id": city.id,
                            "name": city.name,
                            "state_id": city.state_id,
                            "country_id": city.country_id,
                        }
                        for city in cities
                    ],
                }
            )
        )
    except Exception as e:
        traceback.print_exc()
        return common_response(InternalServerError(error=str(e)))


@router.get("/industry-categories/", response_model=IndustryCategoryDropdownResponse)
async def get_industry_categories():
    items = [
        EnumDropdownItem(value=category.value, label=category.value)
        for category in IndustryCategory
    ]
    return IndustryCategoryDropdownResponse(results=items)


@router.get("/job-categories/", response_model=JobCategoryDropdownResponse)
async def get_job_categories():
    items = [
        EnumDropdownItem(value=category.value, label=category.value)
        for category in JobCategory
    ]
    return JobCategoryDropdownResponse(results=items)

from typing import Optional
from sqlalchemy.orm import Session
from repository import locations as locationRepo
from validators.zipcode import validate_zipcode


class LocationValidationError(Exception):
    pass


def validate_location_hierarchy(
    db: Session,
    country_id: int,
    state_id: Optional[int] = None,
    city_id: Optional[int] = None,
    zip_code: Optional[str] = None,
) -> None:
    """
    Validate location hierarchy and relationships

    Raises:
        LocationValidationError: If validation fails
    """
    # Validate country
    country = locationRepo.get_country_by_id(db=db, id=country_id)
    if country is None:
        raise LocationValidationError("Invalid country_id")

    # Validate zip code
    if zip_code and country.iso2:
        is_valid, error_message = validate_zipcode(
            zip_code=zip_code, country_code=country.iso2
        )
        if not is_valid:
            raise LocationValidationError(error_message)

    # Validate state
    if state_id is not None:
        state = locationRepo.get_state_by_id(db=db, id=state_id)
        if state is None:
            raise LocationValidationError("Invalid state_id")
        if state.country_id != country_id:
            raise LocationValidationError("state_id does not belong to country_id")

    # Validate city
    if city_id is not None:
        city = locationRepo.get_city_by_id(db=db, id=city_id)
        if city is None:
            raise LocationValidationError("Invalid city_id")
        if city.state_id != state_id:
            raise LocationValidationError("city_id does not belong to state_id")

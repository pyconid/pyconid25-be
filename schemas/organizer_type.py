from typing import Sequence

from pydantic import BaseModel

from models.OrganizerType import OrganizerType


class OrganizerTypeItem(BaseModel):
    id: str
    name: str


class OrganizerTypeAllResponse(BaseModel):
    results: list[OrganizerTypeItem]


def organizer_type_item_from_model(model: OrganizerType) -> OrganizerTypeItem:
    """Convert OrganizerType model to Schema

    Args:
        model (OrganizerType): A organizer type model instance.

    Returns:
        OrganizerTypeItem: A schema representation of the organizer type.
    """
    return OrganizerTypeItem(id=str(model.id), name=model.name)


def organizer_type_all_response_from_models(
    models: Sequence[OrganizerType],
) -> OrganizerTypeAllResponse:
    """Convert a list of OrganizerType models to OrganizerTypeAllResponse schema."""
    return OrganizerTypeAllResponse(
        results=[organizer_type_item_from_model(model) for model in models]
    )

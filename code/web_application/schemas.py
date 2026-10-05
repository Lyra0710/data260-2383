from datetime import datetime

from pydantic import BaseModel, Field
class VenueCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=500)
    code: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Z0-9-]+$",
    )


class VenueUpdate(VenueCreate):
    pass


class FixtureCreate(BaseModel):
    fixture_name: str = Field(
        min_length=1,
        max_length=255,
    )
    teams: str = Field(
        min_length=1,
        max_length=255,
    )
    fixture_code: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Z0-9-]+$",
    )
    available_slots: int = Field(
        default=0,
        ge=0,
    )
    venue_id: int = Field(gt=0)


class FixtureUpdate(FixtureCreate):
    pass

class RelatedItemOut(BaseModel):
    id: int
    label: str
    details: str


class VenueOut(BaseModel):
    id: int
    name: str
    address: str
    code: str
    created_at: datetime
    updated_at: datetime


class FixtureOut(BaseModel):
    id: int
    fixture_name: str
    teams: str
    fixture_code: str
    available_slots: int
    venue_id: int
    created_at: datetime
    updated_at: datetime
    related_items: list[RelatedItemOut] = []
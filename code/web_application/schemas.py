from datetime import datetime
from enum import Enum
from typing import Literal

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


class FixtureStatus(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class SportType(str, Enum):
    soccer = "soccer"
    basketball = "basketball"
    tennis = "tennis"
    pickleball = "pickleball"


class DocumentFixtureCreate(BaseModel):
    fixture_name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    status: FixtureStatus = FixtureStatus.scheduled
    sport_type: SportType
    scheduled_at: datetime


class DocumentFixtureUpdate(BaseModel):
    fixture_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    status: FixtureStatus | None = None
    sport_type: SportType | None = None
    scheduled_at: datetime | None = None


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    session_id: str | None = Field(default=None, min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4000)
    experiment_id: str | None = Field(default=None, max_length=100)
    experiment_phase: Literal["conversation", "probe"] | None = None


class MemoryMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime


class EpisodicFactOut(BaseModel):
    fact: str
    importance: float


class ChatMemoryUsed(BaseModel):
    short_term_count: int
    short_term_messages: list[MemoryMessageOut]
    long_term_summary: str | None
    episodic_facts: list[EpisodicFactOut]


class ChatResponse(BaseModel):
    reply: str
    memory: ChatMemoryUsed


class FileMemoryCommandRequest(BaseModel):
    command: Literal["/memory", "/compact", "/dream", "/help"]
    recent_messages: list[str] = Field(default_factory=list, max_length=20)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class CurrentUserResponse(BaseModel):
    username: str
    role: Literal["reader", "writer", "moderator"]

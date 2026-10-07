import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EventIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str = Field("wedding", max_length=50)
    date: dt.date | None = None
    time: dt.time | None = None
    venue: str | None = Field(None, max_length=200)
    address: str | None = Field(None, max_length=300)
    waze_url: str | None = Field(None, max_length=500)
    maps_url: str | None = Field(None, max_length=500)
    hosts: str | None = Field(None, max_length=300)
    rsvp_deadline: dt.date | None = None
    default_language: Literal["he", "en"] = "he"
    notes: str | None = None


class EventOut(EventIn):
    model_config = ConfigDict(from_attributes=True)
    id: int

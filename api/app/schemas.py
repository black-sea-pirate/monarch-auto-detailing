import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class QuoteRequestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    contact: str = Field(min_length=5, max_length=200)
    vehicle: str = Field(min_length=2, max_length=160)
    community: str = Field(min_length=2, max_length=120)
    concern: str = Field(min_length=5, max_length=3000)
    source: Literal["website", "card"] = "website"


class QuoteRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    created_at: datetime


class QuoteRequestDraftRead(QuoteRequestRead):
    upload_token: str


class QuoteRequestUploadRead(BaseModel):
    id: uuid.UUID
    kind: Literal["photo", "video"]
    original_name: str
    size_bytes: int
    photo_count: int
    video_count: int
    total_bytes: int


class HealthRead(BaseModel):
    application: str
    environment: str

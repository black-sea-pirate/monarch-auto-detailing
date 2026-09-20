import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuoteRequestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    contact: str = Field(min_length=5, max_length=200)
    contact_method: Literal["whatsapp", "messenger", "telegram", "viber", "sms", "email"]
    vehicle: str = Field(min_length=2, max_length=160)
    community: str = Field(min_length=2, max_length=120)
    concern: str = Field(default="", max_length=2500)
    requested_services: list[str] = Field(default_factory=list, max_length=10)
    source: Literal["website", "card"] = "website"

    @model_validator(mode="after")
    def validate_request_details(self) -> "QuoteRequestCreate":
        if not self.requested_services and not self.concern.strip():
            raise ValueError("Choose at least one service or describe what needs attention.")
        return self


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


class AdminIdentityRead(BaseModel):
    email: str


class AdminQuoteUploadRead(BaseModel):
    id: uuid.UUID
    kind: Literal["photo", "video"]
    original_name: str
    content_type: str
    size_bytes: int
    url: str


class AdminDeliveryRead(BaseModel):
    delivered: bool
    attempts: int
    last_error: str | None
    last_attempt_at: datetime | None


class AdminQuoteListItem(BaseModel):
    id: uuid.UUID
    number: str
    name: str
    vehicle: str
    community: str
    requested_services: list[str]
    status: Literal["new", "viewed", "accepted"]
    photo_count: int
    video_count: int
    created_at: datetime
    viewed_at: datetime | None
    accepted_at: datetime | None
    notification_delivered: bool


class AdminQuoteListRead(BaseModel):
    items: list[AdminQuoteListItem]
    total: int
    new_count: int


class AdminQuoteDetailRead(AdminQuoteListItem):
    contact_method: str
    contact: str
    concern: str
    source: str
    upload_bytes: int
    purge_after: datetime | None
    uploads: list[AdminQuoteUploadRead]
    delivery: AdminDeliveryRead

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


class PriceSetting(BaseModel):
    base_price_cents: int = Field(ge=100, le=1_000_000)
    discount_price_cents: int | None = Field(default=None, ge=100, le=1_000_000)
    discount_enabled: bool = False

    @model_validator(mode="after")
    def validate_discount(self) -> "PriceSetting":
        if self.discount_enabled:
            if self.discount_price_cents is None:
                raise ValueError("Enter a discount price before enabling the discount.")
            if self.discount_price_cents >= self.base_price_cents:
                raise ValueError("The discount price must be lower than the regular price.")
        return self


class SiteSections(BaseModel):
    pricing_enabled: bool = True
    portfolio_enabled: bool = False
    founding_offer_enabled: bool = False


class SiteSettingsUpdate(BaseModel):
    pricing: dict[str, PriceSetting]
    sections: SiteSections
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_price_keys(self) -> "SiteSettingsUpdate":
        from app.site_defaults import PRICE_KEYS

        if set(self.pricing) != set(PRICE_KEYS):
            raise ValueError("Pricing settings are incomplete or contain an unknown service.")
        return self


class SiteSettingsRead(BaseModel):
    pricing: dict[str, PriceSetting]
    sections: SiteSections
    version: int
    updated_at: datetime | None = None
    updated_by: str | None = None


class PortfolioImageRead(BaseModel):
    id: uuid.UUID
    original_name: str
    after_original_name: str | None
    caption: str | None
    sort_order: int
    is_enabled: bool
    size_bytes: int
    after_size_bytes: int | None
    url: str
    after_url: str | None
    created_at: datetime


class PortfolioImageUpdate(BaseModel):
    caption: str | None = Field(default=None, max_length=240)
    is_enabled: bool


class PublicPortfolioImageRead(BaseModel):
    id: uuid.UUID
    caption: str | None
    url: str
    after_url: str | None


class PublicSiteRead(BaseModel):
    pricing: dict[str, PriceSetting]
    sections: SiteSections
    portfolio: list[PublicPortfolioImageRead]
    version: int

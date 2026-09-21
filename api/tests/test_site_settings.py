from collections.abc import AsyncIterator
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.db import get_session
from app.main import app
from app.models import AdminAuditEvent, SiteSettings
from app.routes.admin import require_admin_mutation
from app.schemas import SiteSettingsUpdate
from app.services.admin_auth import AdminIdentity
from app.site_defaults import DEFAULT_PRICING, DEFAULT_SECTIONS


class FakeSiteSession:
    def __init__(self) -> None:
        self.settings = SiteSettings(
            id=1,
            pricing=deepcopy(DEFAULT_PRICING),
            sections=deepcopy(DEFAULT_SECTIONS),
            version=1,
        )
        self.audit_events: list[AdminAuditEvent] = []

    async def get(self, model: type, key: object, **_: object) -> object | None:
        if model is SiteSettings and key == 1:
            return self.settings
        return None

    def add(self, obj: object) -> None:
        if isinstance(obj, AdminAuditEvent):
            self.audit_events.append(obj)

    async def commit(self) -> None:
        pass

    async def refresh(self, _: object) -> None:
        pass


def test_admin_can_publish_a_valid_discount() -> None:
    fake_session = FakeSiteSession()

    async def override_session() -> AsyncIterator[FakeSiteSession]:
        yield fake_session

    async def override_admin() -> AdminIdentity:
        return AdminIdentity(email="owner@example.com")

    pricing = deepcopy(DEFAULT_PRICING)
    pricing["deep"] = {
        "base_price_cents": 17900,
        "discount_price_cents": 15900,
        "discount_enabled": True,
    }
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[require_admin_mutation] = override_admin
    try:
        with TestClient(app) as client:
            response = client.put(
                "/api/v1/admin/site-settings",
                json={
                    "pricing": pricing,
                    "sections": DEFAULT_SECTIONS,
                    "version": 1,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["pricing"]["deep"]["discount_price_cents"] == 15900
    assert response.json()["version"] == 2
    assert [event.action for event in fake_session.audit_events] == ["site_settings_updated"]


def test_discount_must_be_lower_than_regular_price() -> None:
    pricing = deepcopy(DEFAULT_PRICING)
    pricing["maintenance"] = {
        "base_price_cents": 9900,
        "discount_price_cents": 10900,
        "discount_enabled": True,
    }

    with pytest.raises(ValidationError, match="lower than the regular price"):
        SiteSettingsUpdate.model_validate(
            {
                "pricing": pricing,
                "sections": DEFAULT_SECTIONS,
                "version": 1,
            }
        )

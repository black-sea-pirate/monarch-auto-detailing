import uuid
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import app
from app.models import AdminAuditEvent, QuoteRequest
from app.routes.admin import require_admin_mutation
from app.services.admin_auth import AdminIdentity


class FakeAdminSession:
    def __init__(self, quote: QuoteRequest) -> None:
        self.quote = quote
        self.audit_events: list[AdminAuditEvent] = []

    async def get(self, model: type, key: object, **_: object) -> object | None:
        if model is QuoteRequest and key == self.quote.id:
            return self.quote
        return None

    def add(self, obj: object) -> None:
        if isinstance(obj, AdminAuditEvent):
            self.audit_events.append(obj)

    async def commit(self) -> None:
        pass


def test_view_and_accept_are_explicit_separate_states() -> None:
    quote = QuoteRequest(
        id=uuid.uuid4(),
        name="Alex Driver",
        contact="@alex",
        contact_method="telegram",
        vehicle="SUV",
        community="Royal Oak",
        concern="Rear seats",
        requested_services=["Maintenance Interior Clean"],
        source="website",
        status="new",
    )
    fake_session = FakeAdminSession(quote)

    async def override_session() -> AsyncIterator[FakeAdminSession]:
        yield fake_session

    async def override_admin() -> AdminIdentity:
        return AdminIdentity(email="owner@example.com")

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[require_admin_mutation] = override_admin
    try:
        with TestClient(app) as client:
            viewed = client.post(f"/api/v1/admin/quote-requests/{quote.id}/view")
            assert viewed.status_code == 204
            assert quote.status == "viewed"
            assert quote.accepted_at is None

            accepted = client.post(f"/api/v1/admin/quote-requests/{quote.id}/accept")
            assert accepted.status_code == 204
            assert quote.status == "accepted"
            assert quote.accepted_at is not None
            assert quote.purge_after is not None
    finally:
        app.dependency_overrides.clear()

    assert [event.action for event in fake_session.audit_events] == [
        "quote_viewed",
        "quote_accepted",
    ]


def test_admin_endpoint_is_closed_when_authentication_is_not_configured() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/admin/me")

    assert response.status_code == 503

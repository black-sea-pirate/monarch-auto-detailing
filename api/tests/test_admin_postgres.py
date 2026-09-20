import asyncio
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionFactory
from app.main import app
from app.models import AdminAuditEvent, QuoteRequest, QuoteRequestDelivery

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="PostgreSQL integration tests are enabled in CI.",
)


async def _seed_quote(quote_id: uuid.UUID) -> None:
    async with SessionFactory() as session:
        session.add(
            QuoteRequest(
                id=quote_id,
                name="CI Customer",
                contact="ci@example.com",
                contact_method="email",
                vehicle="SUV",
                community="Royal Oak",
                concern="Integration test",
                requested_services=["Maintenance Interior Clean"],
                source="website",
                status="new",
                upload_token_hash="",
                photo_count=0,
                video_count=0,
                upload_bytes=0,
            )
        )
        session.add(QuoteRequestDelivery(quote_id=quote_id, attempts=0))
        await session.commit()


async def _load_quote(quote_id: uuid.UUID) -> QuoteRequest | None:
    async with SessionFactory() as session:
        return await session.get(QuoteRequest, quote_id)


async def _cleanup_quote(quote_id: uuid.UUID) -> None:
    async with SessionFactory() as session:
        await session.execute(delete(AdminAuditEvent).where(AdminAuditEvent.quote_id == quote_id))
        await session.execute(delete(QuoteRequest).where(QuoteRequest.id == quote_id))
        await session.commit()


def test_admin_inbox_with_postgresql() -> None:
    quote_id = uuid.uuid4()
    asyncio.run(_seed_quote(quote_id))
    headers = {"X-Admin-Dev-Token": "ci-admin-token"}

    try:
        with TestClient(app) as client:
            listing = client.get("/api/v1/admin/quote-requests?state=new", headers=headers)
            assert listing.status_code == 200
            assert any(item["id"] == str(quote_id) for item in listing.json()["items"])

            detail = client.get(f"/api/v1/admin/quote-requests/{quote_id}", headers=headers)
            assert detail.status_code == 200
            assert detail.json()["contact"] == "ci@example.com"

            viewed = client.post(
                f"/api/v1/admin/quote-requests/{quote_id}/view",
                headers=headers,
            )
            assert viewed.status_code == 204

            accepted = client.post(
                f"/api/v1/admin/quote-requests/{quote_id}/accept",
                headers=headers,
            )
            assert accepted.status_code == 204

        stored = asyncio.run(_load_quote(quote_id))
        assert stored is not None
        assert stored.status == "accepted"
        assert stored.purge_after is not None
    finally:
        asyncio.run(_cleanup_quote(quote_id))

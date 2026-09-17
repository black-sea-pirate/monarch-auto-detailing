import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import SessionFactory
from app.models import QuoteRequest, QuoteRequestDelivery, QuoteRequestUpload
from app.services.storage import purge_quote_files
from app.services.telegram import deliver_quote

logger = logging.getLogger(__name__)
PURGED_STATUSES = {"accepted_purged", "expired_purged"}


async def purge_quote_data(
    session: AsyncSession,
    quote: QuoteRequest,
    *,
    final_status: str,
) -> None:
    await purge_quote_files(quote.id)
    await session.execute(delete(QuoteRequestUpload).where(QuoteRequestUpload.quote_id == quote.id))
    quote.name = "[purged]"
    quote.contact = ""
    quote.vehicle = ""
    quote.community = ""
    quote.concern = ""
    quote.upload_token_hash = ""
    quote.photo_count = 0
    quote.video_count = 0
    quote.upload_bytes = 0
    quote.status = final_status

    delivery = await session.get(QuoteRequestDelivery, quote.id)
    if delivery is not None:
        now = datetime.now(UTC)
        delivery.purged_at = now
        if final_status == "accepted_purged":
            delivery.accepted_at = now


async def cleanup_expired_quotes() -> None:
    cutoff = datetime.now(UTC) - timedelta(hours=settings.quote_retention_hours)
    async with SessionFactory() as session:
        quotes = list(
            await session.scalars(
                select(QuoteRequest).where(
                    QuoteRequest.created_at < cutoff,
                    QuoteRequest.status.not_in(PURGED_STATUSES),
                )
            )
        )
        for quote in quotes:
            await purge_quote_data(session, quote, final_status="expired_purged")
        if quotes:
            await session.commit()


async def retry_pending_deliveries() -> None:
    if not settings.telegram_enabled:
        return
    async with SessionFactory() as session:
        rows = await session.execute(
            select(QuoteRequest.id, QuoteRequestDelivery.attempts)
            .outerjoin(QuoteRequestDelivery, QuoteRequestDelivery.quote_id == QuoteRequest.id)
            .where(QuoteRequest.status.in_({"stored", "telegram_failed", "telegram_delivering"}))
            .order_by(QuoteRequest.created_at)
            .limit(10)
        )
        quote_ids: list[uuid.UUID] = [
            quote_id for quote_id, attempts in rows if attempts is None or attempts < 5
        ]
    for quote_id in quote_ids:
        await deliver_quote(quote_id)


async def housekeeping_loop() -> None:
    while True:
        await asyncio.sleep(settings.quote_cleanup_interval_seconds)
        try:
            await retry_pending_deliveries()
            await cleanup_expired_quotes()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Quote housekeeping cycle failed")

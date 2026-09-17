import logging
import secrets
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.models import QuoteRequest, QuoteRequestDelivery
from app.services.housekeeping import purge_quote_data
from app.services.telegram import build_quote_summary, telegram

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/telegram", tags=["telegram"])


@router.post("/webhook", include_in_schema=False)
async def telegram_webhook(
    update: dict[str, Any],
    session: Annotated[AsyncSession, Depends(get_session)],
    webhook_secret: Annotated[
        str | None,
        Header(alias="X-Telegram-Bot-Api-Secret-Token"),
    ] = None,
) -> dict[str, bool]:
    expected_secret = settings.telegram_webhook_secret
    if not settings.telegram_enabled or not expected_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram webhook is not configured",
        )
    if webhook_secret is None or not secrets.compare_digest(webhook_secret, expected_secret):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook secret")

    callback = update.get("callback_query")
    if not isinstance(callback, dict):
        return {"ok": True}

    callback_data = callback.get("data")
    callback_id = callback.get("id")
    message = callback.get("message") or {}
    chat = message.get("chat") or {}
    if (
        not isinstance(callback_data, str)
        or not callback_data.startswith("accept:")
        or str(chat.get("id")) != settings.telegram_chat_id
        or not isinstance(callback_id, str)
    ):
        return {"ok": True}

    try:
        quote_id = uuid.UUID(callback_data.removeprefix("accept:"))
    except ValueError:
        return {"ok": True}

    quote = await session.get(QuoteRequest, quote_id)
    delivery = await session.get(QuoteRequestDelivery, quote_id)
    if quote is None or delivery is None:
        try:
            await telegram.answer_callback(callback_id, "Заявка уже очищена.")
        except Exception:
            logger.exception("Could not acknowledge an already-purged Telegram request")
        return {"ok": True}
    if quote.status in {"accepted_purged", "expired_purged"}:
        try:
            await telegram.answer_callback(callback_id, "Заявка уже была принята и очищена.")
        except Exception:
            logger.exception("Could not acknowledge a repeated Telegram callback")
        return {"ok": True}

    accepted_summary = build_quote_summary(quote, accepted=True)
    try:
        await telegram.answer_callback(callback_id, "Принято. Временные данные удаляются.")
    except Exception:
        logger.exception("Could not acknowledge Telegram callback for quote %s", quote_id)
    await purge_quote_data(session, quote, final_status="accepted_purged")
    await session.commit()

    if delivery.summary_message_id is not None:
        try:
            await telegram.mark_accepted(delivery.summary_message_id, accepted_summary)
        except Exception:
            logger.exception("Could not update accepted Telegram message for quote %s", quote_id)
    return {"ok": True}

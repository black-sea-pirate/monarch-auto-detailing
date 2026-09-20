import asyncio
import html
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.config import settings
from app.db import SessionFactory
from app.models import QuoteRequest, QuoteRequestDelivery

logger = logging.getLogger(__name__)
_delivery_lock = asyncio.Lock()


class TelegramAPIError(RuntimeError):
    pass


def _short(value: str, limit: int) -> str:
    return value if len(value) <= limit else f"{value[: limit - 1]}…"


def build_quote_summary(quote: QuoteRequest) -> str:
    request_number = str(quote.id).split("-", 1)[0].upper()
    services = ", ".join(quote.requested_services or []) or "Details in admin"
    return "\n".join(
        [
            "✨ <b>NEW MONARCH REQUEST</b>",
            f"<code>#{request_number}</code> · {html.escape(quote.source.upper())}",
            "",
            f"🚘 <b>Vehicle</b>\n{html.escape(_short(quote.vehicle, 160))}",
            f"📍 <b>Area</b>\n{html.escape(_short(quote.community, 120))}",
            f"🧼 <b>Services</b>\n{html.escape(_short(services, 500))}",
            f"📎 <b>Media</b>\n{quote.photo_count or 0} photo(s) · {quote.video_count or 0} video(s)",
            "",
            "Contact details and media are available only in the protected admin inbox.",
        ]
    )


class TelegramClient:
    def __init__(self) -> None:
        self.base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

    async def _post(self, method: str, json_payload: dict[str, Any]) -> Any:
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{self.base_url}/{method}", json=json_payload)
        try:
            payload = response.json()
        except ValueError as exc:
            raise TelegramAPIError(f"Telegram returned HTTP {response.status_code}.") from exc
        if not response.is_success or not payload.get("ok"):
            description = payload.get("description", f"HTTP {response.status_code}")
            raise TelegramAPIError(str(description))
        return payload.get("result")

    async def send_summary(self, text: str, quote_id: uuid.UUID) -> int:
        request_url = f"{settings.admin_base_url.rstrip('/')}/admin/requests/{quote_id}"
        payload: dict[str, Any] = {
            "chat_id": settings.telegram_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": True},
        }
        if settings.admin_base_url:
            payload["reply_markup"] = {
                "inline_keyboard": [[{"text": "Open secure request", "url": request_url}]]
            }
        result = await self._post("sendMessage", payload)
        return int(result["message_id"])

    async def delete_webhook(self) -> None:
        await self._post("deleteWebhook", {"drop_pending_updates": True})


telegram = TelegramClient()


def _retry_delay(attempts: int) -> timedelta:
    minutes = min(360, 2 ** min(max(attempts, 1), 9))
    return timedelta(minutes=minutes)


async def deliver_quote(quote_id: uuid.UUID) -> None:
    if not settings.telegram_enabled:
        return

    async with _delivery_lock, SessionFactory() as session:
        quote = await session.get(QuoteRequest, quote_id)
        if quote is None or quote.status not in {"new", "viewed", "accepted"}:
            return

        delivery = await session.get(QuoteRequestDelivery, quote_id)
        if delivery is None:
            delivery = QuoteRequestDelivery(quote_id=quote_id, attempts=0)
            session.add(delivery)
        if delivery.delivered_at is not None:
            return

        now = datetime.now(UTC)
        delivery.attempts += 1
        delivery.last_attempt_at = now
        delivery.next_attempt_at = now + _retry_delay(delivery.attempts)
        delivery.telegram_chat_id = settings.telegram_chat_id
        await session.commit()

        try:
            delivery.summary_message_id = await telegram.send_summary(
                build_quote_summary(quote), quote_id
            )
            delivery.delivered_at = datetime.now(UTC)
            delivery.next_attempt_at = None
            delivery.last_error = None
            await session.commit()
        except Exception as exc:
            logger.exception("Telegram delivery failed for quote %s", quote_id)
            delivery.last_error = _short(str(exc), 2000)
            await session.commit()


async def disable_telegram_webhook() -> None:
    if not settings.telegram_enabled:
        return
    try:
        await telegram.delete_webhook()
    except Exception:
        logger.exception("Telegram webhook removal failed")

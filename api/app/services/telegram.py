import asyncio
import html
import json
import logging
import uuid
from contextlib import ExitStack
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select

from app.config import settings
from app.db import SessionFactory
from app.models import QuoteRequest, QuoteRequestDelivery, QuoteRequestUpload
from app.services.storage import resolve_upload_path

logger = logging.getLogger(__name__)
_delivery_lock = asyncio.Lock()
TELEGRAM_SEND_PHOTO_MAX_BYTES = 10 * 1024 * 1024


class TelegramAPIError(RuntimeError):
    pass


def _short(value: str, limit: int) -> str:
    return value if len(value) <= limit else f"{value[: limit - 1]}…"


def build_quote_summary(quote: QuoteRequest, *, accepted: bool = False) -> str:
    heading = "✅ <b>ACCEPTED · MONARCH</b>" if accepted else "✨ <b>NEW MONARCH REQUEST</b>"
    request_number = str(quote.id).split("-", 1)[0].upper()
    return "\n".join(
        [
            heading,
            f"<code>#{request_number}</code>  ·  {html.escape(quote.source.upper())}",
            "",
            f"👤 <b>Client</b>\n{html.escape(_short(quote.name, 180))}",
            f"💬 <b>Contact</b>\n{html.escape(_short(quote.contact, 260))}",
            f"🚘 <b>Vehicle</b>\n{html.escape(_short(quote.vehicle, 220))}",
            f"📍 <b>Community</b>\n{html.escape(_short(quote.community, 180))}",
            f"🧼 <b>Needs attention</b>\n{html.escape(_short(quote.concern, 2200))}",
            f"📎 <b>Media</b>\n{quote.photo_count or 0} photo(s) · {quote.video_count or 0} video(s)",
            "",
            "Tap the button after the request has been saved outside the website.",
        ]
    )


class TelegramClient:
    def __init__(self) -> None:
        self.base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

    async def _post(
        self,
        method: str,
        *,
        json_payload: dict[str, Any] | None = None,
        data: dict[str, str] | None = None,
        files: dict[str, tuple[str, Any, str]] | None = None,
    ) -> Any:
        timeout = httpx.Timeout(180.0, connect=20.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.base_url}/{method}",
                json=json_payload,
                data=data,
                files=files,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise TelegramAPIError(f"Telegram returned HTTP {response.status_code}.") from exc
        if not response.is_success or not payload.get("ok"):
            description = payload.get("description", f"HTTP {response.status_code}")
            raise TelegramAPIError(str(description))
        return payload.get("result")

    async def send_summary(self, text: str) -> int:
        result = await self._post(
            "sendMessage",
            json_payload={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "HTML",
                "link_preview_options": {"is_disabled": True},
            },
        )
        return int(result["message_id"])

    async def send_photo_group(self, uploads: list[QuoteRequestUpload]) -> list[int]:
        if len(uploads) == 1:
            return [await self.send_upload(uploads[0])]

        media: list[dict[str, str]] = []
        with ExitStack() as stack:
            files: dict[str, tuple[str, Any, str]] = {}
            for index, upload in enumerate(uploads):
                field_name = f"photo_{index}"
                path = resolve_upload_path(upload.stored_name)
                handle = stack.enter_context(path.open("rb"))
                files[field_name] = (upload.original_name, handle, upload.content_type)
                media.append({"type": "photo", "media": f"attach://{field_name}"})
            result = await self._post(
                "sendMediaGroup",
                data={
                    "chat_id": settings.telegram_chat_id,
                    "media": json.dumps(media),
                },
                files=files,
            )
        return [int(message["message_id"]) for message in result]

    async def send_upload(self, upload: QuoteRequestUpload) -> int:
        path = resolve_upload_path(upload.stored_name)
        method = "sendDocument"
        field = "document"
        if upload.kind == "photo" and upload.content_type in {
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            method, field = "sendPhoto", "photo"
        elif upload.kind == "video" and upload.content_type == "video/mp4":
            method, field = "sendVideo", "video"

        with path.open("rb") as handle:
            result = await self._post(
                method,
                data={"chat_id": settings.telegram_chat_id},
                files={field: (upload.original_name, handle, upload.content_type)},
            )
        return int(result["message_id"])

    async def add_accept_button(self, message_id: int, quote_id: uuid.UUID) -> None:
        await self._post(
            "editMessageReplyMarkup",
            json_payload={
                "chat_id": settings.telegram_chat_id,
                "message_id": message_id,
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {
                                "text": "✅ Принял",
                                "callback_data": f"accept:{quote_id}",
                            }
                        ]
                    ]
                },
            },
        )

    async def mark_accepted(self, message_id: int, text: str) -> None:
        await self._post(
            "editMessageText",
            json_payload={
                "chat_id": settings.telegram_chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": "HTML",
                "link_preview_options": {"is_disabled": True},
                "reply_markup": {"inline_keyboard": []},
            },
        )

    async def answer_callback(self, callback_id: str, text: str) -> None:
        await self._post(
            "answerCallbackQuery",
            json_payload={"callback_query_id": callback_id, "text": text},
        )

    async def configure_webhook(self) -> None:
        if not settings.telegram_webhook_url or not settings.telegram_webhook_secret:
            return
        await self._post(
            "setWebhook",
            json_payload={
                "url": settings.telegram_webhook_url,
                "secret_token": settings.telegram_webhook_secret,
                "allowed_updates": ["callback_query"],
            },
        )


telegram = TelegramClient()


async def deliver_quote(quote_id: uuid.UUID) -> None:
    if not settings.telegram_enabled:
        return

    async with _delivery_lock, SessionFactory() as session:
        quote = await session.get(QuoteRequest, quote_id)
        if quote is None or quote.status in {
            "telegram_delivered",
            "accepted_purged",
            "expired_purged",
        }:
            return

        delivery = await session.get(QuoteRequestDelivery, quote_id)
        if delivery is None:
            delivery = QuoteRequestDelivery(quote_id=quote_id, attempts=0)
            session.add(delivery)
        delivery.attempts += 1
        delivery.telegram_chat_id = settings.telegram_chat_id
        quote.status = "telegram_delivering"
        await session.commit()

        try:
            if delivery.summary_message_id is None:
                delivery.summary_message_id = await telegram.send_summary(
                    build_quote_summary(quote)
                )
                await session.commit()

            uploads = list(
                await session.scalars(
                    select(QuoteRequestUpload)
                    .where(
                        QuoteRequestUpload.quote_id == quote_id,
                        QuoteRequestUpload.delivered_at.is_(None),
                    )
                    .order_by(QuoteRequestUpload.created_at, QuoteRequestUpload.id)
                )
            )
            standard_photos = [
                upload
                for upload in uploads
                if upload.kind == "photo"
                and upload.content_type in {"image/jpeg", "image/png", "image/webp"}
                and upload.size_bytes <= TELEGRAM_SEND_PHOTO_MAX_BYTES
            ]
            other_uploads = [upload for upload in uploads if upload not in standard_photos]

            for start in range(0, len(standard_photos), 10):
                group = standard_photos[start : start + 10]
                message_ids = await telegram.send_photo_group(group)
                delivered_at = datetime.now(UTC)
                for upload, message_id in zip(group, message_ids, strict=True):
                    upload.telegram_message_id = message_id
                    upload.delivered_at = delivered_at
                await session.commit()

            for upload in other_uploads:
                upload.telegram_message_id = await telegram.send_upload(upload)
                upload.delivered_at = datetime.now(UTC)
                await session.commit()

            await telegram.add_accept_button(delivery.summary_message_id, quote_id)
            delivered_at = datetime.now(UTC)
            delivery.delivered_at = delivered_at
            delivery.last_error = None
            quote.status = "telegram_delivered"
            await session.commit()
        except Exception as exc:
            logger.exception("Telegram delivery failed for quote %s", quote_id)
            delivery.last_error = _short(str(exc), 2000)
            quote.status = "telegram_failed"
            await session.commit()


async def configure_telegram_webhook() -> None:
    if not settings.telegram_enabled:
        return
    try:
        await telegram.configure_webhook()
    except Exception:
        logger.exception("Telegram webhook configuration failed")

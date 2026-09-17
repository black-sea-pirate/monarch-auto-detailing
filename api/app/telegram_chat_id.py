import asyncio

import httpx

from app.config import settings


async def show_private_chat_ids() -> None:
    if not settings.telegram_bot_token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN first, then restart the API container.")

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/getUpdates"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params={"allowed_updates": '["message"]'})
        response.raise_for_status()
        payload = response.json()

    chats: dict[int, str] = {}
    for update in payload.get("result", []):
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        if chat.get("type") != "private" or not isinstance(chat.get("id"), int):
            continue
        label = " ".join(part for part in [chat.get("first_name"), chat.get("last_name")] if part)
        username = f"@{chat['username']}" if chat.get("username") else "no username"
        chats[chat["id"]] = f"{label or 'Unknown user'} ({username})"

    if not chats:
        raise SystemExit("No private chats found. Send /start to the bot and run this again.")
    for chat_id, label in chats.items():
        print(f"TELEGRAM_CHAT_ID={chat_id}  # {label}")


if __name__ == "__main__":
    asyncio.run(show_private_chat_ids())

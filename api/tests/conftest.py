import os

# Tests must never contact the owner's real Telegram bot when pytest is started
# from a directory containing a populated .env file.
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""

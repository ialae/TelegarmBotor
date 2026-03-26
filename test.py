import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

API_ID = int(os.getenv("TEST_TELEGRAM_API_ID"))
API_HASH = os.getenv("TEST_TELEGRAM_API_HASH")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("Your session string:")
    print(client.session.save())
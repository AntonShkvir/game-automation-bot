import time

import pyautogui
from pyrogram import Client
from telethon import TelegramClient

from bot.config import settings
from bot.utils import logger


# async def register_sessions(apiid, apihash) -> None:
#     API_ID = int(apiid)
#     API_HASH = apihash
#
#     if not API_ID or not API_HASH:
#         raise ValueError("API_ID and API_HASH not found in the .env file.")
#
#     session_name = input('\nEnter the session name (press Enter to exit): ')
#
#     if not session_name:
#         return None
#
#     session = Client(
#         name=session_name,
#         api_id=API_ID,
#         api_hash=API_HASH,
#         workdir="sessions/"
#     )
#
#
#     async with session:
#         user_data = await session.get_me()
#
#     logger.success(f'Session added successfully @{user_data.username} | {user_data.first_name} {user_data.last_name}')


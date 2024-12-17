import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from globals import AuthU
from plugins.authers import is_authorized


# Environment variables
API_ID = Config.API_ID
API_HASH = Config.API_HASH
BOT_TOKEN = Config.BOT_TOKEN
OWNER = Config.OWNER

# Initialize Pyrogram client
plugins = dict(root="plugins")
app = Client("m3u8_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN,plugins=plugins)

# Run the bot
app.run()

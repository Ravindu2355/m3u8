import os, asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Func.simples import mention_user, generate_thumbnail, get_tg_filename, teralinks_ex, extract_terabox_surl
from Func.m3u8 import download_and_convert_video
from plugins.authers import is_authorized

@Client.on_message(filters.regex(r'https?://[^\s]+'))
async def handle_link(client, message):
  link = message.text
  teralink =""
  if not is_authorized(message.chat.id):
      await message.reply("**❌️You are not my auther for use me!...❌️**")
      return
  if "tera" in link and "links" in link:
    id=link.split('/')[-1]
    tera_link = teralinks_ex(id)
  elif "tera" in link and "/s/" in link:
    tera_link = link
  else:
    await message.reply('❌️Not Terabox link')
    tera_link = None
  if tera_link:
    surl = extract_terabox_surl(tera_link)
    if surl:
      

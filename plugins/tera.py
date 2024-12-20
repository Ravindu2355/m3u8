import os, asyncio, json
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Func.simples import mention_user, generate_thumbnail, get_tg_filename, url_encode
from Func.m3u8 import download_and_convert_video
import requests
from config import Config


async def extract_tera(str, msg:Message):
    if not str:
        return None
    #str = url_encode(str)
    # Construct the URL
    #url = f"{Config.TeraExScript}?pw={Config.PW}&shorturl={str}"
    req = {
        "shorturl":str,
        "pw":Config.PW
    }
    try:
        # Send the GET request
        response = requests.post(Config.TeraExScript,json=req)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
    except requests.exceptions.RequestException as e:
        # Handle request errors (like network issues)
        print(f"Error fetching data: {e}")
        await msg.reply(f"Err exurl Fetch: {e}")
        return None
    
    try:
        # Parse the JSON response
        j = response.json()
    except ValueError:
        # Handle JSON parsing errors
        print("Error parsing JSON response")
        await msg.reply(f"Json parse Err")
        return None
    
    # Extract data and construct the m3u8 URL
    if j["s"] == 0:
        emsg=j["msg"]
        await msg.reply(f"Ex url returned  Err: {emsg}")
        return None
    m3u8_url = j["d"]["m3u8Url"]
    if m3u8_url:
       await msg.reply(f"**🔯Found M3U8: {m3u8_url} \n🔰Download will start soon!**")
       return m3u8_url
    else:
       emsg=j["msg"]
       await msg.reply(f"No m3u8: {emsg}")
       return None



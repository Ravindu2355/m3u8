import os, asyncio, json
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Func.simples import mention_user, generate_thumbnail, get_tg_filename, url_encode
from Func.m3u8 import download_and_convert_video
import requests
from config import Config
import aiohttp

async def extera_wd(url, msg):
    await msg.edit_text("**🟢Trying wd extraction getting!...**")
    api_url = f"https://wdzone-terabox-api.vercel.app/api?url={url}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url) as response:
                response.raise_for_status()  # Raise an error for HTTP errors
                data = await response.json()
                
                if "✅ Status" in data and data["✅ Status"] == "Success":
                    return {"status": "ok", "data": data}
                else:
                    await msg.edit_text("**🔴Extraction failed**")
                    return {"status": "error", "msg": "Extraction failed"}

        except aiohttp.ClientError as e:
            await msg.edit_text(f"🔴Err on fetching: {str(e)}")
            return {"status": "error", "msg": str(e)}


async def extract_tera(str, msg: Message):
    await msg.edit_text("**🟢Trying M3U8 360p getting!...**")
    if not str:
        return None

    req = {
        "shorturl": str,
        "pw": Config.PW
    }

    try:
        # Send the POST request asynchronously
        async with aiohttp.ClientSession() as session:
            async with session.post(Config.TeraExScript, json=req) as response:
                if response.status != 200:
                    # Handle non-2xx responses
                    await msg.reply(f"Err exurl Fetch: {response.status}")
                    return None
                j = await response.json()  # Parse JSON response

    except aiohttp.ClientError as e:
        # Handle request errors (like network issues)
        await msg.reply(f"Err exurl Fetch: {e}")
        return None

    # Extract data and construct the m3u8 URL
    if j.get("s") == 0:
        emsg = j.get("msg", "Unknown error")
        await msg.reply(f"Ex url returned Err: {emsg}")
        return None

    m3u8_url = j.get("d", {}).get("m3u8Url")
    if m3u8_url:
        await msg.reply(f"**🔯Found M3U8: {m3u8_url} \n🔰Download will start soon!**")
        return m3u8_url
    else:
        emsg = j.get("msg", "No m3u8Url found")
        await msg.reply(f"No m3u8: {emsg}")
        return None



async def eextract_tera(str, msg:Message):
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



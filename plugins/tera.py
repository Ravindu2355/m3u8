import os, asyncio, json
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Func.simples import mention_user, generate_thumbnail, get_tg_filename
from Func.m3u8 import download_and_convert_video
import requests

def extract_tera(str):
    if not str:
        return None
    
    # Construct the URL
    url = f"https://www.1024terabox.com/api/shorturlinfo?app_id=250528&web=1&channel=dubox&clienttype=5&jsToken=9A3D6A68CB44D9B527082086BFE0711B7BE766E8295E50831CB8D16C54AD6FF2848ABE19BB5150B95C57828ABB9D89314DDFCB43E17079449E2E09ECCF6D39F645E05F726419DBDA8E94C9FCED1A80E13647EC1809B39DF983331D7EB4CA72D7FACEFB9B209EE65AE29D0E5F072F448F3358E70C80F256FB568CB2B19E0896BE&dp-logid=61407400196680270002&shorturl={str}&root=1&scene="
  
    try:
        # Send the GET request
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
    except requests.exceptions.RequestException as e:
        # Handle request errors (like network issues)
        print(f"Error fetching data: {e}")
        return None
    
    try:
        # Parse the JSON response
        j = response.json()
    except ValueError:
        # Handle JSON parsing errors
        print("Error parsing JSON response")
        return None
    
    # Extract data and construct the m3u8 URL
    m3u8_url = f"https://www.1024terabox.com/share/extstreaming.m3u8?uk={j['uk']}&shareid={j['shareid']}&type=M3U8_AUTO_360&fid={j['list'][0]['fs_id']}&sign={j['sign']}&timestamp={j['timestamp']}&jsToken=9A3D6A68CB44D9B527082086BFE0711B7BE766E8295E50831CB8D16C54AD6FF2848ABE19BB5150B95C57828ABB9D89314DDFCB43E17079449E2E09ECCF6D39F645E05F726419DBDA8E94C9FCED1A80E13647EC1809B39DF983331D7EB4CA72D7FACEFB9B209EE65AE29D0E5F072F448F3358E70C80F256FB568CB2B19E0896BE&esl=1&isplayer=1&ehps=1&clienttype=5&app_id=250528&web=1&channel=dubox"
    
    return m3u8_url



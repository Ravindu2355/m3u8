import os, asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Func.simples import mention_user, generate_thumbnail, get_tg_filename, teralinks_ex, extract_terabox_surl
from Func.m3u8 import download_and_convert_video
from plugins.authers import is_authorized
from plugins.tera import extract_tera, extera_wd
from plugins.m3u8_handle import dl_m3u8
from Func.downloader import dl
from plugins.tgup import upload_file

@Client.on_message(filters.regex(r'https?://[^\s]+'))
async def handle_link(client, message):
  link = message.text
  if not is_authorized(message.chat.id):
      await message.reply("**❌️You are not my auther for use me!...❌️**")
      return
  rmsg= await message.reply("🪚**Starting..**")
  if "tera" in link:
    teralink = ""
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
         wdt = await extera_wd(tera_link, rmsg)
         if wdt["status"] == "ok":
           data = wdt["data"]["📜 Extracted Info"][0]
           prm = f"🟢Extracted\n  Name : {data['📂 Title']}\nSize : {data['📏 Size']}\nUrl : {data['🔽 Direct Download Link']}\n"
           await rmsg.reply(prm)
           dlj = await dl(data["🔽 Direct Download Link"], rmsg)
           if not "error" in dlj:
             up = await upload_file(client, message.chat.id, dlj['file_path'], rmsg)
           else:
             dl_link = await extract_tera(surl, rmsg)
             if dl_link:
               await prm.delete()
               message.text = f"/m3u8 {dl_link}"
               await dl_m3u8(client,message)
         else:
           dl_link = await extract_tera(surl, message)
           if dl_link:
               message.text = f"/m3u8 {dl_link}"
               await dl_m3u8(client,message)
      else:
        await rmsg.edit_text(f"🤕** Sorry! cant get surl from {tera_link}")
    else:
      await rmsg.edit_text(f"🤕Sorry Cant regognize this is valid {tera_link}")
  else:
    await rmsg.edit_text("🤕**Sorry I cannot download that link!...**") 
    return None
        

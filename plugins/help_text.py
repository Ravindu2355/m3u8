from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from globals import AuthU
from Func.simples import mention_user

@Client.on_message(filters.command("start"))
async def st_rep(client,message:Message):
    await message.reply(f"**🔰RVX M3U8 Downloader🔰\n\n❤️Welcome {mention_user(message)}💪!\n😎I am an simple M3U8 link uploader bot.\n😊Give me a m3u8 link with `/m3u8 <DirectLink>` and \n😇I will upload it to telegram as `video - mp4`😎**")

@Client.on_message(filters.command("help"))
async def st_help(client,message:Message):
    await message.reply("🫠**No avalable!**\n\n**Commands: **\n\n  /start\n  /help\n  /checkauth\n  /addauth\n  /removeauth\n  /m3u8\n  /logo : use carefully")

@Client.on_callback_query(filters.regex(r"cancel"))
async def cancelQ(client,query):
    await query.message.edit_text("🔰Operation cancelled.🪚")


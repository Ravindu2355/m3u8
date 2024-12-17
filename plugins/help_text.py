from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from globals import AuthU
from Func.simples import mention_user

@Client.on_message(filters.command("start"))
async def st_rep(client,message:Message):
    await message.reply(f"**🔰RVX M3U8 Downloader🔰\n\n❤️Welcome {mention_user(message)}💪!\n🔰I am an simple M3U8 link uploader bot.🔰Give me a m3u8 link with `/m3u8 <DirectLink>` and \n😇I will upload it to telegram as `video - mp4`🫡😎**")

import os
import time
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from globals import AuthU
from Func.simples import mention_user, progress_callback, generate_thumbnail
from Func.add_logo import download_video_with_logo
from plugins.authers import is_authorized



@Client.on_message(filters.command("logo"))
async def dl_m3u8(client,message:Message):
    global AuthU
    try:
        args = message.text.split(" ", 1)
        if not is_authorized(message.chat.id):
            await message.reply("**❌️You are not my auther for use me!...❌️**")
            return
        if len(args) < 2:
            await message.reply("Please provide an m3u8 URL. Example: `/download m3u8url`")
            return

        m3u8_url = args[1].strip()
        msg = await message.reply("✅ **Starting download and conversion...**")
        start_time = time.time()

        # File paths
        output_file = "output.mp4"
        thumb_file = "thumb.jpg"

        duration = await download_video_with_logo(msg, m3u8_url, output_file)

        if not os.path.exists(output_file):
            await msg.edit_text("❌ Failed to download or convert the video.")
            return

        # Generate thumbnail
        await msg.edit_text("🖼 **Generating thumbnail...**")
        generate_thumbnail(output_file, thumb_file)

        # Upload to Telegram
        await msg.edit_text("📤 **Uploading video with thumbnail...**")
        upload_start_time = time.time()

        with open(output_file, "rb") as video, open(thumb_file, "rb") as thumb:
            await client.send_video(
                chat_id=message.chat.id,
                video=video,
                duration=int(duration),
                thumb=thumb,  # Attach the generated thumbnail
                caption="✅ **Here is yor video!** ✅️",
                supports_streaming=True,  # Enables streaming
                progress=progress_callback,
                progress_args=(msg, upload_start_time)
            )

        #await message.reply("✅ **Upload complete!**")
        await msg.delete();
        os.remove(output_file)
        os.remove(thumb_file)

    except Exception as e:
        await message.reply(f"❌ An error occurred: {str(e)}")

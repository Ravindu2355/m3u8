import os
import time
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from globals import AuthU
from Func.simples import mention_user, progress_callback, generate_thumbnail


# Environment variables
API_ID = Config.API_ID
API_HASH = Config.API_HASH
BOT_TOKEN = Config.BOT_TOKEN
OWNER = Config.OWNER

# Initialize Pyrogram client
plugins = dict(root="plugins")
app = Client("m3u8_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN,plugins=plugins)




@app.on_message(filters.command("start"))
async def st_rep(client,message:Message):
    await message.reply(f"**🔰RVX M3U8 Downloader🔰\n\n❤️Welcome {mention_user(message)}💪!\n🔰I am an simple M3U8 link uploader bot.🔰Give me a m3u8 link with `/m3u8 <m3u8 direct link>` and \n😇I will upload it to telegram as `video - mp4`🫡😎**")

# Command to download and process video
@app.on_message(filters.command("m3u8"))
async def download_m3u8(client, message: Message):
    try:
        args = message.text.split(" ", 1)
        if str(message.chat.id) not in AuthU:
            await message.reply("**❌️You are not my auther for use me!...❌️**")
            return
        if len(args) < 2:
            await message.reply("Please provide an m3u8 URL. Example: `/download <m3u8_url>`")
            return

        m3u8_url = args[1].strip()
        msg = await message.reply("✅ **Starting download and conversion...**")
        start_time = time.time()

        # File paths
        output_file = "output.mp4"
        thumb_file = "thumb.jpg"

        # FFmpeg command to download and convert
        await msg.edit_text("📥 **Downloading and converting the video...**")
        ffmpeg_command = [
            "ffmpeg", "-i", m3u8_url, "-c", "copy", "-bsf:a", "aac_adtstoasc", output_file
        ]
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        last_update = time.time()

        # Progress updates every 10 seconds
        while process.poll() is None:
            if time.time() - last_update > 10:
                await msg.edit_text("⏳ **FFmpeg is processing...** Please wait.")
                last_update = time.time()

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
                thumb=thumb,  # Attach the generated thumbnail
                caption="✅ **Here is yor video!** ✅️",
                supports_streaming=True,  # Enables streaming
                progress=progress_callback,
                progress_args=(message, upload_start_time)
            )

        #await message.reply("✅ **Upload complete!**")
        await msg.delete();
        os.remove(output_file)
        os.remove(thumb_file)

    except Exception as e:
        await message.reply(f"❌ An error occurred: {str(e)}")

# Run the bot
app.run()

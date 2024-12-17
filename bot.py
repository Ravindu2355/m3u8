import os
import time
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message

# Environment variables
API_ID = int(os.getenv("apiid"))
API_HASH = os.getenv("apihash")
BOT_TOKEN = os.getenv("tk")

# Initialize Pyrogram client
app = Client("m3u8_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Progress callback for uploads
def progress_callback(current, total, message: Message, start_time):
    elapsed_time = time.time() - start_time
    progress = (current / total) * 100
    speed = current / elapsed_time / 1024
    eta = (total - current) / (speed * 1024) if speed > 0 else 0

    progress_msg = (
        f"**Progress**: {progress:.2f}%\n"
        f"**Speed**: {speed:.2f} KB/s\n"
        f"**Elapsed Time**: {int(elapsed_time)}s\n"
        f"**ETA**: {int(eta)}s"
    )
    try:
        message.edit_text(progress_msg)
    except:
        pass

# Generate thumbnail using ffmpeg
def generate_thumbnail(video_path, thumb_path, time_stamp="00:00:05"):
    command = [
        "ffmpeg", "-i", video_path, "-ss", time_stamp, "-vframes", "1", thumb_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Command to download and process video
@app.on_message(filters.command("download"))
async def download_m3u8(client, message: Message):
    try:
        args = message.text.split(" ", 1)
        if len(args) < 2:
            await message.reply("Please provide an m3u8 URL. Example: `/download <m3u8_url>`")
            return

        m3u8_url = args[1].strip()
        await message.reply("✅ **Starting download and conversion...**")
        start_time = time.time()

        # File paths
        output_file = "output.mp4"
        thumb_file = "thumb.jpg"

        # FFmpeg command to download and convert
        await message.reply("📥 **Downloading and converting the video...**")
        ffmpeg_command = [
            "ffmpeg", "-i", m3u8_url, "-c", "copy", "-bsf:a", "aac_adtstoasc", output_file
        ]
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        last_update = time.time()

        # Progress updates every 10 seconds
        while process.poll() is None:
            if time.time() - last_update > 10:
                await message.reply("⏳ **FFmpeg is processing...** Please wait.")
                last_update = time.time()

        if not os.path.exists(output_file):
            await message.reply("❌ Failed to download or convert the video.")
            return

        # Generate thumbnail
        await message.reply("🖼 **Generating thumbnail...**")
        generate_thumbnail(output_file, thumb_file)

        # Upload to Telegram
        await message.reply("📤 **Uploading video with thumbnail...**")
        upload_start_time = time.time()

        with open(output_file, "rb") as video, open(thumb_file, "rb") as thumb:
            await client.send_video(
                chat_id=message.chat.id,
                video=video,
                thumb=thumb,  # Attach the generated thumbnail
                caption="✅ **Here is your streamable video!**",
                supports_streaming=True,  # Enables streaming
                progress=progress_callback,
                progress_args=(message, upload_start_time)
            )

        await message.reply("✅ **Upload complete!**")
        os.remove(output_file)
        os.remove(thumb_file)

    except Exception as e:
        await message.reply(f"❌ An error occurred: {str(e)}")

# Run the bot
app.run()

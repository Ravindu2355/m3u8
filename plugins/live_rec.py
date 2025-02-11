import subprocess
import datetime
import os
import time
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

# Max file size limit (1.99GB)
MAX_FILE_SIZE = 1.99 * 1024 * 1024 * 1024  # 1.99GB in bytes

async def upload_and_start_new_file(bot, message, output_file, start_time):
    """
    Uploads the current file and starts recording a new one.
    """
    try:
        if os.path.exists(output_file):
            await message.reply("✅ Recording complete! Uploading now...")

            # Upload the video to Telegram
            await bot.send_video(
                chat_id=message.chat.id,
                video=output_file,
                caption=f"🎬 **Recording Complete!**\nDuration: {int(time.time() - start_time)} sec."
            )

            # Delete the file after sending
            os.remove(output_file)
    except Exception as e:
        await message.reply(f"❌ Error during upload: {e}")

async def update_progress_message(bot, message, output_file, start_time):
    """
    Updates the progress message every 10 seconds with current recorded time and size.
    """
    while os.path.exists(output_file):
        # Calculate elapsed time and file size
        elapsed_time = int(time.time() - start_time)
        file_size = os.path.getsize(output_file) / (1024 * 1024)  # Convert to MB

        progress_message = f"🟢 RECORDING 🟢\n"
        progress_message += f"📁 Name: {output_file}\n"
        progress_message += f"⏳ Recorded Time: {elapsed_time} sec\n"
        progress_message += f"💾 Size: {file_size:.2f} MB"

        try:
            # Update the message every 10 seconds
            await message.edit(progress_message)
        except Exception as e:
            print(f"Error updating progress message: {e}")
        
        time.sleep(10)  # Sleep for 10 seconds before updating the message

async def record_m3u8(bot, message, url, total_duration):
    """
    Records an M3U8 stream continuously in chunks, uploading every 1.99GB.
    """
    current_duration = 0
    file_index = 1
    while current_duration < total_duration:
        output_file = f"record_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{file_index}.mp4"
        start_time = time.time()

        command = [
            "ffmpeg", "-i", url, "-c:v", "copy", "-c:a", "copy",
            "-t", str(min(3600, total_duration - current_duration)), output_file
        ]
        
        process = subprocess.Popen(command)

        # Start progress message
        progress_message = await message.reply("🎥 Recording started...", quote=True)
        await update_progress_message(bot, progress_message, output_file, start_time)

        while process.poll() is None:
            # Check the file size every 5 seconds
            time.sleep(5)
            if os.path.exists(output_file) and os.path.getsize(output_file) >= MAX_FILE_SIZE:
                process.terminate()  # Stop recording if file exceeds 1.99GB
                break

        await upload_and_start_new_file(bot, message, output_file, start_time)

        # Increase the duration and file index for the next chunk
        current_duration += 3600  # 1 hour chunks
        file_index += 1

@Client.on_message(filters.command("record"))
async def record_command(bot, message):
    """
    Command: /record <M3U8_URL> <duration_in_seconds>
    Example: /record https://example.com/live.m3u8 14400
    """
    try:
        args = message.text.split()
        if len(args) != 3:
            await message.reply("❌ Usage: `/record <M3U8_URL> <duration_in_seconds>`", quote=True)
            return

        m3u8_url = args[1]
        total_duration = int(args[2])

        recording_message = await message.reply("🎥 Recording started...", quote=True)
        await record_m3u8(bot, recording_message, m3u8_url, total_duration)

    except Exception as e:
        await message.reply(f"❌ Error: {e}")

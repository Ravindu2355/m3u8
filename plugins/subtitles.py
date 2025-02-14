import os
import time
import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Store user data
user_files = {}

# Command to handle video messages
#@Client.on_message(filters.video & filters.private)
#async def video_handler(bot, message):
    #user_files[message.from_user.id] = {"video": message.video.file_id}
    #await message.reply_text("Now, please send me the **SRT** or **ASS** subtitle file by replying to this video.")

# Command to handle subtitle files
@Client.on_message(filters.document & filters.private)
async def subtitle_handler(bot, message):
    if message.from_user.id not in user_files or "video" not in user_files[message.from_user.id]:
        return await message.reply_text("Please send a **video first**, then reply with the subtitle file.")

    file_ext = message.document.file_name.split(".")[-1].lower()
    if file_ext not in ["srt", "ass"]:
        #await message.reply_text("Only **SRT** or **ASS** subtitle files are supported.")
        return 

    user_files[message.from_user.id]["subtitle"] = message.document.file_id
    await message.reply_text(
        "**Select the subtitle method:**\n\n **Burn-in**:Best method.That subs are pernement part of video.\n **Move_text**:Also working in most of devices but some tvs will not supporting.but faster than burn-in",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Burn-in (Hardcoded/Slow)", callback_data="burn")],
            [InlineKeyboardButton("📝 Move Text (Softcoded/Fast)", callback_data="mov_text")]
        ])
    )

# Handle subtitle merging method
@Client.on_callback_query(filters.regex("burn|mov_text"))
async def process_subtitles(bot, query):
    user_id = query.from_user.id
    if user_id not in user_files or "video" not in user_files[user_id] or "subtitle" not in user_files[user_id]:
        return await query.message.edit_text("Something went wrong. Please restart the process.")

    method = query.data
    video_path = f"{user_id}_video.mp4"
    sub_path = f"{user_id}_sub.srt"
    output_path = f"{user_id}_output.mp4"

    # Download video and subtitle files
    msg = await query.message.edit_text("Downloading files...")
    video = await bot.download_media(user_files[user_id]["video"], file_name=video_path)
    subtitle = await bot.download_media(user_files[user_id]["subtitle"], file_name=sub_path)

    await msg.edit_text("Merging subtitles...")

    # Select FFmpeg command based on method
    if method == "burn":
        ffmpeg_cmd = [
            "ffmpeg", "-i", video_path, "-vf", f"subtitles={sub_path}", "-c:a", "copy", output_path
        ]
    else:
        ffmpeg_cmd = [
            "ffmpeg", "-i", video_path, "-i", sub_path, "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text", output_path
        ]

    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    start_time = time.time()

    # Progress update loop
    while True:
        await asyncio.sleep(10)
        if process.returncode is not None:
            break  # Exit loop if FFmpeg has finished

        # Get progress percentage
        elapsed_time = time.time() - start_time
        percentage = min(int((elapsed_time / 60) * 100), 100)
        eta = max(int((60 - elapsed_time)), 0)

        await msg.edit_text(f"⏳ Progress: {percentage}%\n⏱ ETA: {eta} sec")

    await process.wait()

    # Send the processed video
    await msg.edit_text("Uploading new video...")
    await bot.send_video(user_id, video=output_path, caption="Here is your video with subtitles!")

    # Cleanup
    os.remove(video_path)
    os.remove(sub_path)
    os.remove(output_path)

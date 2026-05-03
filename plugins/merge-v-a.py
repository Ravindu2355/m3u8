import os
import subprocess
from pyrogram import Client, filters
from Func.simples import get_tg_filename
from plugins.converter import progress_callback
from plugins.live_rec2 import upload_and_start_new_file

download_path = "./downloads"
user_data = {}


# Save video
@Client.on_message(filters.command("videoma") & filters.reply)
async def save_video(bot, message):
    user_id = message.from_user.id
    msg = await message.reply_text("⏳ Downloading video...")

    path1 = os.path.join(download_path, f"{user_id}_video.mp4")

    await message.reply_to_message.download(
        file_name=path1,
        progress=progress_callback,
        progress_args=(msg, "Downloading Video...", 0, {"time": 0, "msg": ""})
    )

    user_data[user_id] = {"video": path1}

    await msg.edit_text("✅ Video saved!\nNow reply audio with /audioma")


# Save audio + merge
@Client.on_message(filters.command("audioma") & filters.reply)
async def save_audio_and_merge(bot, message):
    user_id = message.from_user.id

    if user_id not in user_data or "video" not in user_data[user_id]:
        return await message.reply_text("❌ Send video first with /videoma")

    msg = await message.reply_text("⏳ Downloading audio...")

    path2 = os.path.join(download_path, f"{user_id}_audio.mp3")

    await message.reply_to_message.download(
        file_name=path2,
        progress=progress_callback,
        progress_args=(msg, "Downloading Audio...", 0, {"time": 0, "msg": ""})
    )

    video_path = user_data[user_id]["video"]
    output_path = os.path.join(download_path, f"{user_id}_merged.mp4")

    await msg.edit_text("⚡ Merging video + audio...")

    subprocess.run([
        "ffmpeg",
        "-i", video_path,
        "-i", path2,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path
    ])

    # Upload
    await msg.edit_text("⏳ Uploading merged video...")
    await upload_and_start_new_file(bot, msg, output_path, 0)

    # Cleanup
    try:
        os.remove(video_path)
        os.remove(path2)
        os.remove(output_path)
    except:
        pass

    user_data.pop(user_id, None)

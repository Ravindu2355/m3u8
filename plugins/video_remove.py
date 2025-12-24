import os, subprocess
from pyrogram import Client, filters
from plugins.live_rec2 import upload_and_start_new_file
from Func.simples import get_tg_filename
from plugins.ffmpeg_utils import progress_updater
from plugins.converter import progress_callback
import time

download_path = "./downloads"

def time_to_seconds(time_str):
    h, m, s = map(float, time_str.split(":"))
    return h*3600 + m*60 + s

@Client.on_message(filters.command("remove") & filters.reply)
async def remove_parts(bot, message):
    try:
        time_arg = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply_text("Usage: /remove 00:01:00-00:02:00|00:03:00-00:04:00")

    parts = time_arg.split("|")
    msg = await message.reply_text("⏳ Preparing video...")
    last_update = {"time": 0, "msg": ""}

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    tg_name = await get_tg_filename(message.reply_to_message)
    video_path = os.path.join(download_path, tg_name)
    output_path = os.path.join(download_path, f"{os.path.splitext(tg_name)[0]}_partrem.mp4")

    # Download with progress
    start_time = time.time()
    await message.reply_to_message.download(
        file_name=video_path,
        progress=progress_callback,
        progress_args=(msg, "Downloading...", start_time, last_update)
    )

    # Split and remove parts
    tmp_files = []
    prev_end = 0
    for idx, p in enumerate(parts):
        start_sec = time_to_seconds(p.split("-")[0])
        tmp_file = f"{video_path}_tmp_{idx}.mp4"
        tmp_files.append(tmp_file)
        subprocess.run(["ffmpeg", "-i", video_path, "-ss", str(prev_end), "-to", str(start_sec), "-c", "copy", tmp_file])
        prev_end = time_to_seconds(p.split("-")[1])

    # Last segment
    tmp_file = f"{video_path}_tmp_last.mp4"
    tmp_files.append(tmp_file)
    subprocess.run(["ffmpeg", "-i", video_path, "-ss", str(prev_end), "-c", "copy", tmp_file])

    # Concat
    concat_file = os.path.join(download_path, "concat_list.txt")
    with open(concat_file, "w") as f:
        for t in tmp_files:
            f.write(f"file '{t}'\n")
    subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", output_path])

    # Upload with progress
    await msg.edit_text("⏳ Uploading processed video...")
    start_time = time.time()
    await upload_and_start_new_file(bot, msg, output_path, start_time)

    # Cleanup
    os.remove(video_path)
    os.remove(concat_file)
    for t in tmp_files:
        os.remove(t)

  

import os, subprocess
from pyrogram import Client, filters
from plugins.live_rec2 import upload_and_start_new_file
from Func.simples import get_tg_filename
from plugins.converter import progress_callback

download_path = "./downloads"

def time_to_seconds(time_str):
    h, m, s = map(float, time_str.split(":"))
    return h*3600 + m*60 + s

@Client.on_message(filters.command("mutep") & filters.reply & filters.video)
async def mute_parts(bot, message):
    try:
        time_arg = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply_text("Usage: /mutep 00:01:00-00:02:00|00:03:00-00:04:00")

    parts = time_arg.split("|")
    msg = await message.reply_text("⏳ Muting video parts...")

    tg_name = await get_tg_filename(message)
    video_path = os.path.join(download_path, tg_name)
    output_path = os.path.join(download_path, f"{os.path.splitext(tg_name)[0]}_muted.mp4")

    # Download with progress
    await message.video.download(file_name=video_path, progress=progress_callback, progress_args=(msg,"Downloading...",0,{"time":0,"msg":""}))

    # Build ffmpeg filter
    filters = ",".join([f"volume=enable='between(t,{time_to_seconds(p.split('-')[0])},{time_to_seconds(p.split('-')[1])})':volume=0" for p in parts])
    subprocess.run([
        "ffmpeg", "-i", video_path, "-af", filters, "-c:v", "copy", output_path
    ])

    # Upload
    await msg.edit_text("⏳ Uploading processed video...")
    await upload_and_start_new_file(bot, msg, output_path, 0)
    os.remove(video_path)

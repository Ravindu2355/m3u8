import os, subprocess
from pyrogram import Client, filters
from plugins.live_rec2 import upload_and_start_new_file
from Func.simples import get_tg_filename
from plugins.converter import progress_callback

download_path = "./downloads"

@Client.on_message(filters.command("spd") & filters.reply)
async def speed_video(bot, message):
    try:
        speed = float(message.text.split(" ",1)[1])
    except:
        return await message.reply_text("Usage: /spd <speed factor, e.g., 1.2>")

    msg = await message.reply_text("⏳ Processing speed...")
    tg_name = await get_tg_filename(message.reply_to_message)
    video_path = os.path.join(download_path, tg_name)
    output_path = os.path.join(download_path, f"{os.path.splitext(tg_name)[0]}_spd.mp4")

    # Download with progress
    await message.reply_to_message.download(file_name=video_path, progress=progress_callback, progress_args=(msg,"Downloading...",0,{"time":0,"msg":""}))

    # Apply speed
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-filter:a", f"atempo={speed}",
        "-filter:v", f"setpts={1/speed}*PTS",
        "-c:v", "copy", output_path
    ])

    # Upload
    await msg.edit_text("⏳ Uploading processed video...")
    await upload_and_start_new_file(bot, msg, output_path, 0)
    os.remove(video_path)

import os
import subprocess
from pyrogram import Client, filters
from Func.simples import get_tg_filename
from plugins.converter import progress_callback
from plugins.live_rec2 import upload_and_start_new_file

download_path = "./downloads"
user_data = {}  # store per-user temp data


# Save first video
@Client.on_message(filters.command("v1") & filters.reply)
async def save_v1(bot, message):
    user_id = message.from_user.id
    msg = await message.reply_text("⏳ Downloading first video...")

    tg_name = await get_tg_filename(message.reply_to_message)
    if "./downloads/" in tg_name:
        tg_name = tg_name.replace("./downloads/", "")

    path1 = os.path.join(download_path, f"{user_id}_v1.mp4")

    await message.reply_to_message.download(
        file_name=path1,
        progress=progress_callback,
        progress_args=(msg, "Downloading V1...", 0, {"time": 0, "msg": ""})
    )

    user_data[user_id] = {"v1": path1}

    await msg.edit_text("✅ First video saved!\nNow reply second video with /v2")


# Save second video and merge
@Client.on_message(filters.command("v2") & filters.reply)
async def save_v2_and_merge(bot, message):
    user_id = message.from_user.id

    if user_id not in user_data or "v1" not in user_data[user_id]:
        return await message.reply_text("❌ Send first video with /v1")

    msg = await message.reply_text("⏳ Downloading second video...")

    tg_name = await get_tg_filename(message.reply_to_message)
    if "./downloads/" in tg_name:
        tg_name = tg_name.replace("./downloads/", "")

    path2 = os.path.join(download_path, f"{user_id}_v2.mp4")

    await message.reply_to_message.download(
        file_name=path2,
        progress=progress_callback,
        progress_args=(msg, "Downloading V2...", 0, {"time": 0, "msg": ""})
    )

    path1 = user_data[user_id]["v1"]

    # Create concat file
    concat_file = os.path.join(download_path, f"{user_id}_concat.txt")
    with open(concat_file, "w") as f:
        f.write(f"file '{os.path.abspath(path1)}'\n")
        f.write(f"file '{os.path.abspath(path2)}'\n")

    output_path = os.path.join(download_path, f"{user_id}_merged.mp4")

    await msg.edit_text("⚡ Merging videos (no re-encode)...")

    # Merge without re-encoding
    subprocess.run([
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        output_path
    ])

    # Upload
    await msg.edit_text("⏳ Uploading merged video...")
    await upload_and_start_new_file(bot, msg, output_path, 0)

    # Cleanup
    try:
        os.remove(path1)
        os.remove(path2)
        os.remove(concat_file)
        os.remove(output_path)
    except:
        pass

    user_data.pop(user_id, None)

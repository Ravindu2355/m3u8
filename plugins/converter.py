import os, asyncio
import time
import subprocess, json

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from Func.simples import mention_user, generate_thumbnail, get_tg_filename
from Func.m3u8 import download_and_convert_video


# ------------------------ SAFE DURATION EXTRACTOR ------------------------

def get_duration_safe(video_path):
    """Returns video duration in seconds or 0 if fails."""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", video_path
        ]
        output = subprocess.check_output(cmd).decode()
        data = json.loads(output)

        if "format" in data and "duration" in data["format"]:
            return float(data["format"]["duration"])

        for stream in data.get("streams", []):
            if "duration" in stream:
                return float(stream["duration"])

        return 0
    except:
        return 0


# ------------------------ SAFE EXTENSION HANDLING ------------------------

def has_valid_extension(filename: str) -> bool:
    parts = filename.rsplit('.', 1)
    return len(parts) == 2 and len(parts[1]) <= 5  # 1-5 char extensions


def changeFileExt(filename: str, new_extension: str) -> str:
    if not new_extension.startswith('.'):
        new_extension = '.' + new_extension
    name, _ = os.path.splitext(filename)
    return name + new_extension


# ------------------------ VIDEO DETECTION ------------------------

def is_video_file(filename: str) -> bool:
    video_extensions = {
        "mp4", "webm", "mkv", "mov", "avi", "flv", "wmv",
        "hevc", "av1", "prores", "mxf", "braw",
        "ogv", "3gp", "mts", "ts", "m4v", "css", "txt", "php"
    }
    #ext = os.path.splitext(filename.lower())[1].replace(".", "")
    ext = filename.lower().split('.')[-1]
    return ext in video_extensions


# ------------------------ PROGRESS HANDLER ------------------------

def human_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


async def progress_callback(current, total, message: Message, p_title, start_time, last_update):
    elapsed_time = time.time() - start_time
    speed = (current / elapsed_time) / 1024 if elapsed_time > 0 else 0
    progress = (current / total) * 100 if total > 0 else 0
    eta = (total - current) / (speed * 1024) if speed > 0 else 0

    progress_msg = (
        f"**{p_title}**\n"
        f"**Progress:** {progress:.2f}%\n"
        f"**Done:** {human_readable_size(current)} / {human_readable_size(total)}\n"
        f"**Speed:** {speed:.2f} KB/s\n"
        f"**ETA:** {int(eta)}s"
    )

    if time.time() - last_update["time"] > 10 and last_update["msg"] != progress_msg:
        try:
            await message.edit_text(progress_msg)
            last_update["time"] = time.time()
            last_update["msg"] = progress_msg
        except:
            pass


# ------------------------ HANDLE FILES ------------------------

@Client.on_message(filters.video | filters.document)
async def handle_forwarded_file(client, message: Message):

    # ============ SUBTITLE HANDLING ============
    if message.document:
        doc = message.document

        # detect subtitle
        ext = os.path.splitext(doc.file_name.lower())[1].replace(".", "")
        if ext in ["srt", "ass"]:
            if not message.reply_to_message or not message.reply_to_message.video:
                return await message.reply_text("Send a **video first**, then reply with subtitle.")

            await message.reply(
                "**Subtitle Merger**\n\nChoose method:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔥 Burn-in", callback_data="burn")],
                    [InlineKeyboardButton("📝 Move Text", callback_data="mov_text")],
                    [InlineKeyboardButton("📦 MKV Mux", callback_data="mkv_mux")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
                ])
            )
            return

    # ============ VIDEO CONVERSION ============
    await client.send_message(
        chat_id=message.chat.id,
        text="🎥 **What do you want to convert this video to?**",
        reply_to_message_id=message.id,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎥 MP4", callback_data="convertTo_mp4")],
            [InlineKeyboardButton("🎥 MKV", callback_data="convertTo_mkv")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
        ])
    )


# ------------------------ DOWNLOAD + CONVERT ------------------------

@Client.on_callback_query(filters.regex(r"^convertTo_"))
async def handle_button_click_convert(client, query: CallbackQuery):
    action = query.data
    q_msg = query.message
    original_msg = q_msg.reply_to_message

    if action == "cancel":
        return await q_msg.edit_text("❌ Cancelled.")

    convert_to = action.split("_")[1]

    await q_msg.edit_text("📥 **Downloading...**")

    download_path = "./downloads"
    os.makedirs(download_path, exist_ok=True)

    tg_filename = await get_tg_filename(original_msg)
    file_path = os.path.join(download_path, tg_filename)

    last_update = {"time": 0, "msg": ""}
    start_time = time.time()

    # ------ Download from Telegram ------
    downloaded_file_path = await original_msg.download(
        file_name=file_path,
        progress=progress_callback,
        progress_args=(q_msg, "Downloading...", start_time, last_update)
    )

    await q_msg.edit_text("🔄 **Converting file...**")

    # determine output file
    if has_valid_extension(tg_filename):
        output_file = changeFileExt(downloaded_file_path, convert_to)
    else:
        output_file = f"{downloaded_file_path}.{convert_to}"

    # ------ Convert ------
    duration = await download_and_convert_video(q_msg, downloaded_file_path, output_file)

    # If converter didn't return duration → get manually
    if not duration:
        duration = get_duration_safe(output_file)

    if not os.path.exists(output_file):
        return await q_msg.edit_text("❌ Conversion failed. No output file.")

    # ------ Thumbnail ------
    thumb_file = "thumb.jpg"
    generate_thumbnail(output_file, thumb_file)

    if not os.path.exists(thumb_file):
        return await q_msg.edit_text("❌ Failed to generate thumbnail.")

    # ------ Upload with SAFE duration ------
    await q_msg.edit_text("📤 **Uploading...**")
    upload_start_time = time.time()

    with open(output_file, "rb") as video, open(thumb_file, "rb") as thumb:
        await client.send_video(
            chat_id=original_msg.chat.id,
            video=video,
            duration=int(duration),     # <--- SAFE NOW
            thumb=thumb,
            caption=f"✅ **Converted Successfully!**\n\n`{output_file}`",
            supports_streaming=True,
            progress=progress_callback,
            progress_args=(q_msg, "Uploading...", upload_start_time, last_update)
        )

    await q_msg.delete()

    # Clean files
    for f in [output_file, thumb_file, downloaded_file_path]:
        if os.path.exists(f):
            os.remove(f)

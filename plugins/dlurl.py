import os
import math
import asyncio
import subprocess
import requests
from pyrogram import Client, filters
from plugins.converter import progress_callback
from plugins.live_rec2 import upload_and_start_new_file

download_path = "./downloads"
os.makedirs(download_path, exist_ok=True)

# 1.9 GB in bytes limit for Telegram
MAX_SIZE_BYTES = int(1.9 * 1024 * 1024 * 1024)


def get_video_duration(file_path):
    """Gets total video duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokeyvalue=1",
            file_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 0.0


def download_with_requests(url, output_path):
    """Downloads video stream directly using requests in 1 MB chunks."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    with requests.get(url, headers=headers, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    return True


def split_large_video(file_path, max_bytes=MAX_SIZE_BYTES):
    """Splits large video losslessly into ~1.9 GB playable parts using FFmpeg."""
    file_size = os.path.getsize(file_path)
    if file_size <= max_bytes:
        return [file_path]

    duration = get_video_duration(file_path)
    if duration <= 0:
        return [file_path]

    num_parts = math.ceil(file_size / max_bytes)
    part_duration = duration / num_parts
    
    split_files = []
    base_dir, file_name = os.path.split(file_path)
    name_no_ext, ext = os.path.splitext(file_name)

    for i in range(num_parts):
        start_sec = i * part_duration
        part_out = os.path.abspath(os.path.join(base_dir, f"{name_no_ext}_part_{i+1}{ext}"))

        # Lossless fast split
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", str(start_sec),
            "-i", file_path,
            "-t", str(part_duration),
            "-c", "copy",
            "-avoid_negative_ts", "1",
            part_out
        ], check=True)

        split_files.append(part_out)

    return split_files


# ---------------------------
# DIRECT VIDEO URL DOWNLOAD & AUTO-SPLIT
# ---------------------------

@Client.on_message(filters.command(["trimurl", "dlurl"]))
async def download_video_requests_cmd(bot, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ **Usage:** `/trimurl <VIDEO_URL>`")

    url = message.command[1]
    user_id = message.from_user.id
    msg = await message.reply_text("⏳ Downloading video via direct connection...")

    input_path = os.path.abspath(os.path.join(download_path, f"{user_id}_download.mp4"))
    final_parts = []

    try:
        # Step 1: Download using requests off-thread to avoid blocking async loop
        await asyncio.to_thread(download_with_requests, url, input_path)

        if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
            return await msg.edit_text("❌ Download failed or file is empty. Check the URL.")

        # Step 2: Check file size and split if over 1.9 GB
        file_size_gb = os.path.getsize(input_path) / (1024 ** 3)
        if file_size_gb > 1.9:
            await msg.edit_text(f"📦 Video is **{file_size_gb:.2f} GB**. Splitting into ~1.9 GB parts...")
            final_parts = split_large_video(input_path)
        else:
            final_parts = [input_path]

        # Step 3: Upload all parts
        total_parts = len(final_parts)
        for idx, part_path in enumerate(final_parts):
            if total_parts > 1:
                await msg.edit_text(f"⏳ Uploading part {idx + 1}/{total_parts}...")
            else:
                await msg.edit_text("⏳ Uploading video...")

            await upload_and_start_new_file(bot, msg, part_path, 0)

    except Exception as e:
        await msg.edit_text(f"❌ Error during processing: `{str(e)}`")

    finally:
        # Cleanup temporary files
        cleanup_files = set([input_path] + final_parts)
        for file_path in cleanup_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

        try:
            await msg.delete()
        except Exception:
            pass

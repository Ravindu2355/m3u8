import os
import math
import asyncio
import subprocess
import aiohttp
from pyrogram import Client, filters
from plugins.converter import progress_callback
from plugins.live_rec2 import upload_and_start_new_file

download_path = "./downloads"
os.makedirs(download_path, exist_ok=True)

MAX_SIZE_BYTES = int(1.9 * 1024 * 1024 * 1024)  # ~1.9 GB target limit


def parse_ranges(ranges):
    result = []
    for r in ranges:
        try:
            start, end = r.split("-")
            result.append((start.strip(), end.strip()))
        except Exception:
            return None
    return result


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


async def download_from_url(url, output_path):
    """Downloads video via yt-dlp with fallback to direct aiohttp HTTP stream."""
    # 1. Try yt-dlp first (Supports YouTube, Direct MP4, Twitter/X, Drive, etc.)
    try:
        process = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-f", "b/bestvideo+bestaudio/best",
            "--no-playlist",
            "-o", output_path,
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
    except Exception:
        pass

    # 2. Fallback to direct HTTP download using aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True) as resp:
                if resp.status == 200:
                    with open(output_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(1024 * 1024):
                            f.write(chunk)
                    return True
    except Exception:
        pass

    return False


def split_large_file(file_path, max_bytes=MAX_SIZE_BYTES):
    """Splits output into ~1.9 GB clips if file size exceeds threshold."""
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
# URL TRIM MODE (WITH 1.9GB AUTO SPLIT)
# ---------------------------

@Client.on_message(filters.command("trimurl"))
async def trim_url_cmd(bot, message):
    user_id = message.from_user.id

    if len(message.command) < 3:
        return await message.reply_text(
            "❌ **Usage:**\n`/trimurl <URL> 00:00:00-00:00:10 00:00:25-00:00:40`"
        )

    url = message.command[1]
    ranges = parse_ranges(message.command[2:])
    if not ranges:
        return await message.reply_text("❌ Invalid timestamp format. Use `00:00:00-00:00:10`")

    msg = await message.reply_text("⏳ Downloading video from URL...")

    input_path = os.path.abspath(os.path.join(download_path, f"{user_id}_url_input.mp4"))
    concat_file = os.path.abspath(os.path.join(download_path, f"{user_id}_url_concat.txt"))
    output_path = os.path.abspath(os.path.join(download_path, f"{user_id}_url_final.mp4"))
    clips = []
    final_parts = []

    try:
        # Download step
        success = await download_from_url(url, input_path)
        if not success or not os.path.exists(input_path):
            return await msg.edit_text("❌ Failed to download video from the given URL.")

        await msg.edit_text("✂️ Trimming clips...")

        for i, (start, end) in enumerate(ranges):
            out_clip = os.path.abspath(os.path.join(download_path, f"{user_id}_url_clip_{i}.ts"))

            subprocess.run([
                "ffmpeg", "-y",
                "-ss", start,
                "-to", end,
                "-i", input_path,
                "-c", "copy",
                "-avoid_negative_ts", "1",
                "-f", "mpegts",
                out_clip
            ], check=True)

            clips.append(out_clip)

        # Concatenate trimmed segments
        with open(concat_file, "w") as f:
            for clip in clips:
                f.write(f"file '{clip}'\n")

        await msg.edit_text("🔗 Merging clips...")

        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-fflags", "+genpts",
            "-i", concat_file,
            "-c", "copy",
            "-bsf:a", "aac_adtstoasc",
            output_path
        ], check=True)

        # Split check for files > 1.9 GB
        await msg.edit_text("📦 Checking file size and preparing upload...")
        final_parts = split_large_file(output_path)

        # Upload all parts
        for idx, part in enumerate(final_parts):
            await msg.edit_text(f"⏳ Uploading part {idx + 1}/{len(final_parts)}...")
            await upload_and_start_new_file(bot, msg, part, 0)

    except Exception as e:
        await msg.edit_text(f"❌ Error during processing: `{str(e)}`")

    finally:
        # Clean up temporary files safely
        cleanup_list = [input_path, concat_file, output_path] + clips + final_parts
        for f in set(cleanup_list):
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass

        try:
            await msg.delete()
        except Exception:
            pass

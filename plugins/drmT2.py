import os
import time
import asyncio
import re
from html import escape

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from plugins.live_rec2 import upload_and_start_new_file


DOWNLOAD_PATH = "./downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

active_jobs = set()


def format_time(seconds):
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"


async def safe_edit(msg, text, state):
    if text == state.get("last_text"):
        return

    try:
        await msg.edit_text(text, parse_mode=ParseMode.HTML)
        state["last_text"] = text

    except Exception as e:
        if "MESSAGE_NOT_MODIFIED" not in str(e):
            print("Telegram edit error:", e)


async def run_command(cmd, msg, title, progress_type="normal"):
    start_time = time.monotonic()

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    state = {
        "last_text": None,
        "last_update": 0,
        "latest": "Starting...",
        "progress": "Starting...",
        "speed": "-",
        "eta": "-",
        "size": "-"
    }

    async def update_status(force=False):
        now = time.monotonic()
        elapsed = now - start_time

        if not force and now - state["last_update"] < 5:
            return

        state["last_update"] = now

        text = (
            f"⚙️ <b>{escape(title)}</b>\n\n"
            f"📊 Progress: <b>{escape(str(state['progress']))}</b>\n"
            f"🚀 Speed: <code>{escape(str(state['speed']))}</code>\n"
            f"⏳ ETA: <code>{escape(str(state['eta']))}</code>\n"
            f"📦 Size: <code>{escape(str(state['size']))}</code>\n"
            f"⏱️ Time: <code>{format_time(elapsed)}</code>\n\n"
            f"📝 <code>{escape(state['latest'][:500])}</code>"
        )

        await safe_edit(msg, text, state)

    while True:
        line = await process.stdout.readline()

        if not line:
            break

        line = line.decode(errors="ignore").strip()

        if not line:
            continue

        state["latest"] = line

        if progress_type == "ytdlp":
            parts = line.split("|")

            if len(parts) >= 4:
                state["progress"] = parts[0]
                state["speed"] = parts[1]
                state["eta"] = parts[2]
                state["size"] = parts[3]

        elif progress_type == "ffmpeg":
            if line.startswith("out_time="):
                state["progress"] = "Time: " + line.replace("out_time=", "")

            elif line.startswith("speed="):
                state["speed"] = line.replace("speed=", "")

            elif line.startswith("total_size="):
                state["size"] = line.replace("total_size=", "")

            elif line == "progress=end":
                state["progress"] = "Complete"

        else:
            percentage = re.search(r"(\d+(?:\.\d+)?)%", line)

            if percentage:
                state["progress"] = percentage.group(1) + "%"

        await update_status()

    code = await process.wait()
    elapsed = time.monotonic() - start_time

    if code == 0:
        state["progress"] = "Complete"

        final_text = (
            f"✅ <b>{escape(title)}</b>\n\n"
            f"🎉 <b>Completed successfully</b>\n\n"
            f"⏱️ Time: <code>{format_time(elapsed)}</code>\n\n"
            f"📝 <code>{escape(state['latest'][:500])}</code>"
        )

    else:
        final_text = (
            f"❌ <b>{escape(title)}</b>\n\n"
            f"Process exited with code: <code>{code}</code>\n\n"
            f"📝 <code>{escape(state['latest'][:1000])}</code>"
        )

    await safe_edit(msg, final_text, state)

    return code


@Client.on_message(filters.command("drm2") & filters.private)
async def drm_download(bot, message):
    user_id = message.from_user.id

    if user_id in active_jobs:
        return await message.reply_text("⚠️ You already have an active job.")

    if len(message.command) < 4:
        return await message.reply_text(
            "❌ Invalid usage.\n\n"
            "Usage:\n"
            "/dr MPD_URL REFERER KID:KEY [filename]"
        )

    mpd_url = message.command[1]
    referer = message.command[2]
    key = message.command[3]

    filename = (
        message.command[4]
        if len(message.command) >= 5
        else f"{user_id}_final.mp4"
    )

    filename = os.path.basename(filename)

    if not filename.lower().endswith(".mp4"):
        filename += ".mp4"

    try:
        kid, clear_key = key.split(":", 1)
        kid = kid.strip()
        clear_key = clear_key.strip()

    except ValueError:
        return await message.reply_text(
            "❌ Invalid key format.\n\n"
            "Expected:\n"
            "KID:KEY"
        )

    active_jobs.add(user_id)

    msg = await message.reply_text(
        "🚀 <b>Starting...</b>",
        parse_mode=ParseMode.HTML
    )

    folder = os.path.join(DOWNLOAD_PATH, str(user_id))
    os.makedirs(folder, exist_ok=True)

    encrypted_video = os.path.join(folder, "encrypted_video.mp4")
    encrypted_audio = os.path.join(folder, "encrypted_audio.mp4")
    decrypted_video = os.path.join(folder, "decrypted_video.mp4")
    decrypted_audio = os.path.join(folder, "decrypted_audio.mp4")
    final_path = os.path.join(folder, filename)

    try:
        user_agent = (
            "Mozilla/5.0 (Linux; Android 11; Mobile) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/107.0.0.0 Mobile Safari/537.36"
        )

        common_headers = [
            "--referer", referer,
            "--user-agent", user_agent,
            "--add-header", "Accept: */*",
            "--add-header", "Accept-Language: en-GB,en-US;q=0.9,en;q=0.8",
            "--add-header", 'Sec-CH-UA: "Chromium";v="107", "Not=A?Brand";v="24"',
            "--add-header", "Sec-CH-UA-Mobile: ?1",
            "--add-header", 'Sec-CH-UA-Platform: "Android"',
            "--add-header", "Sec-Fetch-Dest: empty",
            "--add-header", "Sec-Fetch-Mode: cors",
            "--add-header", "Sec-Fetch-Site: cross-site"
        ]

        video_cmd = [
            "yt-dlp",
            "--allow-unplayable",
            *common_headers,
            "-f", "bestvideo",
            "--newline",
            "--progress",
            "--progress-template",
            "download:%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s|%(progress._total_bytes_str)s",
            "-o", encrypted_video,
            mpd_url
        ]

        code = await run_command(
            video_cmd,
            msg,
            "Downloading encrypted video",
            "ytdlp"
        )

        if code != 0:
            raise Exception("Video download failed")

        audio_cmd = [
            "yt-dlp",
            "--allow-unplayable",
            *common_headers,
            "-f", "bestaudio",
            "--newline",
            "--progress",
            "--progress-template",
            "download:%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s|%(progress._total_bytes_str)s",
            "-o", encrypted_audio,
            mpd_url
        ]

        code = await run_command(
            audio_cmd,
            msg,
            "Downloading encrypted audio",
            "ytdlp"
        )

        if code != 0:
            raise Exception("Audio download failed")

        video_decrypt_cmd = [
            "packager",
            f"in={encrypted_video},stream=video,output={decrypted_video}",
            "--enable_raw_key_decryption",
            "--keys",
            f"label=:key_id={kid}:key={clear_key}"
        ]

        code = await run_command(
            video_decrypt_cmd,
            msg,
            "Decrypting video",
            "normal"
        )

        if code != 0:
            raise Exception("Video decryption failed")

        audio_decrypt_cmd = [
            "packager",
            f"in={encrypted_audio},stream=audio,output={decrypted_audio}",
            "--enable_raw_key_decryption",
            "--keys",
            f"label=:key_id={kid}:key={clear_key}"
        ]

        code = await run_command(
            audio_decrypt_cmd,
            msg,
            "Decrypting audio",
            "normal"
        )

        if code != 0:
            raise Exception("Audio decryption failed")

        merge_cmd = [
            "ffmpeg",
            "-y",
            "-i", decrypted_video,
            "-i", decrypted_audio,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c", "copy",
            "-shortest",
            "-progress", "pipe:1",
            "-nostats",
            final_path
        ]

        code = await run_command(
            merge_cmd,
            msg,
            "Merging video and audio",
            "ffmpeg"
        )

        if code != 0:
            raise Exception("FFmpeg merge failed")

        await msg.edit_text(
            "📤 <b>Uploading final file...</b>",
            parse_mode=ParseMode.HTML
        )

        await upload_and_start_new_file(
            bot,
            msg,
            final_path,
            0
        )

    except Exception as e:
        print("DRM JOB ERROR:", repr(e))

        try:
            await msg.edit_text(
                f"❌ <b>Failed</b>\n\n"
                f"<code>{escape(str(e)[:1000])}</code>",
                parse_mode=ParseMode.HTML
            )

        except Exception:
            pass

    finally:
        active_jobs.discard(user_id)

        for path in [
            encrypted_video,
            encrypted_audio,
            decrypted_video,
            decrypted_audio,
            final_path
        ]:
            try:
                if os.path.exists(path):
                    os.remove(path)

            except Exception as e:
                print("Cleanup error:", e)

import os
import asyncio
from pyrogram import Client, filters

from plugins.live_rec2 import upload_and_start_new_file

DOWNLOAD_PATH = "./downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

active_jobs = set()


async def run_command(cmd, msg, title):

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    last_update = 0

    while True:

        line = await process.stdout.readline()

        if not line:
            break

        line = line.decode(errors="ignore").strip()

        if not line:
            continue

        now = asyncio.get_event_loop().time()

        if now - last_update >= 2:

            try:
                await msg.edit_text(
                    f"⚙️ **{title}**\n\n"
                    f"`{line[:500]}`"
                )

                last_update = now

            except Exception:
                pass

    return await process.wait()


@Client.on_message(filters.command("dr") & filters.private)
async def drm_download(bot, message):

    user_id = message.from_user.id

    if user_id in active_jobs:
        return await message.reply_text(
            "⚠️ You already have an active job."
        )

    if len(message.command) < 4:
        return await message.reply_text(
            "Usage:\n"
            "/dr <authorized_mpd_url> <referer> <kid:key> [filename]"
        )

    mpd_url = message.command[1]
    referer = message.command[2]
    key = message.command[3]

    # Fixed: filename is command index 4
    filename = (
        message.command[4]
        if len(message.command) >= 5
        else f"{user_id}_final.mp4"
    )

    active_jobs.add(user_id)

    msg = await message.reply_text(
        "🚀 Starting..."
    )

    folder = os.path.join(
        DOWNLOAD_PATH,
        str(user_id)
    )

    os.makedirs(folder, exist_ok=True)

    encrypted_video = os.path.join(
        folder,
        "encrypted_video.mp4"
    )

    encrypted_audio = os.path.join(
        folder,
        "encrypted_audio.mp4"
    )

    decrypted_video = os.path.join(
        folder,
        "decrypted_video.mp4"
    )

    decrypted_audio = os.path.join(
        folder,
        "decrypted_audio.mp4"
    )

    final_path = os.path.join(
        folder,
        filename
    )

    try:

        # ─────────────────────────
        # COMMON HEADERS
        # ─────────────────────────

        user_agent = (
            "Mozilla/5.0 (Linux; Android 11; Mobile) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/107.0.0.0 Mobile Safari/537.36"
        )

        common_headers = [
            "--referer",
            referer,

            "--user-agent",
            user_agent,

            "--add-header",
            "Accept: */*",

            "--add-header",
            "Accept-Language: en-GB,en-US;q=0.9,en;q=0.8",

            "--add-header",
            'Sec-CH-UA: "Chromium";v="107", "Not=A?Brand";v="24"',

            "--add-header",
            "Sec-CH-UA-Mobile: ?1",

            "--add-header",
            'Sec-CH-UA-Platform: "Android"',

            "--add-header",
            "Sec-Fetch-Dest: empty",

            "--add-header",
            "Sec-Fetch-Mode: cors",

            "--add-header",
            "Sec-Fetch-Site: cross-site"
        ]

        # ─────────────────────────
        # DOWNLOAD VIDEO
        # ─────────────────────────

        video_cmd = [
            "yt-dlp",

            "--allow-unplayable",

            *common_headers,

            "-f",
            "bestvideo",

            "-o",
            encrypted_video,

            mpd_url
        ]

        code = await run_command(
            video_cmd,
            msg,
            "Downloading encrypted video"
        )

        if code != 0:
            raise Exception(
                "Video download failed"
            )

        # ─────────────────────────
        # DOWNLOAD AUDIO
        # ─────────────────────────

        audio_cmd = [
            "yt-dlp",

            "--allow-unplayable",

            *common_headers,

            "-f",
            "bestaudio",

            "-o",
            encrypted_audio,

            mpd_url
        ]

        code = await run_command(
            audio_cmd,
            msg,
            "Downloading encrypted audio"
        )

        if code != 0:
            raise Exception(
                "Audio download failed"
            )

        try:
           kid, clear_key = key.split(":", 1)
        except ValueError:
           raise Exception ("Invalid key format. Expected KID:KEY")

        # ─────────────────────────
        # DECRYPT VIDEO WITH SHAKA PACKAGER
        # ─────────────────────────

        video_decrypt_cmd = [
            "packager",

            f"in={encrypted_video},"
            f"stream=video,"
            f"output={decrypted_video}",

            "--enable_raw_key_decryption",

            "--keys",
            f"label=:key_id={kid}:"
            f"key={clear_key}"
        ]

        code = await run_command(
            video_decrypt_cmd,
            msg,
            "Decrypting video"
        )

        if code != 0:
            raise Exception(
                "Video decryption failed"
            )

        # ─────────────────────────
        # DECRYPT AUDIO WITH SHAKA PACKAGER
        # ─────────────────────────

        audio_decrypt_cmd = [
            "packager",

            f"in={encrypted_audio},"
            f"stream=audio,"
            f"output={decrypted_audio}",

            "--enable_raw_key_decryption",

            "--keys",
            f"label=:key_id={kid}:"
            f"key={clear_key}"
        ]

        code = await run_command(
            audio_decrypt_cmd,
            msg,
            "Decrypting audio"
        )

        if code != 0:
            raise Exception(
                "Audio decryption failed"
            )

        # ─────────────────────────
        # MERGE VIDEO + AUDIO
        # ─────────────────────────

        await msg.edit_text(
            "🎬 **Merging video + audio...**"
        )

        merge_cmd = [
            "ffmpeg",

            "-y",

            "-i",
            decrypted_video,

            "-i",
            decrypted_audio,

            "-map",
            "0:v:0",

            "-map",
            "1:a:0",

            "-c",
            "copy",

            "-shortest",

            final_path
        ]

        code = await run_command(
            merge_cmd,
            msg,
            "Merging"
        )

        if code != 0:
            raise Exception(
                "FFmpeg merge failed"
            )

        # ─────────────────────────
        # UPLOAD
        # ─────────────────────────

        await msg.edit_text(
            "📤 **Uploading final file...**"
        )

        await upload_and_start_new_file(
            bot,
            msg,
            final_path,
            0
        )

    except Exception as e:

        try:
            await msg.edit_text(
                f"❌ **Failed**\n\n"
                f"`{str(e)[:1000]}`"
            )
        except:
            pass

    finally:

        active_jobs.discard(user_id)

        # Cleanup
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

            except:
                pass

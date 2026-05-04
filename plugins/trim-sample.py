import os
import subprocess
from pyrogram import Client, filters
from plugins.converter import progress_callback
from plugins.live_rec2 import upload_and_start_new_file

download_path = "./downloads"
os.makedirs(download_path, exist_ok=True)


def parse_ranges(ranges):
    result = []
    for r in ranges:
        try:
            start, end = r.split("-")
            result.append((start.strip(), end.strip()))
        except:
            return None
    return result


# ---------------------------
# FAST MODE (NO RE-ENCODE)
# ---------------------------
@Client.on_message(filters.command("trim") & filters.reply)
async def trim_fast(bot, message):
    user_id = message.from_user.id

    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Usage:\n/trim 00:00:00-00:00:10 00:00:25-00:00:40"
        )

    ranges = parse_ranges(message.command[1:])
    if not ranges:
        return await message.reply_text("❌ Invalid format")

    msg = await message.reply_text("⏳ Downloading video...")

    input_path = os.path.join(download_path, f"{user_id}_input.mp4")

    await message.reply_to_message.download(
        file_name=input_path,
        progress=progress_callback,
        progress_args=(msg, "Downloading...", 0, {"time": 0, "msg": ""})
    )

    clips = []
    await msg.edit_text("✂️ Trimming (fast mode)...")

    for i, (start, end) in enumerate(ranges):
        out_clip = os.path.join(download_path, f"{user_id}_clip_{i}.ts")

        subprocess.run([
            "ffmpeg",
            "-y",
            "-ss", start,
            "-to", end,
            "-i", input_path,
            "-c", "copy",
            "-avoid_negative_ts", "1",
            "-f", "mpegts",
            out_clip
        ])

        clips.append(out_clip)

    concat_file = os.path.join(download_path, f"{user_id}_concat.txt")
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip}'\n")

    output_path = os.path.join(download_path, f"{user_id}_final.mp4")

    await msg.edit_text("🔗 Merging clips...")

    subprocess.run([
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        output_path
    ])

    await msg.edit_text("⏳ Uploading...")
    await upload_and_start_new_file(bot, msg, output_path, 0)

    # Cleanup
    try:
        os.remove(input_path)
        os.remove(concat_file)
        os.remove(output_path)
        for c in clips:
            os.remove(c)
    except:
        pass

    await msg.delete()


# ---------------------------
# HQ MODE (RE-ENCODE)
# ---------------------------
@Client.on_message(filters.command("trimhq") & filters.reply)
async def trim_hq(bot, message):
    user_id = message.from_user.id

    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Usage:\n/trimhq 00:00:00-00:00:10 00:00:25-00:00:40"
        )

    ranges = parse_ranges(message.command[1:])
    if not ranges:
        return await message.reply_text("❌ Invalid format")

    msg = await message.reply_text("⏳ Downloading video...")

    input_path = os.path.join(download_path, f"{user_id}_input.mp4")

    await message.reply_to_message.download(
        file_name=input_path,
        progress=progress_callback,
        progress_args=(msg, "Downloading...", 0, {"time": 0, "msg": ""})
    )

    clips = []
    await msg.edit_text("🎬 Trimming (HQ mode)...")

    for i, (start, end) in enumerate(ranges):
        out_clip = os.path.join(download_path, f"{user_id}_clip_{i}.mp4")

        subprocess.run([
            "ffmpeg",
            "-y",
            "-ss", start,
            "-to", end,
            "-i", input_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "ultrafast",
            out_clip
        ])

        clips.append(out_clip)

    concat_file = os.path.join(download_path, f"{user_id}_concat.txt")
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip}'\n")

    output_path = os.path.join(download_path, f"{user_id}_final.mp4")

    await msg.edit_text("🔗 Merging HQ clips...")

    subprocess.run([
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        output_path
    ])

    await msg.edit_text("⏳ Uploading...")
    await upload_and_start_new_file(bot, msg, output_path, 0)

    # Cleanup
    try:
        os.remove(input_path)
        os.remove(concat_file)
        os.remove(output_path)
        for c in clips:
            os.remove(c)
    except:
        pass

    await msg.delete()

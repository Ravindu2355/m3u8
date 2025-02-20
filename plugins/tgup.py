import os
import time
import asyncio
import ffmpeg
from pyrogram.types import InputMediaVideo, InputMediaAudio
from pyrogram.errors import FloodWait
from humanize import naturalsize
from log import logger as lg

# Function to get media duration and generate a thumbnail if needed
def get_media_info(file_path, thumb_path=None):
    try:
        probe = ffmpeg.probe(file_path)
        duration = int(float(probe["format"]["duration"])) if "duration" in probe["format"] else 0
        if not thumb_path:
            thumb_path = f"{file_path}.jpg"
            (
                ffmpeg.input(file_path, ss=1)
                .output(thumb_path, vframes=1)
                .run(capture_stdout=True, capture_stderr=True)
            )
        return duration, thumb_path
    except Exception as e:
        lg.info(f"FFmpeg Error: {e}")
        return 0, None

# Function to upload file with progress updates
async def upload_file(client, chat_id, file_path, msg, as_document=False, thumb=None):
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    # Determine media type
    mime_type = file_path.split(".")[-1].lower()
    is_video = mime_type in ["mp4", "mkv", "mov"]
    is_audio = mime_type in ["mp3", "aac", "wav", "ogg"]
    is_image = mime_type in ["jpg", "jpeg", "png", "gif", "webp"]

    # Get media duration & generate thumbnail if necessary
    duration = 0
    if (is_video or is_audio) and not as_document:
        duration, thumb = get_media_info(file_path, thumb)

    # Upload with progress
    async def progress_func(current, total):
        nonlocal last_msg, last_t
        percent = (current / total) * 100
        speed = current / (time.time() - start_time) if current else 0
        eta = (total - current) / speed if speed > 0 else 0
        msg_text = f"**Uploading...**\n\n📂 Name: `{file_name}`\n📏 Size: {naturalsize(file_size)}\n📤 Uploaded: {naturalsize(current)}/{naturalsize(total)} ({percent:.2f}%)\n⚡ Speed: {naturalsize(speed)}/s\n⏳ ETA: {int(eta)}s"
        
        if last_t == 0 or time.time() - last_t >= 10:
            if msg_text != last_msg:
                try:
                    await msg.edit_text(msg_text)
                    last_msg = msg_text
                    last_t = time.time()
                except FloodWait as e:
                    await asyncio.sleep(e.value)

    last_msg, last_t = "", 0
    start_time = time.time()

    try:
        # Send file
        if as_document:
            media = await client.send_document(
                chat_id, file_path, caption=file_name, progress=progress_func
            )
        elif is_video:
            media = await client.send_video(
                chat_id, file_path, thumb=thumb, duration=duration, caption=file_name, progress=progress_func
            )
        elif is_audio:
            media = await client.send_audio(
                chat_id, file_path, duration=duration, caption=file_name, progress=progress_func
            )
        elif is_image:
            media = await client.send_photo(chat_id, file_path, caption=file_name, progress=progress_func)
        else:
            media = await client.send_document(
                chat_id, file_path, caption=file_name, progress=progress_func
            )

        # Final message update
        await msg.edit_text(f"✅ **Upload Complete!**\n📂 `{file_name}`\n📏 Size: {naturalsize(file_size)}")

        return media
    except Exception as e:
        await msg.edit_text(f"Err on sending file : {e}")
        return
        
    finally:
        # Delete file and thumbnail after upload
        try:
            os.remove(file_path)
            if thumb and os.path.exists(thumb):
                os.remove(thumb)
        except Exception as e:
            print(f"File Deletion Error: {e}")
            lg.info(f"File Deletion Error: {e}")
            return
      

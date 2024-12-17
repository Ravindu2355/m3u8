import os
import time
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from globals import AuthU

def mention_user(message:Message):
    user = message.from_user
    user_name = user.first_name
    user_id = user.id
    mention = f"[{user_name}](tg://user?id={user_id})"
    return mention

# Progress callback for uploads
def progress_callback(current, total, message: Message, start_time):
    elapsed_time = time.time() - start_time
    progress = (current / total) * 100
    speed = current / elapsed_time / 1024
    eta = (total - current) / (speed * 1024) if speed > 0 else 0

    progress_msg = (
        f"**Progress**: {progress:.2f}%\n"
        f"**Speed**: {speed:.2f} KB/s\n"
        f"**Elapsed Time**: {int(elapsed_time)}s\n"
        f"**ETA**: {int(eta)}s"
    )
    try:
        message.edit_text(progress_msg)
    except:
        pass

# Generate thumbnail using ffmpeg
def generate_thumbnail(video_path, thumb_path, time_stamp="00:00:05"):
    command = [
        "ffmpeg", "-i", video_path, "-ss", time_stamp, "-vframes", "1", thumb_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

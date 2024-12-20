import os, re
import time
import requests
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from globals import AuthU
import urllib.parse

def url_decode(encoded_string):
    return urllib.parse.unquote(encoded_string)

def url_encode(string):
    return urllib.parse.quote(string)

def mention_user(message:Message):
    user = message.from_user
    user_name = user.first_name
    user_id = user.id
    mention = f"[{user_name}](tg://user?id={user_id})"
    return mention

async def get_tg_filename(message:Message):
    if message.video:
        file_name = message.video.file_name
    elif message.document:
        file_name = message.document.file_name

    if not file_name:
        file_name = f"video_{time.time()}.mp4"
    # Reply with the file name
    return file_name

# Generate thumbnail using ffmpeg
def generate_thumbnail(video_path, thumb_path, time_stamp="00:00:05"):
    command = [
        "ffmpeg", "-i", video_path, "-ss", time_stamp, "-vframes", "1", thumb_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)



# Global variables to store the last progress message and update time
last_msg = ""
last_update_time = 0  # To track the last update time

# Function to convert bytes into human-readable format (KB, MB, GB)
def human_readable_size(size_in_bytes):
    if size_in_bytes < 1024:
        return f"{size_in_bytes:.2f} Bytes"
    elif size_in_bytes < 1024 ** 2:
        return f"{size_in_bytes / 1024:.2f} KB"
    elif size_in_bytes < 1024 ** 3:
        return f"{size_in_bytes / (1024 ** 2):.2f} MB"
    elif size_in_bytes < 1024 ** 4:
        return f"{size_in_bytes / (1024 ** 3):.2f} GB"
    else:
        return f"{size_in_bytes / (1024 ** 4):.2f} TB"

# Progress callback for uploads
async def progress_callback(current, total, message: Message, start_time):
    global last_msg, last_update_time

    elapsed_time = time.time() - start_time  # Time elapsed since upload started
    progress = (current / total) * 100  # Calculate progress percentage
    speed = current / elapsed_time / 1024  # Calculate speed in KB/s
    eta = (total - current) / (speed * 1024) if speed > 0 else 0  # Estimated Time of Arrival (ETA)

    # Convert current, total, and speed to human-readable formats
    current_human = human_readable_size(current)
    total_human = human_readable_size(total)
    speed_human = human_readable_size(current / elapsed_time)  # Speed in KB/s converted to human format
    eta_human = human_readable_size(eta * 1024)  # ETA in bytes converted to human format

    # Build the progress message
    progress_msg = (
        f"**Progress**: {progress:.2f}%\n"
        f"**Uploaded**: {current_human} / {total_human}\n"
        f"**Speed**: {speed_human}/s\n"
        f"**Elapsed Time**: {int(elapsed_time)}s\n"
        f"**ETA**: {eta}s"
    )

    # Check if 10 seconds have passed since the last update
    if time.time() - last_update_time >= 10:  # Update every 10 seconds
        if last_msg != progress_msg:  # Only update if message content has changed
            try:
                await message.edit_text(progress_msg)  # Send the updated progress message
                last_msg = progress_msg  # Store the new message as the last message
                last_update_time = time.time()  # Update the last update time
            except Exception as e:
                print(f"Error updating message: {e}")
                pass


def extract_terabox_surl(link):
    # Regular Expression to identify TeraBox links with "tera" and extract the surl
    regex = r"(?:https?:\/\/(?:www\.)?[^\/]*tera[^\/]*\/s\/|surl=)([a-zA-Z0-9]+)"
    
    # Match the link with the regex
    match = re.search(regex, link)
    
    if match:
        return match.group(1)  # Return the extracted surl
    else:
        return None
                    

def teralinks_ex(id):
    # The URL of the form action
    url = "https://moneymatteronline.com/"

    # The form data to send
    payload = {
        "clickarlink": id
    }

    try:
        # Make the POST request
        response = requests.post(url, data=payload, allow_redirects=True)

        # Get the response body
        response_body = response.text

        # Use regex to find the TeraBox URL with "/s/" in the response
        terabox_url_regex = r"https?:\/\/(?:www\.)?[^\/]*tera[^\/]*\/s\/[^\s\"'>]+"
        match = re.search(terabox_url_regex, response_body)

        if match:
            # Return the extracted TeraBox URL
            return match.group(0)
        else:
            # Return a message if no TeraBox URL is found
            return None
    except requests.RequestException as e:
        # Handle errors
        return None

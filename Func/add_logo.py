import subprocess
import re
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from globals import logo_path



# Regular expression to extract time progress from FFmpeg output
time_regex = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

# Function to get video duration using FFprobe
def get_video_duration(m3u8_url):
    try:
        ffprobe_command = [
            "ffprobe", "-i", m3u8_url, "-show_entries", "format=duration",
            "-v", "quiet", "-of", "csv=p=0"
        ]
        result = subprocess.run(ffprobe_command, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration: {e}")
        return None

# Function to run FFmpeg and update progress
async def download_video_with_logo(message: Message, m3u8_url, output_file):
    duration = get_video_duration(m3u8_url)  # Get video duration in seconds
    if not duration:
        await message.edit_text("❌ Failed to retrieve video duration.")
        return
    if not os.path.isfile(logo_path):
        print(f"❌ Logo file not found at: {logo_path}")
        exit(1)
    #await message.edit_text("📥 **Starting download and conversion...**")
    
    # FFmpeg command
    ffmpeg_command = [
        "ffmpeg", 
        "-i", m3u8_url,                          # Input M3U8 URL
        "-i", logo_path,                         # Input logo
        "-filter_complex", "overlay=W-w-10:H-h-10",      # Add logo at top-left (10px from edges)
        "-c:v", "libx264",                       # Use H.264 codec for video compression
        "-c:a", "aac",                           # Use AAC codec for audio
        "-strict", "experimental",               # Ensure compatibility
        output_file
    ]

    # Start FFmpeg process
    process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True)

    last_update = time.time()  # To track progress updates
    last_msg = ""  # To store the last sent progress message

    # Read FFmpeg output line by line
    while process.poll() is None:
        line = process.stderr.readline()
        if not line:
            continue

        # Extract current time progress from FFmpeg output
        match = time_regex.search(line)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))

            # Calculate current time in seconds
            current_time = hours * 3600 + minutes * 60 + seconds

            # Calculate progress percentage
            progress = (current_time / duration) * 100
            progress = min(progress, 100)  # Cap at 100%

            # Update every 10 seconds
            if time.time() - last_update > 10:
                new_msg = f"⏳ **Progress:** `{progress:.2f}%`\n🎥 **FFmpeg is processing...**"
                if new_msg != last_msg:  # Avoid duplicate updates
                    await message.edit_text(new_msg)
                    last_msg = new_msg
                last_update = time.time()

    # Check if FFmpeg completed successfully
    if process.returncode == 0:
        await message.edit_text("✅ **Download and conversion complete! Uploading...**")
    else:
        await message.edit_text("❌ **FFmpeg process failed!**")
    return duration
        

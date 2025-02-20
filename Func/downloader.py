import aiohttp
import asyncio
import os, re
import time
import subprocess
import humanize
from tqdm import tqdm
from urllib.parse import urlparse

# Set the download directory (change this easily)
dldir = "downloads"

# Ensure the directory exists
os.makedirs(dldir, exist_ok=True)

# Function to format bytes into human-readable sizes
def format_size(size):
    return humanize.naturalsize(size, binary=True)

# Function to determine file type from MIME type
def get_file_type(mime_type):
    if mime_type.startswith("video/"):
        return "video"
    elif mime_type.startswith("audio/"):
        return "audio"
    elif mime_type.startswith("image/"):
        return "image"
    elif mime_type.startswith("application/") or mime_type.startswith("text/"):
        return "document"
    else:
        return "unknown"

# Function to get file info (checks if M3U8, gets filename, size, and type)
async def get_file_info(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.head(url, allow_redirects=True) as response:
                if response.status != 200:
                    return {"error": f"URL not accessible, status: {response.status}"}

                content_type = response.headers.get("Content-Type", "")
                
                # Check if it's an M3U8 file
                is_m3u8 = "application/vnd.apple.mpegurl" in content_type or url.endswith(".m3u8")

                # Get file size
                file_size = response.headers.get("Content-Length")
                file_size = int(file_size) if file_size else None

                # Extract filename
                content_disposition = response.headers.get("Content-Disposition", "")
                if "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[-1].strip().strip('"')
                else:
                    filename = os.path.basename(urlparse(url).path)

                # If filename is missing, generate one
                extension = "mp4" if is_m3u8 else "bin"
                if not filename:
                    filename = f"file_{int(time.time())}.{extension}"

                # Determine file type
                file_type = get_file_type(content_type)
                if is_m3u8:
                    file_type = "video"
                    filename = filename.replace(".m3u8",".mp4")
                return {
                    "url": url,
                    "filename": filename,
                    "file_size": file_size,
                    "is_m3u8": is_m3u8,
                    "file_type": file_type
                }
        except Exception as e:
            return {"error": str(e)}


# Function to download a file with progress tracking
async def download_file(url, msg, filename=None, chunk_size=1024 * 1024):
    file_info = await get_file_info(url)
    if "error" in file_info:
        print(f"Error: {file_info['error']}")
        await msg.edit_text(f"Err getting file data: {file_info['error']}")
        return {"error":file_info['error']}

    filename = filename or file_info["filename"]
    file_size = file_info["file_size"]
    
    # Ensure filename is saved in the specified directory
    file_path = os.path.join(dldir, filename)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"Error: Unable to download file, status {response.status}")
                    await msg.edit_text(f"Error: Unable to download file, status {response.status}")
                    return
                
                with open(file_path, "wb") as f:
                    start_time = time.time()
                    downloaded = 0

                    # If file size is unknown, download normally
                    if not file_size:
                        print(f"Downloading {filename} (Unknown size)...")
                        await msg.edit_text(f"Downloading {filename} (Unknown size)")
                        async for chunk in response.content.iter_chunked(chunk_size):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Calculate percentage, speed
                            elapsed_time = time.time() - start_time
                            speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                             
                            await print_progress(filename=filename, downloaded=downloaded, total_size=None, speed=speed, eta=None, st=start_time, msg=msg)
                        print(f"\nDownload complete: {file_path}")
                        await msg.edit_text(f"Download complete: {file_path}")
                        return
                    
                    # If file size is known, show progress
                    with tqdm(total=file_size, unit="B", unit_scale=True, desc=filename) as progress:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Calculate percentage, speed, and ETA
                            elapsed_time = time.time() - start_time
                            speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                            eta = (file_size - downloaded) / speed if speed > 0 else 0

                            # Print progress
                            progress.update(len(chunk))
                            await print_progress(filename, downloaded, file_size, speed, eta, st=start_time, msg=msg)

        except Exception as e:
            print(f"Download failed: {str(e)}")
            await msg.edit_text(f"Download failed: {str(e)}")
            return {"error": f"ERR on download : {str(e)}"}

    print(f"\nDownload complete: {file_path}")
    await msg.edit_text(f"Download complete: {file_path}")
    return {"ok":f"{file_path}"}


async def download_m3u8(url, msg, filename):
    file_path = os.path.join(dldir, filename)
    print(f"Downloading M3U8 stream: {url} -> {file_path}")
    await msg.edit_text(f"Downloading M3U8 stream: {url} -> {file_path}")

    command = [
        "ffmpeg", "-i", url, "-c", "copy", "-bsf:a", "aac_adtstoasc", file_path, "-progress", "pipe:1"
    ]

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        start_time = time.time()
        duration = None
        last_update = time.time()

        while True:
            output = process.stderr.readline()
            if not output:
                break
            
            # Extract video duration
            if duration is None:
                match = re.search(r"Duration:\s(\d+):(\d+):(\d+.\d+)", output)
                if match:
                    h, m, s = map(float, match.groups())
                    duration = h * 3600 + m * 60 + s  # Convert to seconds

            # Extract current progress time
            time_match = re.search(r"time=(\d+):(\d+):(\d+.\d+)", output)
            if time_match:
                h, m, s = map(float, time_match.groups())
                current_time = h * 3600 + m * 60 + s  # Convert to seconds

                if duration:
                    percent = (current_time / duration) * 100
                    elapsed = time.time() - start_time
                    eta = (elapsed / percent) * (100 - percent) if percent > 0 else 0

                    # Update every 10 seconds
                    if time.time() - last_update >= 10:
                        last_update = time.time()
                        await msg.edit_text(
                            f"📥 Downloading...\n"
                            f"📝 File: `{filename}`\n"
                            f"⏳ Progress: `{percent:.2f}%`\n"
                            f"⏱ Elapsed: `{int(elapsed)}s`\n"
                            f"⌛ ETA: `{int(eta)}s`"
                        )

        process.wait()

        if process.returncode != 0:
            await msg.edit_text(f"❌ FFmpeg failed to download M3U8 stream.")
            return {"error": "ERR on ffmpeg download m3u8."}

        await msg.edit_text(f"✅ M3U8 Download complete: `{filename}`")
        return {"ok": file_path}

    except Exception as e:
        await msg.edit_text(f"❌ Error downloading M3U8: {str(e)}")
        return {"error": f"ERR on download m3u8: {str(e)}"}

#handled m3u8 dl
async def download_m3u8_2(url, msg, filename):
    filename = os.path.join(dldir, filename)  # Save in the specified directory
    print(f"Downloading M3U8 stream: {url} -> {filename}")
    await msg.edit_text(f"Downloading M3U8 stream: {url} -> {filename}")
    file_path = os.path.join(dldir, filename)

    
    command = [
        "ffmpeg", "-i", url, "-c", "copy", "-bsf:a", "aac_adtstoasc", file_path
    ]

    try:
        # Use asyncio for non-blocking process management
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        start_time = time.time()
        downloaded = 0

        async for line in process.stdout:
            # Extract progress from FFmpeg logs
            if "time=" in line:
                elapsed_time = time.time() - start_time
                downloaded += 1024 * 1024  # Simulating 1MB per log update

                speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                await print_progress(filename, downloaded, None, speed, elapsed_time, st=start_time, msg=msg)
        
        # Wait for the process to finish
        await process.wait()

        if process.returncode != 0:
            print(f"Error: FFmpeg failed to download M3U8 stream.")
            await msg.edit_text(f"Error: FFmpeg failed to download M3U8 stream.")
            return {"error": f"ERR on ffmpeg download m3u8."}

        else:
            print(f"\nM3U8 Download complete: {filename}")
            await msg.edit_text(f"\nM3U8 Download complete: {filename}")
            return {"ok":f"{file_path}"}
    
    except Exception as e:
        print(f"Error downloading M3U8: {str(e)}")
        await msg.edit_text(f"Error downloading M3U8: {str(e)}")
        return {"error": f"ERR on download m3u8: {str(e)}"}


last_msg=""
last_t=0
# Function to print progress updates
async def print_progress(filename, downloaded, total_size, speed, eta, st, msg=None):
    global last_msg, last_t
    eta_str = f"{int(eta)}s" if eta else "Unknown"
    percent_done = f"{(downloaded / total_size) * 100:.2f}%" if total_size else "Unknown"
    speed_str = format_size(speed) + "/s" if speed else "Unknown"
    size_done = format_size(downloaded)
    total_size_str = format_size(total_size) if total_size else "Unknown"

    print(f"\r{filename}: {size_done}/{total_size_str} ({percent_done}) at {speed_str}, ETA: {eta_str}", end="", flush=True)
    if msg:
        if last_t == 0 or time.time() - last_t >= 10:
            new_msg = f"**Downloading...**\n\nName : {filename}\nDone : {size_done}/{total_size_str}\nP : {percent_done}\nSpeed : {speed_str}\nETA: {eta_str}"
            if last_msg != new_msg:
                await msg.edit_text(new_msg)
                last_msg = new_msg
                last_t = time.time()

# Function to start the download (supports custom filename)
async def dl(url, msg, custom_filename=None):
    file_info = await get_file_info(url)

    if "error" in file_info:
        print(f"Error: {file_info['error']}")
        await msg.edit_text(f"Err getting file data: {file_info['error']}")
        return {"error": file_info["error"]}

    filename = custom_filename if custom_filename else file_info["filename"]
    file_path = os.path.join(dldir, filename)

    try:
        if file_info["is_m3u8"]:
            # Call download_m3u8 function
            dlf=await download_m3u8(url, msg=msg, filename=filename)
        else:
            # Call download_file function
            dlf=await download_file(url, msg=msg, filename=filename)
        if not "error" in dlf:
            return {"filename": filename, "file_path": file_path}
        else:
            return {"error": dlf['error']}
    
    except Exception as e:
        print(f"Error during download: {str(e)}")
        await msg.edit_text(f"Error: {str(e)}")
        return {"error": str(e)}


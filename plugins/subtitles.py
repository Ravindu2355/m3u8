import os, json
import time
import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Func.simples import mention_user, generate_thumbnail, get_tg_filename
from plugins.converter import progress_callback
from plugins.live_rec2 import upload_and_start_new_file

# Store user data
user_files = {}

# Command to handle video messages
#@Client.on_message(filters.video & filters.private)
#async def video_handler(bot, message):
    #user_files[message.from_user.id] = {"video": message.video.file_id}
    #await message.reply_text("Now, please send me the **SRT** or **ASS** subtitle file by replying to this video.")

# Command to handle subtitle files
#@Client.on_message(filters.document & filters.private)
async def subtitle_handler(bot, message):
    if not message.reply_to_message or not message.reply_to_message.video:
        return await message.reply_text("Please send a **video first**, then reply with the subtitle file.")

    file_ext = message.document.file_name.split(".")[-1].lower()
    if file_ext not in ["srt", "ass"]:
        await message.reply_text("Only **SRT** or **ASS** subtitle files are supported.")
        return 

    #user_files[message.from_user.id]["subtitle"] = message.document.file_id
    await message.reply(
        "**Subtitle Merger**\n\n**Select the subtitle method:**\n\n **Burn-in**:Best method.That subs are pernement part of video.\n **Move_text**:Also working in most of devices but some tvs will not supporting.but faster than burn-in",
        reply_to_message_id=message.id,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Burn-in (Hardcoded/Slow)", callback_data="burn")],
            [InlineKeyboardButton("📝 Move Text (Softcoded/Fast)", callback_data="mov_text")]
        ])
    )
    
download_path = "./downloads"



# Handle subtitle merging method
@Client.on_callback_query(filters.regex(r"burn|mov_text"))
async def process_subtitles(bot, query):
    q_msg = query.message
    await q_msg.edit_text(f"**Subtitle Merger**\n\n- {query.data}")
    if not q_msg.reply_to_message or not q_msg.reply_to_message.document:
        return
    doc_msg = q_msg.reply_to_message
    if not doc_msg.reply_to_message_id:
        await q_msg.edit_text(f"srt was not replying to another")
        return
    vid_msg = await bot.get_messages(q_msg.chat.id, doc_msg.reply_to_message_id)
    if not vid_msg or not vid_msg.video:
        if not vid_msg.document or "video" not in vid_msg.document.mime_type:
            await q_msg.edit_text(f"srt was not replying to video")
            return
    
    #if or "video" not in user_files[user_id] or "subtitle" not in user_files[user_id]:
        #return await query.message.edit_text("Something went wrong. Please restart the process.")

    method = query.data
    #video_path = f".mp4"
    #sub_path = f"_sub.srt"
    #output_path = f"{}_output.mp4"

    # Download video and subtitle files
    msg = await query.message.edit_text("Downloading files...")
    #video = await bot.download_media(user_files[user_id]["video"], file_name=video_path)
    if not os.path.exists(download_path):
            os.makedirs(download_path)
    tgORN = await get_tg_filename(vid_msg)
    video_path = os.path.join(download_path, tgORN)
    sub_f = f"{video_path}_sub.srt"
    sub_path = os.path.join(download_path, sub_f)
    output_path = f"{video_path}_subRvx.mp4"

    # Initialize progress tracking
    last_update = {"time": 0, "msg": ""}
    # Start downloading the files
    try:
        start_time = time.time()
        video = await vid_msg.download(
            file_name=video_path,
            progress=progress_callback,
            progress_args=(q_msg, "Downloading...", start_time,last_update)
            )
        #subtitle = await bot.download_media(user_files[user_id]["subtitle"], file_name=sub_path)
        subtitle = await doc_msg.download(
            file_name=sub_path
        )
    except Exception as e:
        await msg.edit_text(f"❌ **Error on Download Files:** \n\n{str(e)}")

    await msg.edit_text("Merging subtitles...")

    # Select FFmpeg command based on method
    if method == "burn":
        ffmpeg_cmd = [
            "ffmpeg", "-i", video_path, "-vf", f"subtitles={sub_path}", "-c:a", "copy", output_path
        ]
    else:
        ffmpeg_cmd = [
            "ffmpeg", "-i", video_path, "-i", sub_path, "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text", output_path
        ]

    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    start_time = time.time()

    # Progress update loop
    while True:
        await asyncio.sleep(10)
        if process.returncode is not None:
            break  # Exit loop if FFmpeg has finished

        # Get progress percentage
        elapsed_time = time.time() - start_time
        percentage = min(int((elapsed_time / 60) * 100), 100)
        eta = max(int((60 - elapsed_time)), 0)

        pr_msg = f"⏳ Progress: {percentage}%\n⏱ ETA: {eta} sec"
        if pr_msg != last_update["msg"]:
           await msg.edit_text(pr_msg)
           last_update["msg"] = pr_msg

    await process.wait()

    # Send the processed video
    await msg.edit_text("Uploading new video...")
    #await bot.send_video(user_id, video=output_path, caption="Here is your video with subtitles!")
    start_time = time.time()
    await upload_and_start_new_file(bot, msg, output_path, start_time)
    # Cleanup
    os.remove(video_path)
    os.remove(sub_path)
    #os.remove(output_path)

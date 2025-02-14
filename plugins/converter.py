import os, asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Func.simples import mention_user, generate_thumbnail, get_tg_filename
from Func.m3u8 import download_and_convert_video
#from plugins.subtitles import subtitle_handler

# A global dictionary to store messages for handling callbacks
DOWNLOAD_TASKS = {}


def changeFileExt(filename: str, new_extension: str) -> str:
    
    # Ensure new_extension starts with a dot
    if not new_extension.startswith('.'):
        new_extension = '.' + new_extension

    # Get the filename without its current extension
    name, _ = os.path.splitext(filename)

    # Return the new filename with the changed extension
    return name + new_extension


# Helper function for human-readable size format
def human_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

# Progress callback for downloads (updated with floodwait protection)
async def progress_callback(current, total, message: Message, p_title, start_time, last_update):
    global last_progress_msg
    elapsed_time = time.time() - start_time
    speed = current / elapsed_time / 1024
    progress = (current / total) * 100
    eta = (total - current) / (speed * 1024) if speed > 0 else 0

    # Create progress message
    progress_msg = (
        f"**{p_title}**\n"
        f"**Progress:** {progress:.2f}%\n"
        f"**Done:** {human_readable_size(current)} / {human_readable_size(total)}\n"
        f"**Speed:** {speed:.2f} KB/s\n"
        f"**ETA:** {int(eta)}s"
    )

    # Update message every 10 seconds and avoid duplicates
    if time.time() - last_update["time"] > 10 and last_update["msg"] != progress_msg:
        try:
            await message.edit_text(progress_msg)
            last_update["time"] = time.time()
            last_update["msg"] = progress_msg
        except Exception as e:
            print(f"Error updating progress: {e}")

# Command handler: Listen for forwarded video or video documents
@Client.on_message(filters.video | filters.document)
async def handle_forwarded_file(client, message: Message):
    # Check if it's a document and ensure it is a video file
    if message.document and "video" not in message.document.mime_type:
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
               [InlineKeyboardButton("🔥 Burn-in H264-crf23 (Hardcoded/Slow)", callback_data="l264crf23")],
               [InlineKeyboardButton("🔥 Burn-in H264-crf28 (Hardcoded/Slow)", callback_data="l264crf28")],
               [InlineKeyboardButton("📝 Move Text (Softcoded/Fast)", callback_data="mov_text")],
               [InlineKeyboardButton("📃 MKV Mux (Softcoded/Fast)", callback_data="mkv_mux")],
               [InlineKeyboardButton("❌️**Cancel**", callback_data="cancel")],
            ])
        )
        #await message.reply("❌ This document is not a video file.")
        return
    
    # Reply with inline buttons
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎥 MP4", callback_data=f"convertTo_mp4")],
            [InlineKeyboardButton("🎥 MKV", callback_data=f"convertTo_mkv")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
             
        ]
    )
    await client.send_message(chat_id=message.chat.id,text="🎥 **What would you like to do with this file?**", reply_to_message_id=message.id, reply_markup=buttons)
    #DOWNLOAD_TASKS[str(message.id)] = message
    
def safe_progress_callback(callback, *args):
    def wrapper(current, total):
        asyncio.create_task(callback(current, total, *args))
    return wrapper

# Callback query handler for button actions
@Client.on_callback_query(filters.regex(r"^convertTo_"))
async def handle_button_click_convert(client, query: CallbackQuery):
    user_action = query.data
    q_msg = query.message
    original_msg = q_msg.reply_to_message
    if user_action == "cancel":
        #await query.answer("❌ Cancelled.")
        await query.message.edit_text("🔰Operation cancelled.🪚")
        return

    # Extract the message ID from the callback data
    if user_action.startswith("convertTo_"):
        converting_type = user_action.split("_")[1]
        #if original_msg_id in DOWNLOAD_TASKS:
            #original_message = DOWNLOAD_TASKS[original_msg_id]
        if original_msg:
            await q_msg.edit_text("📥 Starting download...")

            # Edit message to show progress
            await q_msg.edit_text("📥 **Downloading... Please wait.**")

            # Set up download path
            download_path = "./downloads"
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            tgORN = await get_tg_filename(original_msg)
            file_name = os.path.join(download_path, tgORN)
            # Initialize progress tracking
            last_update = {"time": 0, "msg": ""}

            # Start downloading the file
            try:
                start_time = time.time()
                downloaded_file_path = await original_msg.download(
                    file_name=file_name,
                    progress=progress_callback,
                    progress_args=(q_msg, "Downloading...", start_time,last_update)
                 )

                # Notify the user after download
                await q_msg.edit_text(f"✅ **File downloaded successfully!**\n**Path:** `{downloaded_file_path}`")
                print(f"File saved to: {downloaded_file_path}")
                start_time = time.time()
                output_file = changeFileExt(tgORN,converting_type) #f"output.{converting_type}"
                thumb_file = "thumb.jpg"

                duration = await download_and_convert_video(q_msg, downloaded_file_path, output_file)

                if not os.path.exists(output_file):
                    await q_msg.edit_text("❌ Failed to download or convert the video.")
                    return

                # Generate thumbnail
                await q_msg.edit_text("🖼 **Generating new thumbnail...**")
                generate_thumbnail(output_file, thumb_file)

                if not os.path.exists(thumb_file):
                    await q_msg.edit_text("❌ Failed to gebarate thumb")
                    return
                await q_msg.edit_text("📤 **Uploading video with thumbnail...**")
                upload_start_time = time.time()

                with open(output_file, "rb") as video, open(thumb_file, "rb") as thumb:
                    await client.send_video(
                          chat_id=original_msg.chat.id,
                          video=video,
                          duration=int(duration),
                          thumb=thumb,  # Attach the generated thumbnail
                          caption=f"✅ **Here is yor video!**✅️\n\n{output_file}",
                          supports_streaming=True,  # Enables streaming
                          progress=progress_callback,
                          progress_args=(q_msg, "Uploading...", upload_start_time,last_update)
                         )

                         #await message.reply("✅ **Upload complete!**")
                await q_msg.delete();
                os.remove(output_file)
                os.remove(thumb_file)
                os.remove(downloaded_file_path)
            except Exception as e:
                await q_msg.edit_text(f"❌ **Error:** {str(e)}")
        else:
            await q_msg.edit_text("❌ Message not found or expired.")

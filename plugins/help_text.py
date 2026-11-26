from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from globals import AuthU, setThumb, getThumb, deleteThumb
from Func.simples import mention_user

@Client.on_message(filters.command("start"))
async def st_rep(client,message:Message):
    await message.reply(f"**🔰RVX M3U8 Downloader🔰\n\n❤️Welcome {mention_user(message)}💪!\n😎I am an simple M3U8 link uploader bot.\n😊Give me a m3u8 link with `/m3u8 <DirectLink>` and \n😇I will upload it to telegram as `video - mp4`😎**")

@Client.on_message(filters.command("help"))
async def st_help(client,message:Message):
    await message.reply("🫠**No avalable!**\n\n**Commands: **\n\n  /start\n  /help\n  /checkauth\n  /addauth\n  /removeauth\n  /m3u8\n  /logo : use carefully")

@Client.on_callback_query(filters.regex(r"cancel"))
async def cancelQ(client,query):
    await query.message.edit_text("🔰Operation cancelled.🪚")
    
# ==========================================
# SET THUMBNAIL
# ==========================================

@Client.on_message(filters.command("set_thumb"))
async def _setThumb(client, message: types.Message):

    # Must reply to a message
    if not message.reply_to_message:
        await message.reply(
            "⚠️ Reply to an image/photo with `/set_thumb`."
        )
        return

    replied = message.reply_to_message

    # Accept photo
    if replied.photo:
        file_id = replied.photo.file_id

    # Accept image document
    elif replied.document:
        mime = replied.document.mime_type or ""

        if not mime.startswith("image/"):
            await message.reply("❌ The replied document is not an image.")
            return

        file_id = replied.document.file_id

    else:
        await message.reply(
            "❌ Reply to a photo or image document."
        )
        return

    status = await message.reply("⏳ Downloading thumbnail...")

    try:
        # Download file
        downloaded_path = await client.download_media(
            replied,
            file_name="thumbnails/downloaded_thumb"
        )

        if not downloaded_path:
            await status.edit("❌ Thumbnail download failed.")
            return

        # Save as our permanent thumbnail
        saved_path = setThumb(downloaded_path)

        if not saved_path:
            await status.edit("❌ Failed to save thumbnail.")
            return

        # Remove temporary downloaded file
        import os

        if downloaded_path != saved_path and os.path.exists(downloaded_path):
            os.remove(downloaded_path)

        await status.edit(
            "✅ **Custom thumbnail updated!**\n\n"
            f"📁 Path: `{saved_path}`"
        )

    except Exception as e:
        await status.edit(
            f"❌ Failed to set thumbnail:\n`{e}`"
        )


# ==========================================
# GET THUMBNAIL
# ==========================================

@Client.on_message(filters.command("get_thumb"))
async def _getThumb(client, message: types.Message):

    thumb = getThumb()

    if not thumb:
        await message.reply("⚠️ No custom thumbnail is currently set.")
        return

    if not os.path.exists(thumb):
        await message.reply("❌ Thumbnail file not found.")
        return

    await message.reply_photo(
        photo=thumb,
        caption="🖼️ **Current Custom Thumbnail**"
    )


# ==========================================
# DELETE THUMBNAIL
# ==========================================

@Client.on_message(filters.command("del_thumb"))
async def _delThumb(client, message: types.Message):

    deleted = deleteThumb()

    if deleted:
        await message.reply(
            "🗑️ **Custom thumbnail deleted!**\n\n"
            "The bot will now use its default thumbnail."
        )
    else:
        await message.reply(
            "⚠️ No custom thumbnail is currently set."
)

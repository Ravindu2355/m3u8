import os
import tempfile
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from PIL import Image
import numpy as np
import imageio
from lottie.parsers.tgs import parse_tgs

# Temporary user session store
user_states = {}

# Function to convert .tgs (Lottie) to gif/webm/mp4
def convert_tgs_lottie(tgs_path, output_path, output_format="webm", width=512, height=512, fps=30):
def convert_tgs_lottie(tgs_path, output_path, output_format="webm", width=512, height=512, fps=30):
    animation = parse_tgs(tgs_path)
    anim_data = animation.animation  # Access internal data

    ip = anim_data.ip  # in frame
    op = anim_data.op  # out frame
    fr = anim_data.fr  # frame rate in the animation metadata

    duration_frames = int((op - ip) * (fps / fr))  # total output frames

    frames = []
    for frame_num in range(duration_frames):
        time = ip + (frame_num / fps) * fr
        img = animation.render_frame(time)
        img = img.convert("RGBA").resize((width, height), Image.ANTIALIAS)
        frames.append(np.array(img))

    if output_format == "gif":
        imageio.mimsave(output_path, frames, format="GIF", duration=1 / fps)
    else:
        codec = "libvpx-vp9" if output_format == "webm" else "libx264"
        writer = imageio.get_writer(output_path, fps=fps, codec=codec)
        for frame in frames:
            writer.append_data(frame)
        writer.close()
        
# Handle incoming .tgs file or animated sticker
@Client.on_message(filters.private & (filters.sticker | filters.document))
async def handle_tgs_input(client: Client, message: Message):
    tgs = None
    if message.document and message.document.file_name.endswith(".tgs"):
        tgs = message.document
    elif message.sticker and message.sticker.is_animated:
        tgs = message.sticker

    if not tgs:
        return await message.reply("❌ Please send an animated `.tgs` sticker or file.")

    user_states[message.from_user.id] = {"file": tgs}
    await message.reply(
        "📤 Choose output format:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("GIF", callback_data="fmt_gif"),
             InlineKeyboardButton("WebM", callback_data="fmt_webm"),
             InlineKeyboardButton("MP4", callback_data="fmt_mp4")]
        ])
    )

@Client.on_callback_query(filters.regex(r"^fmt_"))
async def choose_format(client: Client, query: CallbackQuery):
    fmt = query.data.split("_")[1]
    user_states[query.from_user.id]["format"] = fmt
    await query.message.edit_text(
        "📐 Choose resolution:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("256px", callback_data="res_256"),
             InlineKeyboardButton("512px", callback_data="res_512"),
             InlineKeyboardButton("1080px", callback_data="res_1080")]
        ])
    )

@Client.on_callback_query(filters.regex(r"^res_"))
async def choose_resolution(client: Client, query: CallbackQuery):
    res = int(query.data.split("_")[1])
    user_states[query.from_user.id]["size"] = res
    await query.message.edit_text(
        "🎞 Choose FPS:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("25 FPS", callback_data="fps_25"),
             InlineKeyboardButton("30 FPS", callback_data="fps_30"),
             InlineKeyboardButton("60 FPS", callback_data="fps_60")]
        ])
    )

@Client.on_callback_query(filters.regex(r"^fps_"))
async def choose_fps_and_render(client: Client, query: CallbackQuery):
    fps = int(query.data.split("_")[1])
    state = user_states.pop(query.from_user.id, None)

    if not state or "file" not in state or "format" not in state or "size" not in state:
        return await query.message.edit_text("⚠️ Session expired or missing data. Please resend the `.tgs` file.")

    tgs_file = state["file"]
    fmt = state["format"]
    res = state["size"]

    await query.message.edit_text("🛠 Rendering... Please wait.")

    with tempfile.TemporaryDirectory() as tmpdir:
        tgs_path = os.path.join(tmpdir, "input.tgs")
        output_path = os.path.join(tmpdir, f"output.{fmt}")

        await client.download_media(tgs_file, file_name=tgs_path)

        try:
            convert_tgs_lottie(tgs_path, output_path, output_format=fmt, width=res, height=res, fps=fps)
            caption = f"✅ Converted to `{fmt.upper()}` | {res}px @ {fps}fps"
            if fmt == "gif":
                await query.message.reply_document(output_path, caption=caption)
            else:
                await query.message.reply_video(output_path, caption=caption)
            await query.message.delete()
        except Exception as e:
            await query.message.edit_text(f"❌ Conversion failed:\n`{e}`")

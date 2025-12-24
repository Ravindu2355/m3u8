import time
import asyncio
from pyrogram.errors import FloodWait

async def safe_edit(msg, text):
    """Safely edit a message handling FloodWait."""
    try:
        await msg.edit_text(text)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        await safe_edit(msg, text)
    except:
        pass  # Ignore other edit errors

async def progress_updater(msg, prefix, current, total, last_update):
    """Update progress every 5 seconds without duplicate edits."""
    now = time.time()
    if now - last_update["time"] >= 5:
        pct = current / total * 100 if total else 0
        text = f"⏳ {prefix}\nProgress: `{pct:.2f}%`"
        if text != last_update["msg"]:
            await safe_edit(msg, text)
            last_update["msg"] = text
            last_update["time"] = now

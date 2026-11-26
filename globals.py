from config import Config
import os

AuthU = Config.AUTH
custom_command = ''
logo_path = "Picsart_24-12-17_15-38-54-431.png"
m3u8Status = 0

# ==========================================
# THUMBNAIL SETTINGS
# ==========================================

THUMB_DIR = "thumbnails"
THUMB_PATH = os.path.join(THUMB_DIR, "custom_thumb.jpg")

os.makedirs(THUMB_DIR, exist_ok=True)


def setThumb(path):
    """
    Set custom thumbnail from an existing image file.
    """
    global THUMB_PATH

    if not os.path.exists(path):
        return False

    # Ensure destination folder exists
    os.makedirs(THUMB_DIR, exist_ok=True)

    # Copy file to our custom thumbnail location
    import shutil

    shutil.copy2(path, THUMB_PATH)

    return THUMB_PATH


def getThumb():
    """
    Get custom thumbnail path.
    Returns None if no custom thumbnail exists.
    """
    if os.path.exists(THUMB_PATH):
        return THUMB_PATH

    return None


def deleteThumb():
    """
    Delete custom thumbnail.
    """
    if os.path.exists(THUMB_PATH):
        os.remove(THUMB_PATH)
        return True

    return False

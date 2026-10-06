import os
import logging
from typing import Optional
from aiogram.types import FSInputFile
from PIL import Image

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVER_FILE = os.path.join(BASE_DIR, "cover.jpeg")
COVER_THUMB_FILE = os.path.join(BASE_DIR, "cover_thumb.jpeg")


def ensure_thumbnail() -> Optional[str]:
    """
    cover.jpeg mavjud bo'lsa, Telegram talablariga mos (320px va <200KB)
    bo'lgan cover_thumb.jpeg yaratish yoki mavjudini qaytarish.
    """
    if not os.path.exists(COVER_FILE):
        return None

    try:
        # Agar cover_thumb mavjud bo'lsa va cover.jpeg dan yangi bo'lsa, qayta yaratish shart emas
        if os.path.exists(COVER_THUMB_FILE):
            if os.path.getmtime(COVER_THUMB_FILE) >= os.path.getmtime(COVER_FILE):
                return COVER_THUMB_FILE

        # cover.jpeg dan thumbnail yasash (max 320x320)
        with Image.open(COVER_FILE) as img:
            img = img.convert("RGB")
            img.thumbnail((320, 320), Image.Resampling.LANCZOS)
            img.save(COVER_THUMB_FILE, format="JPEG", quality=85, optimize=True)

        logger.info(f"Yangi video cover_thumb yaratildi: {COVER_THUMB_FILE}")
        return COVER_THUMB_FILE
    except Exception as e:
        logger.error(f"Thumbnail yaratishda xatolik: {e}")
        return None


def get_video_cover() -> Optional[FSInputFile]:
    """Video uchun asosiy muqova (cover) faylini olish"""
    if os.path.exists(COVER_FILE):
        return FSInputFile(COVER_FILE)
    return None


def get_video_thumbnail() -> Optional[FSInputFile]:
    """Video uchun ixcham thumbnail faylini olish"""
    thumb_path = ensure_thumbnail()
    if thumb_path and os.path.exists(thumb_path):
        return FSInputFile(thumb_path)
    if os.path.exists(COVER_FILE):
        return FSInputFile(COVER_FILE)
    return None

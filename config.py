import os
from pathlib import Path
from dotenv import load_dotenv

# .env faylini yuklash
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "8759256550:AAEyaqxm-XWtLNjLObqmMetTOlKBRMhDcT0")
BOT_USERNAME = os.getenv("BOT_USERNAME", "topfilmlar_robot").replace("@", "")

# Admin ID larini list ko'rinishida olish
ADMINS_RAW = os.getenv("ADMIN_ID", "8991315532")
ADMINS = [int(admin_id.strip()) for admin_id in ADMINS_RAW.split(",") if admin_id.strip().isdigit()]

db_env = os.getenv("DATABASE_PATH")
if db_env:
    DATABASE_PATH = Path(db_env)
else:
    DATABASE_PATH = BASE_DIR / "kino_bot.db"

# Agar papka mavjud bo'lmasa yaratish
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


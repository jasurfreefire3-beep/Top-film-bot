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

# PostgreSQL sozlamalari
DB_HOST = os.getenv("DB_HOST", "psql.fr-roub1.bengt.wasmernet.com")
DB_PORT = int(os.getenv("DB_PORT", "20184"))
DB_NAME = os.getenv("DB_NAME", "TopFilm")
DB_USER = os.getenv("DB_USER", "user_162b547c")
DB_PASS = os.getenv("DB_PASS", "pw_eRvi5x1ojzOGN33QKA9Qtj6i9TVTqriq")

import aiosqlite
from typing import Optional, List, Dict, Any
from config import DATABASE_PATH


async def init_db() -> None:
    """Ma'lumotlar bazasini va jadvallarni yaratish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code INTEGER UNIQUE NOT NULL,
                title TEXT NOT NULL,
                file_id TEXT NOT NULL,
                file_type TEXT NOT NULL DEFAULT 'video',
                caption TEXT,
                views INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                invite_link TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS saved_movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                movie_code INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, movie_code)
            )
        """)
        await db.commit()


async def add_user(user_id: int, username: Optional[str], full_name: str) -> None:
    """Foydalanuvchini bazaga qo'shish yoki yangilash"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
        """, (user_id, username, full_name))
        await db.commit()


async def get_users_count() -> int:
    """Foydalanuvchilar umumiy sonini olish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_all_user_ids() -> List[int]:
    """Barcha foydalanuvchilar ID larini olish (xabar yuborish uchun)"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_next_movie_code() -> int:
    """Navbatdagi tavsiya etiladigan kino kodini olish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT MAX(code) FROM movies") as cursor:
            row = await cursor.fetchone()
            if row and row[0] is not None:
                return row[0] + 1
            return 1


async def is_movie_code_exists(code: int) -> bool:
    """Kino kodi mavjudligini tekshirish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT 1 FROM movies WHERE code = ?", (code,)) as cursor:
            return (await cursor.fetchone()) is not None


async def add_movie(code: int, title: str, file_id: str, file_type: str = "video", caption: Optional[str] = None) -> bool:
    """Yangi kinoni bazaga qo'shish"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                INSERT INTO movies (code, title, file_id, file_type, caption)
                VALUES (?, ?, ?, ?, ?)
            """, (code, title, file_id, file_type, caption))
            await db.commit()
            return True
    except Exception as e:
        print(f"Xatolik kino qo'shishda: {e}")
        return False


async def get_movie_by_code(code: int, increment_views: bool = True) -> Optional[Dict[str, Any]]:
    """Kod bo'yicha kinoni olish va ko'rishlar sonini oshirish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM movies WHERE code = ?", (code,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            movie = dict(row)

        if increment_views:
            await db.execute("UPDATE movies SET views = views + 1 WHERE code = ?", (code,))
            await db.commit()
            movie["views"] += 1

        return movie


async def search_movies_by_title(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Nom bo'yicha kinolarni qidirish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        search_pattern = f"%{query.strip()}%"
        async with db.execute("""
            SELECT code, title, views, created_at 
            FROM movies 
            WHERE title LIKE ? 
            ORDER BY id DESC 
            LIMIT ?
        """, (search_pattern, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_movies_count() -> int:
    """Kinolar umumiy sonini olish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM movies") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def delete_movie(code: int) -> bool:
    """Kino kodiga ko'ra kinoni o'chirish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("DELETE FROM movies WHERE code = ?", (code,)) as cursor:
            await db.commit()
            return cursor.rowcount > 0


async def get_recent_movies(limit: int = 10) -> List[Dict[str, Any]]:
    """Oxirgi qo'shilgan kinolar ro'yxati"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT code, title, views, created_at 
            FROM movies 
            ORDER BY id DESC 
            LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


# ------------------ MAJBURIY OBUNA KANALLARI ------------------ #

async def add_channel(channel_id: str, title: str, invite_link: str) -> bool:
    """Majburiy obuna kanalini qo'shish"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                INSERT INTO channels (channel_id, title, invite_link)
                VALUES (?, ?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET
                    title = excluded.title,
                    invite_link = excluded.invite_link
            """, (str(channel_id), title, invite_link))
            await db.commit()
            return True
    except Exception as e:
        print(f"Kanal qo'shishda xatolik: {e}")
        return False


async def get_all_channels() -> List[Dict[str, Any]]:
    """Barcha majburiy obuna kanallarini olish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM channels ORDER BY id ASC") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def delete_channel(channel_id: str) -> bool:
    """Kanalni o'chirish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("DELETE FROM channels WHERE channel_id = ?", (str(channel_id),)) as cursor:
            await db.commit()
            return cursor.rowcount > 0


async def get_channels_count() -> int:
    """Kanallar sonini olish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM channels") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


# ------------------ SAQLANGAN FILMLAR (/saved) ------------------ #

async def add_saved_movie(user_id: int, movie_code: int) -> bool:
    """Filmni foydalanuvchining saqlanganlariga qo'shish"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                INSERT OR IGNORE INTO saved_movies (user_id, movie_code)
                VALUES (?, ?)
            """, (user_id, movie_code))
            await db.commit()
            return True
    except Exception as e:
        print(f"Filmni saqlashda xatolik: {e}")
        return False


async def remove_saved_movie(user_id: int, movie_code: int) -> bool:
    """Filmni saqlanganlardan olib tashlash"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                DELETE FROM saved_movies WHERE user_id = ? AND movie_code = ?
            """, (user_id, movie_code))
            await db.commit()
            return True
    except Exception as e:
        print(f"Filmni o'chirishda xatolik: {e}")
        return False


async def is_movie_saved(user_id: int, movie_code: int) -> bool:
    """Film saqlanganligini tekshirish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT 1 FROM saved_movies WHERE user_id = ? AND movie_code = ?
        """, (user_id, movie_code)) as cursor:
            return (await cursor.fetchone()) is not None


async def get_user_saved_movies(user_id: int) -> List[Dict[str, Any]]:
    """Foydalanuvchi saqlagan barcha filmlar ro'yxatini olish"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT m.code, m.title, m.views, s.created_at as saved_at
            FROM saved_movies s
            JOIN movies m ON s.movie_code = m.code
            WHERE s.user_id = ?
            ORDER BY s.id DESC
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]




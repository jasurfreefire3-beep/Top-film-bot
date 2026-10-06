import ssl
import json
import logging
from typing import Optional, List, Dict, Any
import asyncpg
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


def get_ssl_context() -> ssl.SSLContext:
    """PostgreSQL uchun SSL konteksti"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


async def get_pool() -> asyncpg.Pool:
    """PostgreSQL ulanish poolini olish yoki yaratish"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            ssl=get_ssl_context(),
            min_size=1,
            max_size=10
        )
    return _pool


async def init_db() -> None:
    """PostgreSQL ma'lumotlar bazasini va JSONB jadvallarini yaratish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Foydalanuvchilar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                data JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Kinolar jadvali (barcha ma'lumotlar data JSONB formatida ham saqlanadi)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id SERIAL PRIMARY KEY,
                code INTEGER UNIQUE NOT NULL,
                title TEXT NOT NULL,
                file_id TEXT NOT NULL,
                file_type VARCHAR(50) NOT NULL DEFAULT 'video',
                caption TEXT,
                views INTEGER NOT NULL DEFAULT 0,
                data JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Majburiy obuna kanallari jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id SERIAL PRIMARY KEY,
                channel_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                invite_link TEXT NOT NULL,
                data JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Saqlangan filmlar jadvali (/saved)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_movies (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                movie_code INTEGER NOT NULL,
                data JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, movie_code)
            );
        """)

        # Seriallar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS series (
                id SERIAL PRIMARY KEY,
                code INTEGER UNIQUE NOT NULL,
                title TEXT NOT NULL,
                caption TEXT,
                views INTEGER NOT NULL DEFAULT 0,
                data JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Serial qismlari jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id SERIAL PRIMARY KEY,
                series_code INTEGER NOT NULL,
                episode_number INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                file_type VARCHAR(50) NOT NULL DEFAULT 'video',
                caption TEXT,
                views INTEGER NOT NULL DEFAULT 0,
                data JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(series_code, episode_number)
            );
        """)
        logger.info("PostgreSQL jadvallari, seriallar va JSON strukturalari tayyor.")


# ------------------ FOYDALANUVCHILAR ------------------ #

async def add_user(user_id: int, username: Optional[str], full_name: str) -> None:
    """Foydalanuvchini bazaga qo'shish yoki yangilash"""
    pool = await get_pool()
    user_json = json.dumps({
        "user_id": user_id,
        "username": username,
        "full_name": full_name
    })
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username, full_name, data)
            VALUES ($1, $2, $3, $4::jsonb)
            ON CONFLICT(user_id) DO UPDATE SET
                username = EXCLUDED.username,
                full_name = EXCLUDED.full_name,
                data = EXCLUDED.data;
        """, user_id, username, full_name, user_json)


async def get_users_count() -> int:
    """Foydalanuvchilar umumiy sonini olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT COUNT(*) FROM users;")
        return val or 0


async def get_all_user_ids() -> List[int]:
    """Barcha foydalanuvchilar ID larini olish (broadcast uchun)"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM users;")
        return [r["user_id"] for r in rows]


# ------------------ KINOLAR (JSON FORMATDA SAQLANADI) ------------------ #

async def get_next_movie_code() -> int:
    """Navbatdagi tavsiya etiladigan kino kodini olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        max_code = await conn.fetchval("SELECT MAX(code) FROM movies;")
        if max_code is not None:
            return max_code + 1
        return 1


async def is_movie_code_exists(code: int) -> bool:
    """Kino kodi mavjudligini tekshirish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT 1 FROM movies WHERE code = $1 LIMIT 1;", code)
        return val is not None


async def add_movie(code: int, title: str, file_id: str, file_type: str = "video", caption: Optional[str] = None) -> bool:
    """Yangi kinoni bazaga JSON formatida to'liq saqlash"""
    try:
        pool = await get_pool()
        movie_dict = {
            "code": code,
            "title": title,
            "file_id": file_id,
            "file_type": file_type,
            "caption": caption,
            "views": 0
        }
        movie_json = json.dumps(movie_dict, ensure_ascii=False)

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO movies (code, title, file_id, file_type, caption, data)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb);
            """, code, title, file_id, file_type, caption, movie_json)
            return True
    except Exception as e:
        logger.error(f"Xatolik kino qo'shishda: {e}")
        return False


async def get_movie_by_code(code: int, increment_views: bool = True) -> Optional[Dict[str, Any]]:
    """Kod bo'yicha kinoni olish va ko'rishlar sonini oshirish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM movies WHERE code = $1;", code)
        if not row:
            return None
        
        movie = dict(row)
        if increment_views:
            await conn.execute("UPDATE movies SET views = views + 1 WHERE code = $1;", code)
            movie["views"] += 1
            # JSON ma'lumot ichidagi views ni ham yangilash
            if movie.get("data"):
                try:
                    data_obj = json.loads(movie["data"]) if isinstance(movie["data"], str) else movie["data"]
                    data_obj["views"] = movie["views"]
                    await conn.execute("UPDATE movies SET data = $1::jsonb WHERE code = $2;", json.dumps(data_obj), code)
                except Exception:
                    pass

        return movie


async def search_movies_by_title(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Nom bo'yicha kinolarni qidirish"""
    pool = await get_pool()
    search_pattern = f"%{query.strip()}%"
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT code, title, views, created_at, data
            FROM movies 
            WHERE title ILIKE $1 
            ORDER BY id DESC 
            LIMIT $2;
        """, search_pattern, limit)
        return [dict(r) for r in rows]


async def get_movies_count() -> int:
    """Kinolar umumiy sonini olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT COUNT(*) FROM movies;")
        return val or 0


async def delete_movie(code: int) -> bool:
    """Kino kodiga ko'ra kinoni o'chirish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM saved_movies WHERE movie_code = $1;", code)
        res = await conn.execute("DELETE FROM movies WHERE code = $1;", code)
        # res looks like 'DELETE 1'
        return res.endswith("1")


async def get_recent_movies(limit: int = 10) -> List[Dict[str, Any]]:
    """Oxirgi qo'shilgan kinolar ro'yxati"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT code, title, views, created_at, data
            FROM movies 
            ORDER BY id DESC 
            LIMIT $1;
        """, limit)
        return [dict(r) for r in rows]


# ------------------ MAJBURIY OBUNA KANALLARI ------------------ #

async def add_channel(channel_id: str, title: str, invite_link: str) -> bool:
    """Majburiy obuna kanalini qo'shish"""
    try:
        pool = await get_pool()
        channel_json = json.dumps({
            "channel_id": str(channel_id),
            "title": title,
            "invite_link": invite_link
        }, ensure_ascii=False)

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO channels (channel_id, title, invite_link, data)
                VALUES ($1, $2, $3, $4::jsonb)
                ON CONFLICT(channel_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    invite_link = EXCLUDED.invite_link,
                    data = EXCLUDED.data;
            """, str(channel_id), title, invite_link, channel_json)
            return True
    except Exception as e:
        logger.error(f"Kanal qo'shishda xatolik: {e}")
        return False


async def get_all_channels() -> List[Dict[str, Any]]:
    """Barcha majburiy obuna kanallarini olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM channels ORDER BY id ASC;")
        return [dict(r) for r in rows]


async def delete_channel(channel_id: str) -> bool:
    """Kanalni o'chirish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute("DELETE FROM channels WHERE channel_id = $1;", str(channel_id))
        return not res.endswith("0")


async def get_channels_count() -> int:
    """Kanallar sonini olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT COUNT(*) FROM channels;")
        return val or 0


# ------------------ SAQLANGAN FILMLAR (/saved) ------------------ #

async def add_saved_movie(user_id: int, movie_code: int) -> bool:
    """Filmni foydalanuvchining saqlanganlariga qo'shish"""
    try:
        pool = await get_pool()
        saved_json = json.dumps({"user_id": user_id, "movie_code": movie_code})
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO saved_movies (user_id, movie_code, data)
                VALUES ($1, $2, $3::jsonb)
                ON CONFLICT (user_id, movie_code) DO NOTHING;
            """, user_id, movie_code, saved_json)
            return True
    except Exception as e:
        logger.error(f"Filmni saqlashda xatolik: {e}")
        return False


async def remove_saved_movie(user_id: int, movie_code: int) -> bool:
    """Filmni saqlanganlardan olib tashlash"""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM saved_movies WHERE user_id = $1 AND movie_code = $2;
            """, user_id, movie_code)
            return True
    except Exception as e:
        logger.error(f"Filmni o'chirishda xatolik: {e}")
        return False


async def is_movie_saved(user_id: int, movie_code: int) -> bool:
    """Film saqlanganligini tekshirish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        val = await conn.fetchval("""
            SELECT 1 FROM saved_movies WHERE user_id = $1 AND movie_code = $2 LIMIT 1;
        """, user_id, movie_code)
        return val is not None


async def get_user_saved_movies(user_id: int) -> List[Dict[str, Any]]:
    """Foydalanuvchi saqlagan barcha filmlar va seriallar ro'yxatini olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                COALESCE(m.code, s.code) as code,
                COALESCE(m.title, s.title) as title,
                COALESCE(m.views, s.views) as views,
                sm.created_at as saved_at,
                CASE WHEN s.code IS NOT NULL THEN 'series' ELSE 'movie' END as item_type
            FROM saved_movies sm
            LEFT JOIN movies m ON sm.movie_code = m.code
            LEFT JOIN series s ON sm.movie_code = s.code
            WHERE sm.user_id = $1 AND (m.code IS NOT NULL OR s.code IS NOT NULL)
            ORDER BY sm.id DESC;
        """, user_id)
        return [dict(r) for r in rows]


# ------------------ SERIALLAR VA QISMLAR (JSON FORMATDA) ------------------ #

async def get_next_series_code() -> int:
    """Navbatdagi tavsiya etiladigan serial kodini olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        max_movie = await conn.fetchval("SELECT MAX(code) FROM movies;") or 0
        max_series = await conn.fetchval("SELECT MAX(code) FROM series;") or 0
        return max(max_movie, max_series) + 1


async def is_series_code_exists(code: int) -> bool:
    """Serial kodi mavjudligini tekshirish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT 1 FROM series WHERE code = $1 LIMIT 1;", code)
        return val is not None


async def add_series(code: int, title: str, caption: Optional[str] = None) -> bool:
    """Yangi serial yaratish"""
    try:
        pool = await get_pool()
        series_json = json.dumps({
            "code": code,
            "title": title,
            "caption": caption,
            "views": 0,
            "type": "series"
        }, ensure_ascii=False)

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO series (code, title, caption, data)
                VALUES ($1, $2, $3, $4::jsonb);
            """, code, title, caption, series_json)
            return True
    except Exception as e:
        logger.error(f"Serial yaratishda xatolik: {e}")
        return False


async def get_series_by_code(code: int, increment_views: bool = True) -> Optional[Dict[str, Any]]:
    """Serial ma'lumotlarini olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM series WHERE code = $1;", code)
        if not row:
            return None
        series = dict(row)
        if increment_views:
            await conn.execute("UPDATE series SET views = views + 1 WHERE code = $1;", code)
            series["views"] += 1
        return series


async def delete_series(code: int) -> bool:
    """Serialni va uning barcha qismlarini o'chirish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM saved_movies WHERE movie_code = $1;", code)
        await conn.execute("DELETE FROM episodes WHERE series_code = $1;", code)
        res = await conn.execute("DELETE FROM series WHERE code = $1;", code)
        return res.endswith("1")


async def get_all_series() -> List[Dict[str, Any]]:
    """Barcha seriallar ro'yxatini va qismlar sonini olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT s.code, s.title, s.views, s.created_at, COUNT(e.id) as episode_count
            FROM series s
            LEFT JOIN episodes e ON s.code = e.series_code
            GROUP BY s.code, s.title, s.views, s.created_at, s.id
            ORDER BY s.id DESC;
        """)
        return [dict(r) for r in rows]


async def search_series_by_title(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Seriallarni nomi bo'yicha qidirish"""
    pool = await get_pool()
    search_pattern = f"%{query.strip()}%"
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT s.code, s.title, s.views, s.created_at, COUNT(e.id) as episode_count
            FROM series s
            LEFT JOIN episodes e ON s.code = e.series_code
            WHERE s.title ILIKE $1
            GROUP BY s.code, s.title, s.views, s.created_at, s.id
            ORDER BY s.id DESC
            LIMIT $2;
        """, search_pattern, limit)
        return [dict(r) for r in rows]


async def get_series_count() -> int:
    """Seriallar umumiy sonini olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT COUNT(*) FROM series;")
        return val or 0


# ------------------ QISMLAR (EPISODES) ------------------ #

async def get_next_episode_number(series_code: int) -> int:
    """Serial uchun navbatdagi qism raqamini olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        max_ep = await conn.fetchval("""
            SELECT MAX(episode_number) FROM episodes WHERE series_code = $1;
        """, series_code)
        if max_ep is not None:
            return max_ep + 1
        return 1


async def add_episode(series_code: int, episode_number: int, file_id: str, file_type: str = "video", caption: Optional[str] = None) -> bool:
    """Serialga yangi qism qo'shish"""
    try:
        pool = await get_pool()
        ep_json = json.dumps({
            "series_code": series_code,
            "episode_number": episode_number,
            "file_id": file_id,
            "file_type": file_type,
            "caption": caption
        }, ensure_ascii=False)

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO episodes (series_code, episode_number, file_id, file_type, caption, data)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                ON CONFLICT (series_code, episode_number) DO UPDATE SET
                    file_id = EXCLUDED.file_id,
                    file_type = EXCLUDED.file_type,
                    caption = EXCLUDED.caption,
                    data = EXCLUDED.data;
            """, series_code, episode_number, file_id, file_type, caption, ep_json)
            return True
    except Exception as e:
        logger.error(f"Qism qo'shishda xatolik: {e}")
        return False


async def get_episodes_by_series(series_code: int) -> List[Dict[str, Any]]:
    """Serialning barcha qismlarini olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM episodes 
            WHERE series_code = $1 
            ORDER BY episode_number ASC;
        """, series_code)
        return [dict(r) for r in rows]


async def get_episode(series_code: int, episode_number: int, increment_views: bool = True) -> Optional[Dict[str, Any]]:
    """Aniq bir qismni olish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM episodes 
            WHERE series_code = $1 AND episode_number = $2;
        """, series_code, episode_number)
        if not row:
            return None
        ep = dict(row)
        if increment_views:
            await conn.execute("""
                UPDATE episodes SET views = views + 1 
                WHERE series_code = $1 AND episode_number = $2;
            """, series_code, episode_number)
            ep["views"] += 1
        return ep


async def delete_episode(series_code: int, episode_number: int) -> bool:
    """Serialdan bitta qismni o'chirish"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute("""
            DELETE FROM episodes 
            WHERE series_code = $1 AND episode_number = $2;
        """, series_code, episode_number)
        return not res.endswith("0")


async def close_pool() -> None:
    """PostgreSQL ulanish poolini yopish"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None



from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_kb() -> InlineKeyboardMarkup:
    """Start xabari ostidagi tugma"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎬 Barcha Filmlar", url="https://t.me/TopFilmlarUZB1")
            ]
        ]
    )


def get_movie_actions_kb(movie_code: int, bot_username: str, is_saved: bool = False) -> InlineKeyboardMarkup:
    """Kino ostidagi 3 ta tugma: Filmni ulashish, Ko'proq filmlar, Saqlab qo'yish"""
    share_link = f"https://t.me/share/url?url=https://t.me/{bot_username}?start={movie_code}&text={movie_code}-sonli kino TOP FILM botida!"
    save_btn_text = "⭐️ Saqlangan" if is_saved else "💾 Saqlab qo'yish"
    save_callback = f"unsave_{movie_code}" if is_saved else f"save_{movie_code}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="↗️ Filmni ulashish", url=share_link)
            ],
            [
                InlineKeyboardButton(text="🎬 Ko'proq filmlar", url="https://t.me/TopFilmlarUZB1")
            ],
            [
                InlineKeyboardButton(text=save_btn_text, callback_data=save_callback)
            ]
        ]
    )


def get_saved_movies_kb(movies: list) -> InlineKeyboardMarkup:
    """Saqlangan filmlar ro'yxati uchun tugmalar"""
    buttons = []
    for m in movies:
        buttons.append([
            InlineKeyboardButton(
                text=f"🎬 {m['title']} (Kod: {m['code']})",
                callback_data=f"get_movie_{m['code']}"
            ),
            InlineKeyboardButton(
                text="❌",
                callback_data=f"unsave_list_{m['code']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_search_results_kb(movies: list) -> InlineKeyboardMarkup:
    """Qidiruv natijalari uchun tugmalar"""
    buttons = []
    for m in movies:
        buttons.append([
            InlineKeyboardButton(
                text=f"🎬 {m['title']} (Kod: {m['code']})",
                callback_data=f"get_movie_{m['code']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_subscription_kb(channels: list, payload: str = "none") -> InlineKeyboardMarkup:
    """Majburiy obuna kanallari va tekshirish tugmasi"""
    buttons = []
    for idx, ch in enumerate(channels, start=1):
        btn_text = f"➕ {idx}-kanalga a'zo bo'lish"
        buttons.append([
            InlineKeyboardButton(text=btn_text, url=ch["invite_link"])
        ])
    
    # Obunani tekshirish tugmasi
    buttons.append([
        InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data=f"check_sub_{payload}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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
    """Saqlangan filmlar va seriallar ro'yxati uchun tugmalar"""
    buttons = []
    for m in movies:
        is_ser = m.get("item_type") == "series"
        icon = "📺" if is_ser else "🎬"
        cb = f"get_series_{m['code']}" if is_ser else f"get_movie_{m['code']}"
        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {m['title']} (Kod: {m['code']})",
                callback_data=cb
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


def get_episodes_selection_kb(series_code: int, episodes: list, bot_username: str, is_saved: bool = False) -> InlineKeyboardMarkup:
    """Serial qismlarini tanlash tugmalari"""
    buttons = []
    # Qismlarni 3 tadan qilib joylash
    row = []
    for ep in episodes:
        ep_num = ep["episode_number"]
        row.append(InlineKeyboardButton(text=f"🎬 {ep_num}-qism", callback_data=f"get_ep_{series_code}_{ep_num}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Ulashish va Saqlash tugmalari
    share_link = f"https://t.me/share/url?url=https://t.me/{bot_username}?start=series_{series_code}&text={series_code}-sonli serial TOP FILM botida!"
    save_btn_text = "⭐️ Saqlangan" if is_saved else "💾 Saqlab qo'yish"
    save_callback = f"unsave_{series_code}" if is_saved else f"save_{series_code}"

    buttons.append([
        InlineKeyboardButton(text="↗️ Serialni ulashish", url=share_link)
    ])
    buttons.append([
        InlineKeyboardButton(text="🎬 Ko'proq filmlar", url="https://t.me/TopFilmlarUZB1")
    ])
    buttons.append([
        InlineKeyboardButton(text=save_btn_text, callback_data=save_callback)
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_episode_player_kb(series_code: int, episode_number: int, bot_username: str, is_saved: bool = False) -> InlineKeyboardMarkup:
    """Qism ostidagi tugmalar"""
    share_link = f"https://t.me/share/url?url=https://t.me/{bot_username}?start=series_{series_code}&text={series_code}-sonli serialning {episode_number}-qismi TOP FILM botida!"
    save_btn_text = "⭐️ Saqlangan" if is_saved else "💾 Saqlab qo'yish"
    save_callback = f"unsave_{series_code}" if is_saved else f"save_{series_code}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Barcha qismlar", callback_data=f"series_all_{series_code}")
            ],
            [
                InlineKeyboardButton(text="↗️ Qismni ulashish", url=share_link)
            ],
            [
                InlineKeyboardButton(text="🎬 Ko'proq filmlar", url="https://t.me/TopFilmlarUZB1")
            ],
            [
                InlineKeyboardButton(text=save_btn_text, callback_data=save_callback)
            ]
        ]
    )


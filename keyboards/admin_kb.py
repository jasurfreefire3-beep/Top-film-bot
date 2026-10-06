from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_admin_menu() -> InlineKeyboardMarkup:
    """Admin boshqaruv paneli menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎬 Kino qo'shish", callback_data="admin_add_movie"),
                InlineKeyboardButton(text="📺 Seriallar", callback_data="admin_series_menu")
            ],
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
                InlineKeyboardButton(text="📑 Oxirgi kinolar", callback_data="admin_recent_movies")
            ],
            [
                InlineKeyboardButton(text="🗑 Kinoni o'chirish", callback_data="admin_delete_movie"),
                InlineKeyboardButton(text="📢 Majburiy obuna", callback_data="admin_channels")
            ],
            [
                InlineKeyboardButton(text="✉️ Xabar yuborish", callback_data="admin_broadcast")
            ]
        ]
    )


def get_series_admin_menu() -> InlineKeyboardMarkup:
    """Seriallar boshqaruv menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Yangi serial yaratish", callback_data="admin_add_series"),
                InlineKeyboardButton(text="🎬 Qism qo'shish", callback_data="admin_add_episode")
            ],
            [
                InlineKeyboardButton(text="🗑 Qism o'chirish", callback_data="admin_delete_episode"),
                InlineKeyboardButton(text="📑 Seriallar ro'yxati", callback_data="admin_list_series")
            ],
            [
                InlineKeyboardButton(text="❌ Serialni o'chirish", callback_data="admin_delete_series")
            ],
            [
                InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="cancel_action")
            ]
        ]
    )


def get_channels_menu(channels: list) -> InlineKeyboardMarkup:
    """Majburiy obuna kanallari ro'yxati va boshqaruvi"""
    keyboard = []
    for ch in channels:
        keyboard.append([
            InlineKeyboardButton(text=f"📢 {ch['title'][:20]}", url=ch['invite_link']),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_channel_{ch['channel_id']}")
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="➕ Yangi kanal qo'shish", callback_data="admin_add_channel")
    ])
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Admin panelga qaytish", callback_data="cancel_action")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cancel_kb() -> InlineKeyboardMarkup:
    """Jarayonni bekor qilish tugmasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
        ]
    )


def get_code_choice_kb(suggested_code: int) -> InlineKeyboardMarkup:
    """Tavsiya etilgan kodni qabul qilish yoki o'zgartirish tugmasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ Tavsiya etilgan kod ({suggested_code})",
                    callback_data=f"use_code_{suggested_code}"
                )
            ],
            [
                InlineKeyboardButton(text="✍️ O'zim kod yozaman", callback_data="custom_code")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
            ]
        ]
    )


def get_confirm_movie_kb() -> InlineKeyboardMarkup:
    """Kinoni saqlashni tasdiqlash"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💾 Saqlash", callback_data="confirm_save_movie"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
            ]
        ]
    )


def get_broadcast_choice_kb() -> InlineKeyboardMarkup:
    """Xabar uchun tugma qo'shish yoki qo'shmaslik tanlovi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔘 Tugma qo'shish", callback_data="broadcast_add_button")
            ],
            [
                InlineKeyboardButton(text="➡️ Tugmasiz yuborish", callback_data="broadcast_no_button")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
            ]
        ]
    )


def get_broadcast_confirm_kb() -> InlineKeyboardMarkup:
    """Xabarni yuborishni tasdiqlash"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Barchaga yuborish", callback_data="broadcast_confirm_send")
            ],
            [
                InlineKeyboardButton(text="🔄 Tugmani o'zgartirish", callback_data="broadcast_add_button")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
            ]
        ]
    )


def get_button_color_kb() -> InlineKeyboardMarkup:
    """Tugma rangini tanlash menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔴 Qizil", callback_data="btncolor_red"),
                InlineKeyboardButton(text="🔵 Ko'k", callback_data="btncolor_blue")
            ],
            [
                InlineKeyboardButton(text="🟢 Yashil", callback_data="btncolor_green"),
                InlineKeyboardButton(text="⚪️ Klassik (Oddiy)", callback_data="btncolor_classic")
            ],
            [
                InlineKeyboardButton(text="🟡 Sariq", callback_data="btncolor_yellow"),
                InlineKeyboardButton(text="🟣 Binafsha", callback_data="btncolor_purple")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
            ]
        ]
    )


def get_broadcast_preview_kb(has_buttons: bool = True) -> InlineKeyboardMarkup:
    """Preview ko'rinishi ostidagi tugmalar"""
    keyboard = [
        [
            InlineKeyboardButton(text="🚀 Barchaga yuborish", callback_data="broadcast_confirm_send")
        ],
        [
            InlineKeyboardButton(text="➕ Yana tugma qo'shish", callback_data="broadcast_add_button")
        ]
    ]
    if has_buttons:
        keyboard[1].append(InlineKeyboardButton(text="🗑 Tugmalarni tozalash", callback_data="broadcast_clear_buttons"))
    
    keyboard.append([
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def parse_custom_buttons(text: str):
    """
    Admin kiritgan matndan inline tugmalar yasash.
    Qaytaradi: (success: bool, result: InlineKeyboardMarkup yoki xatolik matni, raw_list: list)
    """
    rows = []
    raw_list = []
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    if not lines:
        return False, "Matn bo'sh!", []
    
    for line in lines:
        buttons_in_row = []
        raw_row = []
        # '|' orqali bir qatordagi bir nechta tugmalarni ajratish
        parts = [p.strip() for p in line.split("|") if p.strip()]
        for part in parts:
            if " - " in part:
                btn_text, url = part.split(" - ", 1)
            elif "->" in part:
                btn_text, url = part.split("->", 1)
            elif "=" in part:
                btn_text, url = part.split("=", 1)
            else:
                return False, f"⚠️ Format xato: '<code>{part}</code>'.\nFormat: <code>Tugma matni - https://havola...</code>", []
            
            btn_text = btn_text.strip()
            url = url.strip()
            
            if not (url.startswith("http://") or url.startswith("https://") or url.startswith("tg://")):
                return False, f"⚠️ Havola noto'g'ri (http://, https:// yoki tg:// bilan boshlanishi shart): '<code>{url}</code>'", []
            
            buttons_in_row.append(InlineKeyboardButton(text=btn_text, url=url))
            raw_row.append({"text": btn_text, "url": url})
        
        if buttons_in_row:
            rows.append(buttons_in_row)
            raw_list.append(raw_row)
            
    if not rows:
        return False, "Hech qanday tugma topilmadi!", []
        
    return True, InlineKeyboardMarkup(inline_keyboard=rows), raw_list



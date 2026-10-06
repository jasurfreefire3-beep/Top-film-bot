import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMINS, BOT_USERNAME
from database import (
    get_users_count,
    get_movies_count,
    get_next_movie_code,
    is_movie_code_exists,
    add_movie,
    delete_movie,
    get_recent_movies,
    get_all_user_ids,
    add_channel,
    get_all_channels,
    delete_channel,
    add_series,
    get_series_by_code,
    get_next_series_code,
    is_series_code_exists,
    delete_series,
    get_all_series,
    add_episode,
    get_episodes_by_series,
    get_episode,
    delete_episode,
    get_next_episode_number,
)
from states import (
    AddMovieState,
    DeleteMovieState,
    BroadcastState,
    AddChannelState,
    AddSeriesState,
    AddEpisodeState,
    DeleteEpisodeState,
    DeleteSeriesState,
)
from keyboards.admin_kb import (
    get_admin_menu,
    get_cancel_kb,
    get_code_choice_kb,
    get_channels_menu,
    get_broadcast_choice_kb,
    get_button_color_kb,
    get_broadcast_preview_kb,
    get_series_admin_menu,
    get_admin_series_list_kb,
    get_admin_single_series_kb,
)

admin_router = Router()


def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id in ADMINS


@admin_router.message(Command("admin"))
async def admin_panel_handler(message: Message, state: FSMContext):
    """Admin panelini ochish"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Kechirasiz, bu buyruq faqat bot adminlari uchun mo'ljallangan.")
        return

    await state.clear()
    await message.answer(
        "👋 <b>Admin paneliga xush kelibsiz!</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "cancel_action")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Amalni bekor qilish"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.clear()
    await callback.message.edit_text(
        "❌ Amal bekor qilindi.\n\n"
        "Boshqaruv paneli:",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


# ------------------ KINO QO'SHISH BOSQICHLARI ------------------ #

@admin_router.callback_query(F.data == "admin_add_movie")
async def start_add_movie(callback: CallbackQuery, state: FSMContext):
    """Kino qo'shishni boshlash: video yoki fayl so'rash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.set_state(AddMovieState.waiting_for_video)
    await callback.message.edit_text(
        "🎬 <b>Kino qo'shish bo'limi</b>\n\n"
        "Iltimos, kinoni (video yoki fayl) botga yuboring yoki boshqa kanaldan <b>forward</b> qiling.\n\n"
        "<i>Bekor qilish uchun pastdagi tugmani bosing:</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(AddMovieState.waiting_for_video, F.video)
async def process_movie_video(message: Message, state: FSMContext):
    """Video qabul qilindi"""
    if not is_admin(message.from_user.id):
        return

    file_id = message.video.file_id
    file_type = "video"
    caption = message.caption or ""

    await state.update_data(file_id=file_id, file_type=file_type, initial_caption=caption)
    await state.set_state(AddMovieState.waiting_for_title)

    prompt_text = "✅ <b>Video qabul qilindi!</b>\n\n"
    if caption:
        prompt_text += f"<i>Video izohi: {caption[:100]}</i>\n\n"
    prompt_text += "✍️ <b>Endi ushbu kinoning nomini kiriting:</b>\n<i>(Masalan: Qasoskorlar: Intiho)</i>"

    await message.answer(prompt_text, reply_markup=get_cancel_kb(), parse_mode="HTML")


@admin_router.message(AddMovieState.waiting_for_video, F.document)
async def process_movie_document(message: Message, state: FSMContext):
    """Fayl ko'rinishidagi video qabul qilindi"""
    if not is_admin(message.from_user.id):
        return

    file_id = message.document.file_id
    file_type = "document"
    caption = message.caption or ""

    await state.update_data(file_id=file_id, file_type=file_type, initial_caption=caption)
    await state.set_state(AddMovieState.waiting_for_title)

    await message.answer(
        "✅ <b>Fayl qabul qilindi!</b>\n\n"
        "✍️ <b>Endi ushbu kinoning nomini kiriting:</b>\n"
        "<i>(Masalan: Avatar 2: Suv yo'li)</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(AddMovieState.waiting_for_video)
async def invalid_video_input(message: Message):
    """Video o'rniga boshqa narsa yuborilganda"""
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "⚠️ Iltimos, kino faylini (video yoki hujjat) yuboring yoki forward qiling!",
        reply_markup=get_cancel_kb()
    )


@admin_router.message(AddMovieState.waiting_for_title, F.text)
async def process_movie_title(message: Message, state: FSMContext):
    """Kino nomi kiritildi"""
    if not is_admin(message.from_user.id):
        return

    title = message.text.strip()
    await state.update_data(title=title)

    suggested_code = await get_next_movie_code()

    await message.answer(
        f"🎬 <b>Kino nomi:</b> {title}\n\n"
        f"🔢 <b>Tavsiya etilgan kod:</b> <code>{suggested_code}</code>\n\n"
        f"Ushbu kodni ma'qullaysizmi yoki o'zingiz ixtiyoriy raqamli kod kiritasizmi?",
        reply_markup=get_code_choice_kb(suggested_code),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data.startswith("use_code_"))
async def use_suggested_code(callback: CallbackQuery, state: FSMContext):
    """Tavsiya etilgan kodni saqlash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    code = int(callback.data.split("_")[2])
    data = await state.get_data()
    
    file_id = data.get("file_id")
    file_type = data.get("file_type", "video")
    title = data.get("title")
    caption = data.get("initial_caption", "")

    success = await add_movie(
        code=code,
        title=title,
        file_id=file_id,
        file_type=file_type,
        caption=caption
    )

    if success:
        deep_link = f"https://t.me/{BOT_USERNAME}?start={code}"
        post_template = (
            f"🎬 <b>Film:</b> {title}\n"
            f"🔢 <b>Kino kodi:</b> <code>{code}</code>\n"
            f"📥 <b>Botdan yuklab olish:</b>\n{deep_link}"
        )
        await callback.message.edit_text(
            f"🎉 <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
            f"🎬 <b>Nomi:</b> {title}\n"
            f"🔢 <b>Kodi:</b> <code>{code}</code>\n"
            f"🔗 <b>Auto havola:</b> <code>{deep_link}</code>\n\n"
            f"📋 <b>Kanal uchun tayyor post:</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{post_template}\n"
            f"━━━━━━━━━━━━━━━━━━",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "❌ Xatolik yuz berdi. Ushbu kodli kino bazada mavjud bo'lishi mumkin.",
            reply_markup=get_admin_menu()
        )

    await state.clear()
    await callback.answer()


@admin_router.callback_query(F.data == "custom_code")
async def ask_custom_code(callback: CallbackQuery, state: FSMContext):
    """Qo'lda boshqa kod yozishni so'rash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.set_state(AddMovieState.waiting_for_code)
    await callback.message.edit_text(
        "✍️ <b>Kino uchun noyob raqamli kod kiriting:</b>\n"
        "<i>(Masalan: 105, 777 va h.k.)</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(AddMovieState.waiting_for_code, F.text)
async def process_custom_code(message: Message, state: FSMContext):
    """Qo'lda kiritilgan kodni qabul qilish va saqlash"""
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        return await message.answer(
            "⚠️ Kod faqat butun musbat raqamlardan iborat bo'lishi kerak!\nQaytadan kiriting:",
            reply_markup=get_cancel_kb()
        )

    code = int(text)
    if await is_movie_code_exists(code):
        return await message.answer(
            f"⚠️ <b>{code}</b> kodi allaqachon mavjud! Boshqa raqam kiriting:",
            reply_markup=get_cancel_kb(),
            parse_mode="HTML"
        )

    data = await state.get_data()
    file_id = data.get("file_id")
    file_type = data.get("file_type", "video")
    title = data.get("title")
    caption = data.get("initial_caption", "")

    success = await add_movie(
        code=code,
        title=title,
        file_id=file_id,
        file_type=file_type,
        caption=caption
    )

    if success:
        deep_link = f"https://t.me/{BOT_USERNAME}?start={code}"
        post_template = (
            f"🎬 <b>Film:</b> {title}\n"
            f"🔢 <b>Kino kodi:</b> <code>{code}</code>\n"
            f"📥 <b>Botdan yuklab olish:</b>\n{deep_link}"
        )
        await message.answer(
            f"🎉 <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
            f"🎬 <b>Nomi:</b> {title}\n"
            f"🔢 <b>Kodi:</b> <code>{code}</code>\n"
            f"🔗 <b>Auto havola:</b> <code>{deep_link}</code>\n\n"
            f"📋 <b>Kanal uchun tayyor post:</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{post_template}\n"
            f"━━━━━━━━━━━━━━━━━━",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Xatolik yuz berdi. Kino saqlanmadi.",
            reply_markup=get_admin_menu()
        )

    await state.clear()


# ------------------ STATISTIKA ------------------ #

@admin_router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    """Bot statistikasini ko'rsatish"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    users_count = await get_users_count()
    movies_count = await get_movies_count()

    text = (
        "📊 <b>Bot statistikasi:</b>\n\n"
        f"👥 Foydalanuvchilar soni: <b>{users_count}</b> ta\n"
        f"🎬 Bazadagi kinolar soni: <b>{movies_count}</b> ta\n\n"
        "⚡️ Bot sozlamalari va server barqaror ishlamoqda."
    )

    await callback.message.edit_text(text, reply_markup=get_admin_menu(), parse_mode="HTML")
    await callback.answer()


# ------------------ OXIRGI KINOLAR ------------------ #

@admin_router.callback_query(F.data == "admin_recent_movies")
async def show_recent_movies(callback: CallbackQuery):
    """Oxirgi 10 ta kinoni ko'rsatish"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    movies = await get_recent_movies(limit=10)
    if not movies:
        await callback.message.edit_text(
            "📑 Bazada hozircha hech qanday kino mavjud emas.",
            reply_markup=get_admin_menu()
        )
        return await callback.answer()

    text = "📑 <b>Oxirgi qo'shilgan 10 ta kino:</b>\n\n"
    for idx, m in enumerate(movies, start=1):
        text += f"{idx}. <b>{m['title']}</b>\n   🔢 Kod: <code>{m['code']}</code> | 👁 Ko'rishlar: {m['views']}\n\n"

    await callback.message.edit_text(text, reply_markup=get_admin_menu(), parse_mode="HTML")
    await callback.answer()


# ------------------ KINONI O'CHIRISH ------------------ #

@admin_router.callback_query(F.data == "admin_delete_movie")
async def start_delete_movie(callback: CallbackQuery, state: FSMContext):
    """Kino o'chirishni boshlash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.set_state(DeleteMovieState.waiting_for_code)
    await callback.message.edit_text(
        "🗑 <b>Kinoni o'chirish</b>\n\n"
        "O'chirmoqchi bo'lgan kino kodini kiriting:",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(DeleteMovieState.waiting_for_code, F.text)
async def process_delete_movie(message: Message, state: FSMContext):
    """Kino kodini qabul qilib bazadan o'chirish"""
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        return await message.answer(
            "⚠️ Kod raqam bo'lishi kerak! Qaytadan kiriting:",
            reply_markup=get_cancel_kb()
        )

    code = int(text)
    deleted = await delete_movie(code)

    if deleted:
        await message.answer(
            f"✅ Kod: <b>{code}</b> bo'lgan kino muvaffaqiyatli o'chirildi!",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ Kod: <b>{code}</b> bo'lgan kino topilmadi.",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )

    await state.clear()


# ------------------ XABAR TARQATISH (BROADCAST) ------------------ #

# ------------------ XABAR TARQATISH (BROADCAST) ------------------ #

@admin_router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Barcha foydalanuvchilarga xabar yuborishni boshlash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.set_state(BroadcastState.waiting_for_message)
    await callback.message.edit_text(
        "📢 <b>Xabar tarqatish bo'limi</b>\n\n"
        "Barcha bot foydalanuvchilariga yuboriladigan xabarni (matn, rasm, video va h.k.) yuboring:",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(BroadcastState.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """1. Xabarni qabul qilish va tugma qo'shishni so'rash"""
    if not is_admin(message.from_user.id):
        return

    # Xabar ma'lumotlarini saqlash
    await state.update_data(
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        custom_buttons=[]
    )

    await message.answer(
        "✅ <b>Xabar qabul qilindi!</b>\n\n"
        "Ushbu xabar tagiga tugma (havola/link) qo'shishni xohlaysizmi?",
        reply_markup=get_broadcast_choice_kb(),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "broadcast_add_button")
async def ask_broadcast_button_color(callback: CallbackQuery, state: FSMContext):
    """2. Tugma rangini tanlashni so'rash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.set_state(BroadcastState.choosing_button_color)
    text = (
        "🎨 <b>Tugma rangini tanlang:</b>\n\n"
        "Quyidagi ranglardan birini tanlang:\n"
        "• 🔴 <b>Qizil</b>\n"
        "• 🔵 <b>Ko'k</b>\n"
        "• 🟢 <b>Yashil</b>\n"
        "• ⚪️ <b>Klassik</b> (oddiy standart tugma)\n"
        "• 🟡 <b>Sariq</b> yoki 🟣 <b>Binafsha</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_button_color_kb(), parse_mode="HTML")
    await callback.answer()


@admin_router.callback_query(F.data.startswith("btncolor_"))
async def process_button_color(callback: CallbackQuery, state: FSMContext):
    """3. Rang tanlangach, ustiga yoziladigan matnni so'rash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    color_key = callback.data.replace("btncolor_", "")
    await state.update_data(current_btn_color=color_key)
    await state.set_state(BroadcastState.waiting_for_button_text)

    color_names = {
        "red": "🔴 Qizil",
        "blue": "🔵 Ko'k",
        "green": "🟢 Yashil",
        "classic": "⚪️ Klassik",
        "yellow": "🟡 Sariq",
        "purple": "🟣 Binafsha"
    }
    selected_name = color_names.get(color_key, "⚪️ Klassik")

    await callback.message.edit_text(
        f"🎨 Tanlangan rang: <b>{selected_name}</b>\n\n"
        "✍️ <b>Endi ushbu tugma ustiga yoziladigan matnni kiriting:</b>\n"
        "<i>(Masalan: 🎬 Kinoni tomosha qilish)</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(BroadcastState.waiting_for_button_text, F.text)
async def process_button_text(message: Message, state: FSMContext):
    """4. Matn kiritilgach, unga ulanadigan havolani so'rash"""
    if not is_admin(message.from_user.id):
        return

    btn_text = message.text.strip()
    await state.update_data(current_btn_text=btn_text)
    await state.set_state(BroadcastState.waiting_for_button_url)

    await message.answer(
        f"✍️ Tugma matni: <b>{btn_text}</b>\n\n"
        "🔗 <b>Endi ushbu tugma bosilganda ochiladigan havolani (link) kiriting:</b>\n"
        "<i>(Masalan: https://t.me/TopFilmlarUZB1)</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(BroadcastState.waiting_for_button_url, F.text)
async def process_button_url(message: Message, state: FSMContext):
    """5. Havola kiritilgach, tugmani yaratish va Preview ko'rsatish"""
    if not is_admin(message.from_user.id):
        return

    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("tg://")):
        return await message.answer(
            "⚠️ Havola noto'g'ri! Havola <code>https://...</code> yoki <code>tg://...</code> ko'rinishida bo'lishi shart.\n\n"
            "Qaytadan kiriting:",
            reply_markup=get_cancel_kb(),
            parse_mode="HTML"
        )

    data = await state.get_data()
    color_key = data.get("current_btn_color", "classic")
    raw_text = data.get("current_btn_text", "Havola")

    color_prefixes = {
        "red": "🔴 ",
        "blue": "🔵 ",
        "green": "🟢 ",
        "classic": "",
        "yellow": "🟡 ",
        "purple": "🟣 "
    }
    prefix = color_prefixes.get(color_key, "")
    final_text = f"{prefix}{raw_text}"

    custom_buttons = data.get("custom_buttons", [])
    custom_buttons.append({"text": final_text, "url": url})
    await state.update_data(custom_buttons=custom_buttons)

    # Preview markup yasash
    markup_rows = [[InlineKeyboardButton(text=btn["text"], url=btn["url"])] for btn in custom_buttons]
    preview_kb = InlineKeyboardMarkup(inline_keyboard=markup_rows)

    await message.answer("👁 <b>XABARNING KO'RINIShI (PREVIEW):</b>", parse_mode="HTML")
    try:
        await message.bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=data["from_chat_id"],
            message_id=data["message_id"],
            reply_markup=preview_kb
        )
    except Exception as e:
        return await message.answer(
            f"❌ Xatolik yuz berdi: {e}",
            reply_markup=get_cancel_kb()
        )

    await message.answer(
        f"✅ <b>Tugma muvaffaqiyatli qo'shildi!</b> (Jami tugmalar: {len(custom_buttons)} ta)\n\n"
        "Xabarni hoziroq tarqatishingiz yoki yana tugma qo'shishingiz mumkin:",
        reply_markup=get_broadcast_preview_kb(has_buttons=True),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "broadcast_clear_buttons")
async def clear_broadcast_buttons(callback: CallbackQuery, state: FSMContext):
    """Barcha tugmalarni tozalash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.update_data(custom_buttons=[])
    await callback.answer("🗑 Barcha tugmalar tozalandi!", show_alert=True)
    await callback.message.edit_text(
        "🗑 Tugmalar tozalandi.\n\nEndi nima qilmoqchisiz?",
        reply_markup=get_broadcast_choice_kb(),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "broadcast_no_button")
async def process_broadcast_no_buttons(callback: CallbackQuery, state: FSMContext):
    """Tugmasiz yuborish preview-si"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.update_data(custom_buttons=[])
    data = await state.get_data()

    await callback.message.answer("👁 <b>XABARNING KO'RINIShI (PREVIEW):</b>", parse_mode="HTML")
    try:
        await callback.bot.copy_message(
            chat_id=callback.message.chat.id,
            from_chat_id=data["from_chat_id"],
            message_id=data["message_id"]
        )
    except Exception as e:
        return await callback.message.answer(
            f"❌ Xatolik: {e}",
            reply_markup=get_cancel_kb()
        )

    await callback.message.answer(
        "👆 <b>Xabaringiz yuqoridagi ko'rinishda (tugmasiz) barcha foydalanuvchilarga yuboriladi.</b>\n\n"
        "Yuborishni tasdiqlaysizmi?",
        reply_markup=get_broadcast_preview_kb(has_buttons=False),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data == "broadcast_confirm_send")
async def send_broadcast_to_all(callback: CallbackQuery, state: FSMContext):
    """Xabarni barcha foydalanuvchilarga yuborish"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    data = await state.get_data()
    from_chat_id = data.get("from_chat_id")
    message_id = data.get("message_id")
    custom_buttons = data.get("custom_buttons", [])

    reply_markup = None
    if custom_buttons:
        rows = [[InlineKeyboardButton(text=btn["text"], url=btn["url"])] for btn in custom_buttons]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=rows)

    user_ids = await get_all_user_ids()
    if not user_ids:
        await callback.message.edit_text("Bazada hech qanday foydalanuvchi yo'q.", reply_markup=get_admin_menu())
        await state.clear()
        return

    status_msg = await callback.message.edit_text(f"⏳ Xabar yuborilmoqda: 0/{len(user_ids)}...")

    sent_count = 0
    blocked_count = 0

    for idx, u_id in enumerate(user_ids, start=1):
        try:
            await callback.bot.copy_message(
                chat_id=u_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
                reply_markup=reply_markup
            )
            sent_count += 1
        except Exception:
            blocked_count += 1

        if idx % 20 == 0:
            try:
                await status_msg.edit_text(f"⏳ Xabar yuborilmoqda: {idx}/{len(user_ids)}...")
            except Exception:
                pass
        await asyncio.sleep(0.05)

    try:
        await status_msg.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"📢 <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"✅ Muvaffaqiyatli yetkazildi: <b>{sent_count}</b> ta\n"
        f"🚫 Bloklagan/Yetib bormagan: <b>{blocked_count}</b> ta",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )
    await state.clear()


# ------------------ MAJBURIY OBUNA BOSHQARUVI ------------------ #

@admin_router.callback_query(F.data == "admin_channels")
async def show_channels_management(callback: CallbackQuery, state: FSMContext):
    """Majburiy obuna kanallari ro'yxatini ko'rsatish"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.clear()
    channels = await get_all_channels()

    text = (
        "📢 <b>Majburiy obuna kanallari bo'limi</b>\n\n"
        f"Ayni vaqtda faol kanallar: <b>{len(channels)}</b> ta.\n\n"
        "Foydalanuvchilar kinoni yuklab olishdan oldin ushbu kanallarga a'zo bo'lishlari so'raladi.\n"
        "<i>Eslatma: Bot ushbu kanallarda <b>ADMIN</b> bo'lishi shart!</i>"
    )

    await callback.message.edit_text(text, reply_markup=get_channels_menu(channels), parse_mode="HTML")
    await callback.answer()


@admin_router.callback_query(F.data.startswith("del_channel_"))
async def delete_channel_handler(callback: CallbackQuery):
    """Kanalni majburiy obunadan o'chirish"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    channel_id = callback.data.replace("del_channel_", "")
    await delete_channel(channel_id)
    await callback.answer("✅ Kanal o'chirildi!", show_alert=True)

    channels = await get_all_channels()
    text = (
        "📢 <b>Majburiy obuna kanallari bo'limi</b>\n\n"
        f"Ayni vaqtda faol kanallar: <b>{len(channels)}</b> ta.\n\n"
        "<i>Kanal muvaffaqiyatli o'chirildi.</i>"
    )
    await callback.message.edit_text(text, reply_markup=get_channels_menu(channels), parse_mode="HTML")


@admin_router.callback_query(F.data == "admin_add_channel")
async def start_add_channel(callback: CallbackQuery, state: FSMContext):
    """Yangi kanal qo'shishni boshlash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.set_state(AddChannelState.waiting_for_channel)
    text = (
        "📢 <b>Kanal qo'shish:</b>\n\n"
        "1. Avval botni kanalingizga <b>ADMIN</b> qiling;\n"
        "2. Kanaldan biron xabarni bu yerga <b>FORWARD</b> qiling\n"
        "yoki kanal username-ini yuboring (Masalan: <code>@mening_kanalim</code>)\n"
        "yoki kanal ID raqamini kiriting (Masalan: <code>-1001234567890</code>)."
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_kb(), parse_mode="HTML")
    await callback.answer()


@admin_router.message(AddChannelState.waiting_for_channel)
async def process_channel_input(message: Message, state: FSMContext):
    """Kanal ma'lumotlarini qabul qilish va tekshirish"""
    if not is_admin(message.from_user.id):
        return

    chat_id = None
    title = None
    invite_link = None

    # 1. Agar kanaldan post forward qilingan bo'lsa
    if message.forward_from_chat:
        chat = message.forward_from_chat
        chat_id = chat.id
        title = chat.title
        if chat.username:
            invite_link = f"https://t.me/{chat.username}"
    # 2. Agar matn (username yoki raqamli ID) yozilgan bo'lsa
    elif message.text:
        text = message.text.strip()
        chat_id = int(text) if (text.startswith("-") or text.isdigit()) else text

    if not chat_id:
        return await message.answer(
            "⚠️ Kanal aniqlanmadi. Iltimos, kanaldan post forward qiling yoki username/ID yuboring:",
            reply_markup=get_cancel_kb()
        )

    # Bot kanalga kira olishini va adminligini tekshirish
    try:
        chat = await message.bot.get_chat(chat_id)
        title = chat.title or str(chat_id)
        
        # Bot adminligini tekshirish
        bot_member = await message.bot.get_chat_member(chat_id=chat.id, user_id=message.bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            return await message.answer(
                f"⚠️ Bot <b>{title}</b> kanalida ADMIN emas!\n"
                "Iltimos, avval botni kanalga admin qiling va qaytadan yuboring.",
                reply_markup=get_cancel_kb(),
                parse_mode="HTML"
            )

        if chat.username:
            invite_link = f"https://t.me/{chat.username}"
        elif not invite_link:
            try:
                # Agar havola bo'lmasa, yangi taklif havolasi yaratish
                link_obj = await message.bot.create_chat_invite_link(chat_id=chat.id)
                invite_link = link_obj.invite_link
            except Exception:
                pass

        if not invite_link:
            # Havolani qo'lda so'rash
            await state.update_data(channel_id=str(chat.id), title=title)
            await state.set_state(AddChannelState.waiting_for_invite_link)
            return await message.answer(
                f"✅ Kanal topildi: <b>{title}</b>\n\n"
                "Bu kanal yopiq (private) bo'lganligi sababli, iltimos, kanalning <b>taklif havolasini (invite link)</b> yuboring:",
                reply_markup=get_cancel_kb(),
                parse_mode="HTML"
            )

        # Kanali saqlash
        success = await add_channel(str(chat.id), title, invite_link)
        if success:
            channels = await get_all_channels()
            await message.answer(
                f"🎉 <b>Kanal muvaffaqiyatli qo'shildi!</b>\n\n"
                f"📢 <b>Nomi:</b> {title}\n"
                f"🔗 <b>Havola:</b> {invite_link}",
                reply_markup=get_channels_menu(channels),
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Kanalni saqlashda xatolik yuz berdi.", reply_markup=get_admin_menu())

        await state.clear()

    except Exception as e:
        await message.answer(
            f"❌ Xatolik yuz berdi: {e}\n\n"
            "Iltimos, bot kanalda ADMIN ekanligini va username/ID to'g'riligini tekshiring.",
            reply_markup=get_cancel_kb()
        )


@admin_router.message(AddChannelState.waiting_for_invite_link, F.text)
async def process_invite_link(message: Message, state: FSMContext):
    """Yopiq kanal uchun havola kiritilganda saqlash"""
    if not is_admin(message.from_user.id):
        return

    link = message.text.strip()
    if not (link.startswith("https://t.me/") or link.startswith("http://t.me/")):
        return await message.answer(
            "⚠️ Noto'g'ri havola! Havola <code>https://t.me/...</code> ko'rinishida bo'lishi kerak.\nQaytadan kiriting:",
            reply_markup=get_cancel_kb(),
            parse_mode="HTML"
        )

    data = await state.get_data()
    channel_id = data.get("channel_id")
    title = data.get("title")

    success = await add_channel(channel_id, title, link)
    if success:
        channels = await get_all_channels()
        await message.answer(
            f"🎉 <b>Kanal muvaffaqiyatli qo'shildi!</b>\n\n"
            f"📢 <b>Nomi:</b> {title}\n"
            f"🔗 <b>Havola:</b> {link}",
            reply_markup=get_channels_menu(channels),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Kanalni saqlashda xatolik yuz berdi.", reply_markup=get_admin_menu())

    await state.clear()


# ------------------ SERIALLAR VA QISMLAR BOSHQARUVI ------------------ #

@admin_router.callback_query(F.data == "admin_series_menu")
async def show_series_menu(callback: CallbackQuery, state: FSMContext):
    """Seriallar boshqaruv menyusini ko'rsatish"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.clear()
    series_cnt = await get_series_count()
    await callback.message.edit_text(
        "📺 <b>Seriallar boshqaruvi bo'limi:</b>\n\n"
        f"Ayni vaqtda bazada: <b>{series_cnt}</b> ta serial mavjud.\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=get_series_admin_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin_add_series")
async def start_add_series(callback: CallbackQuery, state: FSMContext):
    """Yangi serial yaratishni boshlash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.set_state(AddSeriesState.waiting_for_title)
    await callback.message.edit_text(
        "📺 <b>Yangi serial yaratish:</b>\n\n"
        "Serial nomini kiriting:\n<i>(Masalan: Kurtlar Vadisi)</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(AddSeriesState.waiting_for_title, F.text)
async def process_series_title(message: Message, state: FSMContext):
    """Serial nomini qabul qilish va kodni taklif etish"""
    if not is_admin(message.from_user.id):
        return

    title = message.text.strip()
    await state.update_data(series_title=title)

    suggested_code = await get_next_series_code()

    # Kod tanlash tugmalari
    code_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ Tavsiya etilgan kod ({suggested_code})",
                    callback_data=f"use_series_code_{suggested_code}"
                )
            ],
            [
                InlineKeyboardButton(text="✍️ O'zim kod yozaman", callback_data="custom_series_code")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
            ]
        ]
    )

    await message.answer(
        f"📺 <b>Serial nomi:</b> {title}\n\n"
        f"🔢 <b>Tavsiya etilgan kod:</b> <code>{suggested_code}</code>\n\n"
        f"Ushbu kodni ma'qullaysizmi yoki boshqa kod kiritasizmi?",
        reply_markup=code_kb,
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data.startswith("use_series_code_"))
async def use_suggested_series_code(callback: CallbackQuery, state: FSMContext):
    """Tavsiya etilgan kod bilan serialni yaratish"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    code = int(callback.data.split("_")[3])
    data = await state.get_data()
    title = data.get("series_title")

    success = await add_series(code=code, title=title)
    if success:
        deep_link = f"https://t.me/{BOT_USERNAME}?start=series_{code}"
        post_template = (
            f"📺 <b>Serial:</b> {title}\n"
            f"🔢 <b>Serial kodi:</b> <code>{code}</code>\n"
            f"📥 <b>Barcha qismlarni ko'rish:</b>\n{deep_link}"
        )
        await callback.message.edit_text(
            f"🎉 <b>Serial muvaffaqiyatli yaratildi!</b>\n\n"
            f"📺 <b>Nomi:</b> {title}\n"
            f"🔢 <b>Kodi:</b> <code>{code}</code>\n"
            f"🔗 <b>Auto havola:</b> <code>{deep_link}</code>\n\n"
            f"📋 <b>Kanal uchun tayyor post:</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{post_template}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"<i>Endi ushbu serialga «🎬 Qism qo'shish» tugmasi orqali qismlarni yuklashingiz mumkin.</i>",
            reply_markup=get_series_admin_menu(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Serialni yaratishda xatolik yuz berdi.", reply_markup=get_series_admin_menu())

    await state.clear()
    await callback.answer()


@admin_router.callback_query(F.data == "custom_series_code")
async def ask_custom_series_code(callback: CallbackQuery, state: FSMContext):
    """Qo'lda serial kodi kiritishni so'rash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.set_state(AddSeriesState.waiting_for_code)
    await callback.message.edit_text(
        "✍️ <b>Serial uchun noyob raqamli kod kiriting:</b>\n<i>(Masalan: 50, 100 va h.k.)</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(AddSeriesState.waiting_for_code, F.text)
async def process_custom_series_code(message: Message, state: FSMContext):
    """Qo'lda kiritilgan kod bilan serialni yaratish"""
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        return await message.answer("⚠️ Kod raqam bo'lishi kerak! Qayta kiriting:", reply_markup=get_cancel_kb())

    code = int(text)
    if await is_series_code_exists(code) or await is_movie_code_exists(code):
        return await message.answer(f"⚠️ <b>{code}</b> kodi allaqachon mavjud! Boshqa kod kiriting:", reply_markup=get_cancel_kb(), parse_mode="HTML")

    data = await state.get_data()
    title = data.get("series_title")

    success = await add_series(code=code, title=title)
    if success:
        deep_link = f"https://t.me/{BOT_USERNAME}?start=series_{code}"
        post_template = (
            f"📺 <b>Serial:</b> {title}\n"
            f"🔢 <b>Serial kodi:</b> <code>{code}</code>\n"
            f"📥 <b>Barcha qismlarni ko'rish:</b>\n{deep_link}"
        )
        await message.answer(
            f"🎉 <b>Serial muvaffaqiyatli yaratildi!</b>\n\n"
            f"📺 <b>Nomi:</b> {title}\n"
            f"🔢 <b>Kodi:</b> <code>{code}</code>\n"
            f"🔗 <b>Auto havola:</b> <code>{deep_link}</code>\n\n"
            f"📋 <b>Kanal uchun tayyor post:</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{post_template}\n"
            f"━━━━━━━━━━━━━━━━━━",
            reply_markup=get_series_admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Serialni yaratishda xatolik yuz berdi.", reply_markup=get_series_admin_menu())

    await state.clear()


# ------------------ QISM QO'SHISH ------------------ #

@admin_router.callback_query(F.data == "admin_add_episode")
async def start_add_episode(callback: CallbackQuery, state: FSMContext):
    """Serialga qism qo'shishni boshlash: serial kodini so'rash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.set_state(AddEpisodeState.waiting_for_series_code)
    await callback.message.edit_text(
        "🎬 <b>Serialga qism qo'shish:</b>\n\n"
        "Qaysi serialga qism qo'shmoqchisiz? Serial kodini kiriting:\n<i>(Masalan: 1)</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(AddEpisodeState.waiting_for_series_code, F.text)
async def process_episode_series_code(message: Message, state: FSMContext):
    """Serial kodi kiritilganda tekshirish va qism raqamini so'rash"""
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        return await message.answer("⚠️ Serial kodi raqam bo'lishi kerak! Qayta kiriting:", reply_markup=get_cancel_kb())

    series_code = int(text)
    series = await get_series_by_code(series_code, increment_views=False)
    if not series:
        return await message.answer(f"❌ <b>{series_code}</b>-kodli serial topilmadi. Qaytadan kiriting:", reply_markup=get_cancel_kb(), parse_mode="HTML")

    next_ep = await get_next_episode_number(series_code)
    await state.update_data(series_code=series_code, series_title=series["title"])
    await state.set_state(AddEpisodeState.waiting_for_episode_number)

    await message.answer(
        f"📺 Serial: <b>{series['title']}</b> (Kod: <code>{series_code}</code>)\n\n"
        f"🔢 <b>Qism raqamini kiriting:</b>\n"
        f"<i>(Tavsiya etiladi: <b>{next_ep}</b>)</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(AddEpisodeState.waiting_for_episode_number, F.text)
async def process_episode_number(message: Message, state: FSMContext):
    """Qism raqamini qabul qilish va video so'rash"""
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        return await message.answer("⚠️ Qism raqami musbat butun son bo'lishi kerak! Qayta kiriting:", reply_markup=get_cancel_kb())

    ep_num = int(text)
    await state.update_data(episode_number=ep_num)
    await state.set_state(AddEpisodeState.waiting_for_video)

    data = await state.get_data()
    await message.answer(
        f"📺 <b>{data['series_title']}</b> — <b>{ep_num}-qism</b>\n\n"
        "📹 <b>Endi ushbu qism videosini yuboring yoki boshqa kanaldan FORWARD qiling:</b>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(AddEpisodeState.waiting_for_video, F.video)
async def process_episode_video(message: Message, state: FSMContext):
    """Qism videosini saqlash"""
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    series_code = data["series_code"]
    series_title = data["series_title"]
    episode_number = data["episode_number"]
    file_id = message.video.file_id
    caption = message.caption or ""

    success = await add_episode(
        series_code=series_code,
        episode_number=episode_number,
        file_id=file_id,
        file_type="video",
        caption=caption
    )

    if success:
        await message.answer(
            f"🎉 <b>Qism muvaffaqiyatli saqlandi!</b>\n\n"
            f"📺 Serial: <b>{series_title}</b>\n"
            f"🎬 Qism: <b>{episode_number}-qism</b>\n"
            f"🔢 Serial kodi: <code>{series_code}</code>\n\n"
            f"<i>Foydalanuvchilar botga <code>{series_code}</code> yozib barcha qismlarni ko'rishlari mumkin.</i>",
            reply_markup=get_series_admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Qismni saqlashda xatolik yuz berdi.", reply_markup=get_series_admin_menu())

    await state.clear()


@admin_router.message(AddEpisodeState.waiting_for_video, F.document)
async def process_episode_document(message: Message, state: FSMContext):
    """Qism faylini (hujjatini) saqlash"""
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    series_code = data["series_code"]
    series_title = data["series_title"]
    episode_number = data["episode_number"]
    file_id = message.document.file_id
    caption = message.caption or ""

    success = await add_episode(
        series_code=series_code,
        episode_number=episode_number,
        file_id=file_id,
        file_type="document",
        caption=caption
    )

    if success:
        await message.answer(
            f"🎉 <b>Qism muvaffaqiyatli saqlandi!</b>\n\n"
            f"📺 Serial: <b>{series_title}</b>\n"
            f"🎬 Qism: <b>{episode_number}-qism</b>\n"
            f"🔢 Serial kodi: <code>{series_code}</code>",
            reply_markup=get_series_admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Qismni saqlashda xatolik yuz berdi.", reply_markup=get_series_admin_menu())

    await state.clear()


# ------------------ QISM O'CHIRISH ------------------ #

@admin_router.callback_query(F.data == "admin_delete_episode")
async def start_delete_episode(callback: CallbackQuery, state: FSMContext):
    """Qism o'chirishni boshlash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.set_state(DeleteEpisodeState.waiting_for_series_code)
    await callback.message.edit_text(
        "🗑 <b>Serialdan qism o'chirish:</b>\n\n"
        "Serial kodini kiriting:\n<i>(Masalan: 1)</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(DeleteEpisodeState.waiting_for_series_code, F.text)
async def process_delete_episode_series(message: Message, state: FSMContext):
    """Qism o'chirish uchun serial kodini qabul qilish"""
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        return await message.answer("⚠️ Serial kodi raqam bo'lishi kerak! Qayta kiriting:", reply_markup=get_cancel_kb())

    series_code = int(text)
    series = await get_series_by_code(series_code, increment_views=False)
    if not series:
        return await message.answer(f"❌ <b>{series_code}</b>-kodli serial topilmadi.", reply_markup=get_cancel_kb(), parse_mode="HTML")

    episodes = await get_episodes_by_series(series_code)
    if not episodes:
        await state.clear()
        return await message.answer(f"⚠️ <b>{series['title']}</b> serialida hali hech qanday qism yo'q.", reply_markup=get_series_admin_menu(), parse_mode="HTML")

    ep_list = ", ".join([str(e["episode_number"]) for e in episodes])
    await state.update_data(series_code=series_code)
    await state.set_state(DeleteEpisodeState.waiting_for_episode_number)

    await message.answer(
        f"📺 Serial: <b>{series['title']}</b>\n"
        f"Mavjud qismlar: <b>{ep_list}</b>\n\n"
        "🗑 <b>O'chirmoqchi bo'lgan qism raqamini kiriting:</b>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(DeleteEpisodeState.waiting_for_episode_number, F.text)
async def process_delete_episode_num(message: Message, state: FSMContext):
    """Qismni o'chirish"""
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        return await message.answer("⚠️ Qism raqam bo'lishi kerak! Qayta kiriting:", reply_markup=get_cancel_kb())

    ep_num = int(text)
    data = await state.get_data()
    series_code = data["series_code"]

    deleted = await delete_episode(series_code, ep_num)
    if deleted:
        await message.answer(
            f"✅ <b>{series_code}</b>-kodli serialdan <b>{ep_num}-qism</b> muvaffaqiyatli o'chirildi!",
            reply_markup=get_series_admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ <b>{ep_num}-qism</b> topilmadi yoki allaqachon o'chirilgan.",
            reply_markup=get_series_admin_menu(),
            parse_mode="HTML"
        )

    await state.clear()


# ------------------ SERIALNI O'CHIRISH ------------------ #

@admin_router.callback_query(F.data == "admin_delete_series")
async def start_delete_series(callback: CallbackQuery, state: FSMContext):
    """Serialni o'chirishni boshlash"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    await state.set_state(DeleteSeriesState.waiting_for_series_code)
    await callback.message.edit_text(
        "❌ <b>Serialni o'chirish:</b>\n\n"
        "O'chirmoqchi bo'lgan serial kodini kiriting:\n<i>(Masalan: 1)</i>\n\n"
        "⚠️ <i>Diqqat: Serial o'chirilsa, uning barcha qismlari ham o'chiriladi!</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(DeleteSeriesState.waiting_for_series_code, F.text)
async def process_delete_series(message: Message, state: FSMContext):
    """Serialni o'chirish"""
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        return await message.answer("⚠️ Serial kodi raqam bo'lishi kerak! Qayta kiriting:", reply_markup=get_cancel_kb())

    code = int(text)
    deleted = await delete_series(code)
    if deleted:
        await message.answer(
            f"✅ Kod: <b>{code}</b> bo'lgan serial va uning barcha qismlari o'chirildi!",
            reply_markup=get_series_admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ Kod: <b>{code}</b> bo'lgan serial topilmadi.",
            reply_markup=get_series_admin_menu(),
            parse_mode="HTML"
        )

    await state.clear()


# ------------------ SERIALLAR RO'YXATI ------------------ #

@admin_router.callback_query(F.data == "admin_list_series")
async def show_all_series_admin(callback: CallbackQuery):
    """Barcha seriallar ro'yxatini ko'rsatish (har biri bosiladigan tugma bilan)"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    series_list = await get_all_series()
    if not series_list:
        await callback.message.edit_text("📑 Bazada hozircha seriallar mavjud emas.", reply_markup=get_series_admin_menu())
        return await callback.answer()

    text = (
        "📑 <b>Mavjud seriallar ro'yxati:</b>\n\n"
        "<i>Boshqarish, qism qo'shish yoki o'chirish uchun kerakli serial tugmasini bosing:</i>"
    )

    await callback.message.edit_text(text, reply_markup=get_admin_series_list_kb(series_list), parse_mode="HTML")
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_view_series_"))
async def admin_view_single_series(callback: CallbackQuery):
    """Bitta serialni ko'rish va boshqarish sahifasi"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    series_code = int(callback.data.replace("admin_view_series_", ""))
    series = await get_series_by_code(series_code, increment_views=False)
    if not series:
        return await callback.answer("Serial topilmadi!", show_alert=True)

    episodes = await get_episodes_by_series(series_code)
    ep_list_str = ", ".join([str(e["episode_number"]) for e in episodes]) if episodes else "Hali qismlar yo'q"
    deep_link = f"https://t.me/{BOT_USERNAME}?start=series_{series_code}"

    text = (
        f"📺 <b>Serial:</b> {series['title']}\n"
        f"🔢 <b>Kodi:</b> <code>{series_code}</code>\n"
        f"🎬 <b>Qismlar soni:</b> {len(episodes)} ta\n"
        f"🎞 <b>Mavjud qismlar:</b> {ep_list_str}\n"
        f"👁 <b>Ko'rishlar:</b> {series['views']} marta\n"
        f"🔗 <b>Auto havola:</b> <code>{deep_link}</code>\n\n"
        f"<i>Quyidagi tugmalar orqali ushbu serialni boshqaring:</i>"
    )

    await callback.message.edit_text(text, reply_markup=get_admin_single_series_kb(series_code), parse_mode="HTML")
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_quick_add_ep_"))
async def admin_quick_add_episode(callback: CallbackQuery, state: FSMContext):
    """Serial ichidan to'g'ridan-to'g'ri qism qo'shish"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    series_code = int(callback.data.replace("admin_quick_add_ep_", ""))
    series = await get_series_by_code(series_code, increment_views=False)
    if not series:
        return await callback.answer("Serial topilmadi!", show_alert=True)

    next_ep = await get_next_episode_number(series_code)
    await state.update_data(series_code=series_code, series_title=series["title"])
    await state.set_state(AddEpisodeState.waiting_for_episode_number)

    await callback.message.edit_text(
        f"📺 Serial: <b>{series['title']}</b> (Kod: <code>{series_code}</code>)\n\n"
        f"🔢 <b>Qism raqamini kiriting:</b>\n"
        f"<i>(Tavsiya etiladi: <b>{next_ep}</b>)</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_quick_del_ep_"))
async def admin_quick_del_episode(callback: CallbackQuery, state: FSMContext):
    """Serial ichidan to'g'ridan-to'g'ri qism o'chirish"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    series_code = int(callback.data.replace("admin_quick_del_ep_", ""))
    series = await get_series_by_code(series_code, increment_views=False)
    if not series:
        return await callback.answer("Serial topilmadi!", show_alert=True)

    episodes = await get_episodes_by_series(series_code)
    if not episodes:
        return await callback.answer("Ushbu serialda hali qismlar yo'q!", show_alert=True)

    ep_list = ", ".join([str(e["episode_number"]) for e in episodes])
    await state.update_data(series_code=series_code)
    await state.set_state(DeleteEpisodeState.waiting_for_episode_number)

    await callback.message.edit_text(
        f"📺 Serial: <b>{series['title']}</b>\n"
        f"Mavjud qismlar: <b>{ep_list}</b>\n\n"
        "🗑 <b>O'chirmoqchi bo'lgan qism raqamini kiriting:</b>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin_quick_del_ser_"))
async def admin_quick_del_series(callback: CallbackQuery):
    """Serialni to'g'ridan-to'g'ri o'chirish"""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat berilmagan!", show_alert=True)

    series_code = int(callback.data.replace("admin_quick_del_ser_", ""))
    deleted = await delete_series(series_code)
    if deleted:
        await callback.answer("✅ Serial va barcha qismlari o'chirildi!", show_alert=True)
    else:
        await callback.answer("❌ O'chirishda xatolik yuz berdi.", show_alert=True)

    series_list = await get_all_series()
    if not series_list:
        await callback.message.edit_text("📑 Bazada hozircha seriallar mavjud emas.", reply_markup=get_series_admin_menu())
    else:
        text = "📑 <b>Mavjud seriallar ro'yxati:</b>\n\n<i>Kerakli serialni tanlang:</i>"
        await callback.message.edit_text(text, reply_markup=get_admin_series_list_kb(series_list), parse_mode="HTML")





from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message, CallbackQuery
from config import BOT_USERNAME, ADMINS
from database import (
    add_user,
    get_movie_by_code,
    search_movies_by_title,
    add_saved_movie,
    remove_saved_movie,
    is_movie_saved,
    get_user_saved_movies,
)
from keyboards.user_kb import (
    get_movie_actions_kb,
    get_search_results_kb,
    get_subscription_kb,
    get_saved_movies_kb,
    get_start_kb,
)
from services.subscription import check_user_subscription

user_router = Router()


def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id in ADMINS


async def send_movie(message_or_call, movie: dict, user_id: int = None):
    """Kinoni foydalanuvchiga yuboruvchi yordamchi funksiya"""
    if user_id is None:
        user_id = message_or_call.from_user.id

    is_saved = await is_movie_saved(user_id, movie["code"])

    caption = (
        f"🎬 <b>Nomi:</b> {movie['title']}\n"
        f"📥 <b>Yuklangan:</b> {movie['views']} marta\n"
        f"🔢 <b>Kodi:</b> <code>{movie['code']}</code>\n\n"
        f"🤖 <a href=\"https://t.me/{BOT_USERNAME}\">TOP FILM</a>"
    )

    kb = get_movie_actions_kb(movie["code"], BOT_USERNAME, is_saved=is_saved)

    # Message yoki CallbackQuery ekanligini tekshirish
    send_func = message_or_call.answer_video if movie["file_type"] == "video" else message_or_call.answer_document

    try:
        await send_func(
            video=movie["file_id"] if movie["file_type"] == "video" else None,
            document=movie["file_id"] if movie["file_type"] == "document" else None,
            caption=caption,
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception:
        try:
            await message_or_call.answer_document(
                document=movie["file_id"],
                caption=caption,
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception:
            await message_or_call.answer("❌ Kinoni yuklashda xatolik yuz berdi.")


@user_router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject):
    """Start buyrug'i va Deep-linking (kod orqali ochish)"""
    user = message.from_user
    await add_user(user.id, user.username, user.full_name)

    args = command.args
    target_code = int(args) if (args and args.isdigit()) else None

    # Majburiy obunani tekshirish (adminlar uchun shart emas)
    if not is_admin(user.id):
        is_sub, unsubscribed = await check_user_subscription(message.bot, user.id)
        if not is_sub:
            payload = f"code_{target_code}" if target_code else "none"
            await message.answer(
                "⚠️ <b>Botdan to'liq foydalanish uchun quyidagi homiy kanallarga a'zo bo'ling:</b>\n\n"
                "Barcha kanallarga a'zo bo'lgach, <b>«✅ Obunani tekshirish»</b> tugmasini bosing:",
                reply_markup=get_subscription_kb(unsubscribed, payload=payload),
                parse_mode="HTML"
            )
            return

    # Agar start bilan birga kod yuborilgan bo'lsa: /start 15
    if target_code:
        movie = await get_movie_by_code(target_code)
        if movie:
            await send_movie(message, movie, user_id=user.id)
            return
        else:
            await message.answer(f"❌ Kechirasiz, <b>{target_code}</b>-kodli kino topilmadi.", parse_mode="HTML")
            return

    # Oddiy start bosilganda
    await message.answer(
        f"👋 Assalomu alaykum, <b>{user.full_name}</b>!\n\n"
        f"🎬 <a href=\"https://t.me/{BOT_USERNAME}\">TOP FILM</a> kino botiga xush kelibsiz!\n\n"
        "🔍 Kinoni yuklab olish uchun uning <b>kodini</b> yuboring (Masalan: <code>1</code>)\n"
        "yoki kino <b>nomini</b> yozing.\n\n"
        "⭐️ Saqlangan filmlaringiz: /saved",
        reply_markup=get_start_kb(),
        parse_mode="HTML"
    )


@user_router.message(Command("saved"))
async def saved_movies_handler(message: Message):
    """Foydalanuvchi saqlagan filmlar ro'yxatini ko'rsatish"""
    user = message.from_user
    movies = await get_user_saved_movies(user.id)

    if not movies:
        await message.answer(
            "⭐️ <b>Sizda hozircha saqlangan filmlar mavjud emas.</b>\n\n"
            "Har qanday filmni yuklaganingizda uning ostidagi «💾 Saqlab qo'yish» tugmasini bossangiz, bu yerga saqlanadi.",
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"⭐️ <b>Siz saqlagan filmlar ({len(movies)} ta):</b>\n\n"
        "Kerakli filmni yuklab olish uchun uning nomini bosing:",
        reply_markup=get_saved_movies_kb(movies),
        parse_mode="HTML"
    )


@user_router.callback_query(F.data.startswith("save_"))
async def save_movie_callback(callback: CallbackQuery):
    """Filmni saqlanganlarga qo'shish"""
    code = int(callback.data.replace("save_", ""))
    user_id = callback.from_user.id

    await add_saved_movie(user_id, code)
    await callback.answer("✅ Film saqlanganlarga qo'shildi!\n/saved orqali ko'rishingiz mumkin.", show_alert=True)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_movie_actions_kb(code, BOT_USERNAME, is_saved=True)
        )
    except Exception:
        pass


@user_router.callback_query(F.data.startswith("unsave_list_"))
async def unsave_from_list_callback(callback: CallbackQuery):
    """/saved ro'yxatidan filmni olib tashlash"""
    code = int(callback.data.replace("unsave_list_", ""))
    user_id = callback.from_user.id

    await remove_saved_movie(user_id, code)
    await callback.answer("❌ Film saqlanganlardan olib tashlandi.", show_alert=False)

    movies = await get_user_saved_movies(user_id)
    if not movies:
        await callback.message.edit_text(
            "⭐️ <b>Sizda saqlangan filmlar qolmadi.</b>",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_reply_markup(
            reply_markup=get_saved_movies_kb(movies)
        )


@user_router.callback_query(F.data.startswith("unsave_"))
async def unsave_movie_callback(callback: CallbackQuery):
    """Film ostidagi tugmadan saqlanganlikni bekor qilish"""
    code = int(callback.data.replace("unsave_", ""))
    user_id = callback.from_user.id

    await remove_saved_movie(user_id, code)
    await callback.answer("❌ Film saqlanganlardan olib tashlandi.", show_alert=True)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_movie_actions_kb(code, BOT_USERNAME, is_saved=False)
        )
    except Exception:
        pass


@user_router.callback_query(F.data.startswith("check_sub_"))
async def check_subscription_callback(callback: CallbackQuery):
    """Obunani qayta tekshirish tugmasi bosilganda"""
    payload = callback.data.replace("check_sub_", "")
    user_id = callback.from_user.id

    is_sub, unsubscribed = await check_user_subscription(callback.bot, user_id)
    if not is_sub:
        await callback.answer(
            "❌ Hali barcha kanallarga a'zo bo'lmadingiz! Iltimos, obuna bo'ling.",
            show_alert=True
        )
        try:
            await callback.message.edit_reply_markup(
                reply_markup=get_subscription_kb(unsubscribed, payload=payload)
            )
        except Exception:
            pass
        return

    await callback.answer("✅ Rahmat! Obuna tasdiqlandi.", show_alert=False)
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Payload bo'yicha amalni davom ettirish
    if payload.startswith("code_"):
        code_str = payload.replace("code_", "")
        if code_str.isdigit():
            movie = await get_movie_by_code(int(code_str))
            if movie:
                await send_movie(callback.message, movie, user_id=user_id)
                return
            else:
                await callback.message.answer(f"❌ <b>{code_str}</b>-kodli kino topilmadi.", parse_mode="HTML")
                return

    elif payload.startswith("query_"):
        query = payload.replace("query_", "")
        results = await search_movies_by_title(query, limit=10)
        if results:
            if len(results) == 1:
                movie = await get_movie_by_code(results[0]["code"])
                if movie:
                    await send_movie(callback.message, movie, user_id=user_id)
                    return
            await callback.message.answer(
                f"🔍 <b>'{query}'</b> bo'yicha topilgan kinolar:\n<i>Kerakli kinoni tanlang:</i>",
                reply_markup=get_search_results_kb(results),
                parse_mode="HTML"
            )
            return

    # Standart xush kelibsiz xabari
    await callback.message.answer(
        f"👋 Assalomu alaykum!\n\n"
        f"🎬 <a href=\"https://t.me/{BOT_USERNAME}\">TOP FILM</a> kino botiga xush kelibsiz!\n\n"
        "🔍 Kinoni yuklab olish uchun uning <b>kodini</b> yuboring (Masalan: <code>1</code>)\n"
        "yoki kino <b>nomini</b> yozing.\n\n"
        "⭐️ Saqlangan filmlaringiz: /saved",
        reply_markup=get_start_kb(),
        parse_mode="HTML"
    )


@user_router.callback_query(F.data.startswith("get_movie_"))
async def callback_get_movie(callback: CallbackQuery):
    """Qidiruv natijasidan kinoni tanlaganda yuklab berish"""
    user_id = callback.from_user.id
    code = int(callback.data.split("_")[2])

    if not is_admin(user_id):
        is_sub, unsubscribed = await check_user_subscription(callback.bot, user_id)
        if not is_sub:
            await callback.answer("⚠️ Avval homiy kanallarga a'zo bo'ling!", show_alert=True)
            await callback.message.answer(
                "⚠️ <b>Kinoni yuklashdan oldin quyidagi kanallarga a'zo bo'ling:</b>",
                reply_markup=get_subscription_kb(unsubscribed, payload=f"code_{code}"),
                parse_mode="HTML"
            )
            return

    movie = await get_movie_by_code(code)
    if movie:
        await send_movie(callback.message, movie, user_id=user_id)
    else:
        await callback.message.answer("❌ Kino topilmadi.")
    
    await callback.answer()


@user_router.message(F.text)
async def search_movie_handler(message: Message):
    """Foydalanuvchi matn yoki raqam yuborganda qidirish"""
    user = message.from_user
    text = message.text.strip()

    # Majburiy obunani tekshirish
    if not is_admin(user.id):
        is_sub, unsubscribed = await check_user_subscription(message.bot, user.id)
        if not is_sub:
            payload = f"code_{text}" if text.isdigit() else f"query_{text[:20]}"
            await message.answer(
                "⚠️ <b>Botdan foydalanish uchun quyidagi homiy kanallarga a'zo bo'ling:</b>\n\n"
                "Barcha kanallarga a'zo bo'lgach, <b>«✅ Obunani tekshirish»</b> tugmasini bosing:",
                reply_markup=get_subscription_kb(unsubscribed, payload=payload),
                parse_mode="HTML"
            )
            return

    # Agar raqam bo'lsa (kino kodi)
    if text.isdigit():
        code = int(text)
        movie = await get_movie_by_code(code)
        if movie:
            await send_movie(message, movie, user_id=user.id)
        else:
            await message.answer(
                f"❌ <b>{code}</b>-kodli kino topilmadi.\n"
                "Iltimos, kod to'g'riligini tekshiring yoki kino nomini yozib qidiring.",
                parse_mode="HTML"
            )
        return

    # Agar kino nomi yozilgan bo'lsa
    results = await search_movies_by_title(text, limit=10)
    if not results:
        await message.answer(
            f"🔍 <b>'{text}'</b> bo'yicha hech qanday kino topilmadi.\n\n"
            "Iltimos, kino nomini to'g'riroq yozing yoki uning kodini yuboring.",
            parse_mode="HTML"
        )
        return

    if len(results) == 1:
        # Bitta kino topilsa to'g'ridan-to'g'ri yuborish
        movie = await get_movie_by_code(results[0]["code"])
        if movie:
            await send_movie(message, movie, user_id=user.id)
            return

    # Bir nechta kino topilsa ro'yxat chiqarish
    await message.answer(
        f"🔍 <b>'{text}'</b> bo'yicha topilgan kinolar:\n"
        "<i>Kerakli kinoni tanlang:</i>",
        reply_markup=get_search_results_kb(results),
        parse_mode="HTML"
    )

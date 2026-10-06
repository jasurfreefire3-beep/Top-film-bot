from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_USERNAME, ADMINS
from database import (
    add_user,
    get_movie_by_code,
    search_movies_by_title,
    add_saved_movie,
    remove_saved_movie,
    is_movie_saved,
    get_user_saved_movies,
    get_series_by_code,
    search_series_by_title,
    get_episodes_by_series,
    get_episode,
)
from keyboards.user_kb import (
    get_movie_actions_kb,
    get_search_results_kb,
    get_subscription_kb,
    get_saved_movies_kb,
    get_start_kb,
    get_episodes_selection_kb,
    get_episode_player_kb,
)
import logging
from services.subscription import check_user_subscription
from services.cover import get_video_cover, get_video_thumbnail

logger = logging.getLogger(__name__)

user_router = Router()


def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id in ADMINS


async def send_movie(message_or_call, movie: dict, user_id: int = None):
    """Kinoni foydalanuvchiga yuboruvchi yordamchi funksiya (muqova/cover bilan)"""
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
    file_id = movie["file_id"]
    file_type = movie.get("file_type", "video")

    target = message_or_call.message if isinstance(message_or_call, CallbackQuery) else message_or_call

    try:
        if file_type == "video":
            thumb_file = get_video_thumbnail()
            cover_file = get_video_cover()

            kwargs = {
                "video": file_id,
                "caption": caption,
                "reply_markup": kb,
                "parse_mode": "HTML"
            }
            if thumb_file:
                kwargs["thumbnail"] = thumb_file
            if cover_file:
                kwargs["cover"] = cover_file

            try:
                await target.answer_video(**kwargs)
            except Exception as e_cover:
                logger.warning(f"Video cover bilan yuborishda ogohlantirish: {e_cover}. Coversiz yuborilmoqda...")
                await target.answer_video(
                    video=file_id,
                    caption=caption,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
        else:
            await target.answer_document(
                document=file_id,
                caption=caption,
                reply_markup=kb,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Kino yuborishda xatolik: {e}")
        try:
            await target.answer_document(
                document=file_id,
                caption=caption,
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception as e2:
            logger.error(f"Fallback ham ishlamadi: {e2}")
            await target.answer("❌ Kinoni yuklashda xatolik yuz berdi.")


async def send_series_menu(message_or_call, series: dict, user_id: int):
    """Serial qismlari ro'yxatini va tugmalarini chiqarish"""
    episodes = await get_episodes_by_series(series["code"])
    is_saved = await is_movie_saved(user_id, series["code"])

    text = (
        f"📺 <b>{series['title']}</b>\n\n"
        f"🔢 <b>Serial kodi:</b> <code>{series['code']}</code>\n"
        f"🎬 <b>Mavjud qismlar:</b> {len(episodes)} ta\n"
        f"👁 <b>Ko'rishlar:</b> {series['views']} marta\n\n"
        f"<i>Ko'rmoqchi bo'lgan qismni tanlang:</i>"
    )
    if not episodes:
        text += "\n\n⚠️ <i>Ushbu serialga hali qismlar yuklanmagan.</i>"

    kb = get_episodes_selection_kb(series["code"], episodes, BOT_USERNAME, is_saved=is_saved)

    if isinstance(message_or_call, Message):
        await message_or_call.answer(text, reply_markup=kb, parse_mode="HTML")
    elif isinstance(message_or_call, CallbackQuery):
        msg = message_or_call.message
        # Agar oldingi xabar video, rasm yoki hujjat bo'lsa, edit_text ishlamaydi, yangi xabar qilib yuboramiz
        if msg.video or msg.photo or msg.document:
            await msg.answer(text, reply_markup=kb, parse_mode="HTML")
        else:
            try:
                await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")
            except Exception:
                await msg.answer(text, reply_markup=kb, parse_mode="HTML")


async def send_episode_video(message_or_call, series: dict, episode: dict, user_id: int):
    """Serial qismini yuborish"""
    is_saved = await is_movie_saved(user_id, series["code"])
    caption = (
        f"📺 <b>{series['title']}</b>\n"
        f"🎬 <b>{episode['episode_number']}-qism</b>\n\n"
        f"🔢 <b>Serial kodi:</b> <code>{series['code']}</code>\n"
        f"👁 <b>Ko'rishlar:</b> {episode['views']} marta\n\n"
        f"🤖 <a href=\"https://t.me/{BOT_USERNAME}\">TOP FILM</a>"
    )
    kb = get_episode_player_kb(series["code"], episode["episode_number"], BOT_USERNAME, is_saved=is_saved)
    file_id = episode["file_id"]
    file_type = episode.get("file_type", "video")

    target = message_or_call.message if isinstance(message_or_call, CallbackQuery) else message_or_call

    try:
        if file_type == "video":
            thumb_file = get_video_thumbnail()
            cover_file = get_video_cover()

            kwargs = {
                "video": file_id,
                "caption": caption,
                "reply_markup": kb,
                "parse_mode": "HTML"
            }
            if thumb_file:
                kwargs["thumbnail"] = thumb_file
            if cover_file:
                kwargs["cover"] = cover_file

            try:
                await target.answer_video(**kwargs)
            except Exception as e_cover:
                logger.warning(f"Qismni cover bilan yuborishda ogohlantirish: {e_cover}. Coversiz yuborilmoqda...")
                await target.answer_video(
                    video=file_id,
                    caption=caption,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
        else:
            await target.answer_document(
                document=file_id,
                caption=caption,
                reply_markup=kb,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Qism yuborishda xatolik: {e}")
        try:
            await target.answer_document(
                document=file_id,
                caption=caption,
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception as e2:
            logger.error(f"Fallback ham ishlamadi: {e2}")
            await target.answer("❌ Qismni yuklashda xatolik yuz berdi.")


@user_router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject):
    """Start buyrug'i va Deep-linking (kod orqali ochish)"""
    user = message.from_user
    await add_user(user.id, user.username, user.full_name)

    args = command.args
    target_code = None
    is_series_link = False

    if args:
        if args.startswith("series_"):
            code_str = args.replace("series_", "")
            if code_str.isdigit():
                target_code = int(code_str)
                is_series_link = True
        elif args.isdigit():
            target_code = int(args)

    # Majburiy obunani tekshirish (adminlar uchun shart emas)
    if not is_admin(user.id):
        is_sub, unsubscribed = await check_user_subscription(message.bot, user.id)
        if not is_sub:
            payload = f"start_{args}" if args else "none"
            await message.answer(
                "⚠️ <b>Botdan to'liq foydalanish uchun quyidagi homiy kanallarga a'zo bo'ling:</b>\n\n"
                "Barcha kanallarga a'zo bo'lgach, <b>«✅ Obunani tekshirish»</b> tugmasini bosing:",
                reply_markup=get_subscription_kb(unsubscribed, payload=payload),
                parse_mode="HTML"
            )
            return

    # Agar start bilan birga kod yuborilgan bo'lsa
    if target_code is not None:
        if is_series_link:
            series = await get_series_by_code(target_code)
            if series:
                await send_series_menu(message, series, user_id=user.id)
                return
        else:
            # Avval kinodan qidirish
            movie = await get_movie_by_code(target_code)
            if movie:
                await send_movie(message, movie, user_id=user.id)
                return
            # Agar kinoda bo'lmasa, serialdan qidirish
            series = await get_series_by_code(target_code)
            if series:
                await send_series_menu(message, series, user_id=user.id)
                return

        await message.answer(f"❌ Kechirasiz, <b>{target_code}</b>-kodli film yoki serial topilmadi.", parse_mode="HTML")
        return

    # Oddiy start bosilganda
    await message.answer(
        f"👋 Assalomu alaykum, <b>{user.full_name}</b>!\n\n"
        f"🎬 <a href=\"https://t.me/{BOT_USERNAME}\">TOP FILM</a> kino va serial botiga xush kelibsiz!\n\n"
        "🔍 Film yoki serialni yuklab olish uchun uning <b>kodini</b> yuboring (Masalan: <code>1</code>)\n"
        "yoki <b>nomini</b> yozing.\n\n"
        "⭐️ Saqlanganlaringiz: /saved",
        reply_markup=get_start_kb(),
        parse_mode="HTML"
    )


@user_router.message(Command("saved"))
async def saved_movies_handler(message: Message):
    """Foydalanuvchi saqlagan filmlar va seriallar ro'yxatini ko'rsatish"""
    user = message.from_user
    movies = await get_user_saved_movies(user.id)

    if not movies:
        await message.answer(
            "⭐️ <b>Sizda hozircha saqlangan film yoki seriallar mavjud emas.</b>\n\n"
            "Har qanday film yoki serialni yuklaganingizda uning ostidagi «💾 Saqlab qo'yish» tugmasini bossangiz, bu yerga saqlanadi.",
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"⭐️ <b>Siz saqlaganlar ({len(movies)} ta):</b>\n\n"
        "Yuklab olish uchun nomini bosing:",
        reply_markup=get_saved_movies_kb(movies),
        parse_mode="HTML"
    )


@user_router.callback_query(F.data.startswith("save_"))
async def save_movie_callback(callback: CallbackQuery):
    """Filmni yoki serialni saqlanganlarga qo'shish"""
    code = int(callback.data.replace("save_", ""))
    user_id = callback.from_user.id

    await add_saved_movie(user_id, code)
    await callback.answer("✅ Saqlanganlarga qo'shildi!\n/saved orqali ko'rishingiz mumkin.", show_alert=True)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_movie_actions_kb(code, BOT_USERNAME, is_saved=True)
        )
    except Exception:
        pass


@user_router.callback_query(F.data.startswith("unsave_list_"))
async def unsave_from_list_callback(callback: CallbackQuery):
    """/saved ro'yxatidan olib tashlash"""
    code = int(callback.data.replace("unsave_list_", ""))
    user_id = callback.from_user.id

    await remove_saved_movie(user_id, code)
    await callback.answer("❌ Saqlanganlardan olib tashlandi.", show_alert=False)

    movies = await get_user_saved_movies(user_id)
    if not movies:
        await callback.message.edit_text(
            "⭐️ <b>Sizda saqlanganlar qolmadi.</b>",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_reply_markup(
            reply_markup=get_saved_movies_kb(movies)
        )


@user_router.callback_query(F.data.startswith("unsave_"))
async def unsave_movie_callback(callback: CallbackQuery):
    """Ostidagi tugmadan saqlanganlikni bekor qilish"""
    code = int(callback.data.replace("unsave_", ""))
    user_id = callback.from_user.id

    await remove_saved_movie(user_id, code)
    await callback.answer("❌ Saqlanganlardan olib tashlandi.", show_alert=True)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_movie_actions_kb(code, BOT_USERNAME, is_saved=False)
        )
    except Exception:
        pass


@user_router.callback_query(F.data.startswith("get_ep_"))
async def callback_get_episode(callback: CallbackQuery):
    """Serial qismini yuklab berish"""
    user_id = callback.from_user.id
    parts = callback.data.split("_")
    series_code = int(parts[2])
    ep_num = int(parts[3])

    if not is_admin(user_id):
        is_sub, unsubscribed = await check_user_subscription(callback.bot, user_id)
        if not is_sub:
            await callback.answer("⚠️ Avval homiy kanallarga a'zo bo'ling!", show_alert=True)
            await callback.message.answer(
                "⚠️ <b>Serialni ko'rish uchun quyidagi kanallarga a'zo bo'ling:</b>",
                reply_markup=get_subscription_kb(unsubscribed, payload=f"get_ep_{series_code}_{ep_num}"),
                parse_mode="HTML"
            )
            return

    series = await get_series_by_code(series_code, increment_views=False)
    episode = await get_episode(series_code, ep_num, increment_views=True)

    if series and episode:
        await send_episode_video(callback.message, series, episode, user_id=user_id)
    else:
        await callback.message.answer("❌ Ushbu qism topilmadi.")

    await callback.answer()


@user_router.callback_query(F.data.startswith("series_all_"))
async def callback_series_all_episodes(callback: CallbackQuery):
    """Serialning barcha qismlari ro'yxatiga qaytish"""
    user_id = callback.from_user.id
    series_code = int(callback.data.split("_")[2])
    series = await get_series_by_code(series_code, increment_views=False)

    if series:
        await send_series_menu(callback, series, user_id=user_id)
    else:
        await callback.message.answer("❌ Serial topilmadi.")

    await callback.answer()


@user_router.callback_query(F.data.startswith("get_series_"))
async def callback_get_series(callback: CallbackQuery):
    """Qidiruv natijasidan serial tanlanganda qismlar ro'yxatini chiqarish"""
    user_id = callback.from_user.id
    series_code = int(callback.data.split("_")[2])

    if not is_admin(user_id):
        is_sub, unsubscribed = await check_user_subscription(callback.bot, user_id)
        if not is_sub:
            await callback.answer("⚠️ Avval homiy kanallarga a'zo bo'ling!", show_alert=True)
            await callback.message.answer(
                "⚠️ <b>Serialni ko'rish uchun quyidagi kanallarga a'zo bo'ling:</b>",
                reply_markup=get_subscription_kb(unsubscribed, payload=f"get_series_{series_code}"),
                parse_mode="HTML"
            )
            return

    series = await get_series_by_code(series_code)
    if series:
        await send_series_menu(callback, series, user_id=user_id)
    else:
        await callback.message.answer("❌ Serial topilmadi.")

    await callback.answer()


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

    # Payload bo'yicha davom ettirish
    if payload.startswith("get_ep_"):
        parts = payload.split("_")
        series_code = int(parts[2])
        ep_num = int(parts[3])
        series = await get_series_by_code(series_code, increment_views=False)
        episode = await get_episode(series_code, ep_num, increment_views=True)
        if series and episode:
            await send_episode_video(callback.message, series, episode, user_id=user_id)
            return

    elif payload.startswith("get_series_"):
        series_code = int(payload.split("_")[2])
        series = await get_series_by_code(series_code)
        if series:
            await send_series_menu(callback, series, user_id=user_id)
            return

    elif payload.startswith("code_"):
        code_str = payload.replace("code_", "")
        if code_str.isdigit():
            code = int(code_str)
            movie = await get_movie_by_code(code)
            if movie:
                await send_movie(callback.message, movie, user_id=user_id)
                return
            series = await get_series_by_code(code)
            if series:
                await send_series_menu(callback, series, user_id=user_id)
                return

    elif payload.startswith("start_"):
        arg = payload.replace("start_", "")
        if arg.startswith("series_"):
            s_code = int(arg.replace("series_", ""))
            series = await get_series_by_code(s_code)
            if series:
                await send_series_menu(callback.message, series, user_id=user_id)
                return
        elif arg.isdigit():
            c = int(arg)
            movie = await get_movie_by_code(c)
            if movie:
                await send_movie(callback.message, movie, user_id=user_id)
                return
            series = await get_series_by_code(c)
            if series:
                await send_series_menu(callback.message, series, user_id=user_id)
                return

    # Standart start xabari
    await callback.message.answer(
        f"👋 Assalomu alaykum!\n\n"
        f"🎬 <a href=\"https://t.me/{BOT_USERNAME}\">TOP FILM</a> kino va serial botiga xush kelibsiz!\n\n"
        "🔍 Film yoki serialni yuklab olish uchun uning <b>kodini</b> yuboring (Masalan: <code>1</code>)\n"
        "yoki <b>nomini</b> yozing.\n\n"
        "⭐️ Saqlanganlaringiz: /saved",
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

    # Agar raqam bo'lsa (film yoki serial kodi)
    if text.isdigit():
        code = int(text)
        # 1. Avval kinolardan qidirish
        movie = await get_movie_by_code(code)
        if movie:
            await send_movie(message, movie, user_id=user.id)
            return

        # 2. Seriallardan qidirish
        series = await get_series_by_code(code)
        if series:
            await send_series_menu(message, series, user_id=user.id)
            return

        await message.answer(
            f"❌ <b>{code}</b>-kodli film yoki serial topilmadi.\n"
            "Iltimos, kod to'g'riligini tekshiring yoki nomini yozib qidiring.",
            parse_mode="HTML"
        )
        return

    # Agar matn yozilgan bo'lsa: film va seriallardan qidirish
    movies = await search_movies_by_title(text, limit=10)
    series_list = await search_series_by_title(text, limit=10)

    if not movies and not series_list:
        await message.answer(
            f"🔍 <b>'{text}'</b> bo'yicha hech qanday film yoki serial topilmadi.\n\n"
            "Iltimos, nomini to'g'riroq yozing yoki uning kodini yuboring.",
            parse_mode="HTML"
        )
        return

    # Agar jami faqat bitta natija bo'lsa
    if len(movies) == 1 and len(series_list) == 0:
        m = await get_movie_by_code(movies[0]["code"])
        if m:
            await send_movie(message, m, user_id=user.id)
            return

    if len(series_list) == 1 and len(movies) == 0:
        s = await get_series_by_code(series_list[0]["code"])
        if s:
            await send_series_menu(message, s, user_id=user.id)
            return

    # Natijalar ro'yxati tugmalarini yasash
    buttons = []
    for m in movies:
        buttons.append([
            InlineKeyboardButton(text=f"🎬 {m['title']} (Kod: {m['code']})", callback_data=f"get_movie_{m['code']}")
        ])
    for s in series_list:
        buttons.append([
            InlineKeyboardButton(text=f"📺 {s['title']} ({s['episode_count']} qism) (Kod: {s['code']})", callback_data=f"get_series_{s['code']}")
        ])

    search_kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        f"🔍 <b>'{text}'</b> bo'yicha topilgan natijalar:\n<i>Keraklisini tanlang:</i>",
        reply_markup=search_kb,
        parse_mode="HTML"
    )

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeDefault

from config import BOT_TOKEN, ADMINS
from database import init_db
from handlers.admin import admin_router
from handlers.user import user_router

# Loggingni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    """Bot komandalarini o'rnatish"""
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="saved", description="⭐️ Saqlangan filmlar"),
        BotCommand(command="admin", description="Admin paneli (faqat adminlar uchun)")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


async def main():
    logger.info("Bot ishga tushirilmoqda...")

    # Ma'lumotlar bazasini initsializatsiya qilish
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    # Bot va Dispatcherni yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Routerlarni ro'yxatdan o'tkazish
    dp.include_router(admin_router)
    dp.include_router(user_router)

    # Bot komandalarini o'rnatish
    await set_commands(bot)

    # Eski kutilayotgan yangilanishlarni (updates) tozalash
    await bot.delete_webhook(drop_pending_updates=True)

    # Adminlarga bot ishga tushgani haqida xabar yuborish
    for admin_id in ADMINS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text="🚀 <b>Kino bot muvaffaqiyatli ishga tushdi!</b>\n\n"
                     "Boshqaruv panelini ochish uchun: /admin",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Admin {admin_id} ga xabar yetkazilmadi: {e}")

    logger.info("Bot faol ishlamoqda (polling)...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")


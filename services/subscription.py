import logging
from typing import Tuple, List, Dict, Any
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from database import get_all_channels

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = {
    ChatMemberStatus.CREATOR,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.RESTRICTED
}


async def check_user_subscription(bot: Bot, user_id: int) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Foydalanuvchining majburiy kanallarga a'zoligini tekshirish.
    Qaytaradi:
    (is_subscribed: bool, unsubscribed_channels: list)
    """
    channels = await get_all_channels()
    if not channels:
        return True, []

    unsubscribed = []

    for ch in channels:
        channel_id = ch["channel_id"]
        # Agar channel_id raqam bo'lsa int ga o'tkazish
        try:
            target_chat_id = int(channel_id) if channel_id.startswith("-") or channel_id.isdigit() else channel_id
            member = await bot.get_chat_member(chat_id=target_chat_id, user_id=user_id)
            if member.status not in ACTIVE_STATUSES:
                unsubscribed.append(ch)
        except Exception as e:
            logger.warning(f"Kanalga a'zolikni tekshirishda xatolik ({channel_id}): {e}")
            # Agar bot kanalda admin bo'lmasa yoki kanal topilmasa ham foydalanuvchiga kanalni ko'rsatamiz
            unsubscribed.append(ch)

    return len(unsubscribed) == 0, unsubscribed


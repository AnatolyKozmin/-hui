import os 
import asyncio

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from services.gspread_client import GSpreadClient
from services.redis_client import CacheKeys, RedisClient
from bot.routers.common import setup_common_router
from bot.routers.superadmin import setup_superadmin_router
from bot.routers.faculty_admin import setup_faculty_admin_router
from bot.routers.interviewer_registration import setup_interviewer_registration_router


load_dotenv()


bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()


# Services
redis_client = RedisClient()
gs_client = GSpreadClient()


async def get_bot_username() -> str:
    bot_username = await redis_client.get(CacheKeys.BOT_USERNAME)
    if not bot_username:
        me = await bot.get_me()
        bot_username = me.username
        await redis_client.set(CacheKeys.BOT_USERNAME, bot_username)
    return bot_username


# Routers
dp.include_router(setup_common_router(redis_client))
dp.include_router(setup_superadmin_router())
dp.include_router(setup_faculty_admin_router(redis_client, gs_client, bot))
dp.include_router(setup_interviewer_registration_router(redis_client))


async def main():
    print("Bot is running")
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())
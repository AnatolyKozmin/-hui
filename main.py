import os 
import asyncio

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from services.gspread_client import GSpreadClient
from state.inmemory import AppState
from bot.routers.common import setup_common_router
from bot.routers.admin import setup_admin_router


load_dotenv()


bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()


state = AppState()
gs = GSpreadClient()


async def get_bot_username() -> str:
    if state.bot_username is None:
        me = await bot.get_me()
        state.bot_username = me.username
    return state.bot_username


# Routers
dp.include_router(setup_common_router(state))
dp.include_router(setup_admin_router(state, gs, get_bot_username))


async def main():
    print("Bot is running")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
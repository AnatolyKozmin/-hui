from typing import Optional

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from state.inmemory import AppState


def setup_common_router(state: AppState) -> Router:
    router = Router()

    @router.message(Command("start"))
    async def cmd_start(message: Message, command: CommandObject) -> None:
        arg = command.args or ""
        if arg.startswith("inv_"):
            token = arg[4:]
            payload = state.invites.get(token)
            if not payload:
                await message.answer("Ссылка недействительна или устарела")
                return
            state.invites.pop(token, None)
            await message.answer(
                f"Готово! Вы привязаны как собеседующий: {payload['tab_name']} ({payload['kind']})"
            )
            return

        await message.answer("Привет! Я бот для записи и управления собеседованиями.")

    return router



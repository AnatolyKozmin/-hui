import os
import secrets
from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from services.gspread_client import GSpreadClient
from state.inmemory import AppState


def is_admin(user_id: int) -> bool:
    raw = os.getenv("ADMIN_IDS", "")
    if not raw:
        return False
    try:
        ids = {int(x.strip()) for x in raw.split(",") if x.strip()}
    except ValueError:
        ids = set()
    return user_id in ids


def setup_admin_router(state: AppState, gs: GSpreadClient, get_bot_username):
    router = Router()

    def admin_menu_kb() -> InlineKeyboardMarkup:
        buttons = [
            [InlineKeyboardButton(text="Задать таблицы", callback_data="adm|set_sheets")],
            [InlineKeyboardButton(text="Список листов", callback_data="adm|list_tabs")],
            [InlineKeyboardButton(text="Импорт участников", callback_data="adm|parse_participants")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @router.message(Command("set_sheets"))
    async def cmd_set_sheets(message: Message, command: CommandObject) -> None:
        if not is_admin(message.from_user.id):
            await message.answer("Команда доступна только администратору")
            return
        if not command.args:
            await message.answer(
                "Формат: /set_sheets <faculty_slug> <ne_opyt_id> <opyt_id> <svod_id>"
            )
            return
        parts = command.args.split()
        if len(parts) != 4:
            await message.answer(
                "Нужно передать 4 аргумента: faculty_slug ne_opyt_id opyt_id svod_id"
            )
            return
        faculty, ne_opyt_id, opyt_id, svod_id = parts
        state.faculty_sheets[faculty] = {
            "ne_opyt": ne_opyt_id,
            "opyt": opyt_id,
            "svod": svod_id,
        }
        await message.answer("Сохранено")

    @router.message(Command("admin"))
    async def cmd_admin(message: Message) -> None:
        if not is_admin(message.from_user.id):
            await message.answer("Недоступно")
            return
        await message.answer("Панель администратора:", reply_markup=admin_menu_kb())

    @router.callback_query(F.data == "adm|set_sheets")
    async def cb_adm_set_sheets(callback: CallbackQuery) -> None:
        if not is_admin(callback.from_user.id):
            await callback.answer("Недоступно", show_alert=True)
            return
        state.pending[callback.from_user.id] = {"type": "set_sheets", "ctx": {}}
        await callback.message.answer(
            "Отправьте одной строкой: <faculty_slug> <ne_opyt_id> <opyt_id> <svod_id>"
        )
        await callback.answer()

    @router.callback_query(F.data == "adm|list_tabs")
    async def cb_adm_list_tabs(callback: CallbackQuery) -> None:
        if not is_admin(callback.from_user.id):
            await callback.answer("Недоступно", show_alert=True)
            return
        state.pending[callback.from_user.id] = {"type": "list_tabs", "ctx": {}}
        await callback.message.answer(
            "Отправьте: <faculty_slug> <ne_opyt|opyt>"
        )
        await callback.answer()

    @router.callback_query(F.data == "adm|parse_participants")
    async def cb_adm_parse_participants(callback: CallbackQuery) -> None:
        if not is_admin(callback.from_user.id):
            await callback.answer("Недоступно", show_alert=True)
            return
        state.pending[callback.from_user.id] = {"type": "parse_participants", "ctx": {}}
        await callback.message.answer(
            "Отправьте: <faculty_slug>"
        )
        await callback.answer()

    @router.message(Command("list_tabs"))
    async def cmd_list_tabs(message: Message, command: CommandObject) -> None:
        if not is_admin(message.from_user.id):
            await message.answer("Команда доступна только администратору")
            return
        if not command.args:
            await message.answer("Формат: /list_tabs <faculty_slug> <ne_opyt|opyt>")
            return
        parts = command.args.split()
        if len(parts) != 2 or parts[1] not in ("ne_opyt", "opyt"):
            await message.answer("Формат: /list_tabs <faculty_slug> <ne_opyt|opyt>")
            return
        faculty, kind = parts
        sheet_id = state.faculty_sheets.get(faculty, {}).get(kind)
        if not sheet_id:
            await message.answer("Сначала задайте таблицы через /set_sheets")
            return
        try:
            tabs = gs.list_worksheet_titles(sheet_id)
        except Exception as e:
            await message.answer(f"Ошибка чтения: {e}")
            return
        if not tabs:
            await message.answer("Листов не найдено")
            return
        buttons = [
            [InlineKeyboardButton(text=title, callback_data=f"geninv|{faculty}|{kind}|{title}")]
            for title in tabs
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("Выберите лист (собеседующего) для создания ссылки:", reply_markup=kb)

    @router.callback_query(F.data.startswith("geninv|"))
    async def cb_gen_invite(callback: CallbackQuery) -> None:
        if not is_admin(callback.from_user.id):
            await callback.answer("Недоступно", show_alert=True)
            return
        try:
            _, faculty, kind, tab_name = callback.data.split("|", maxsplit=3)
        except Exception:
            await callback.answer("Неверные данные", show_alert=True)
            return
        token = secrets.token_urlsafe(10)
        state.invites[token] = {
            "faculty": faculty,
            "kind": kind,
            "tab_name": tab_name,
        }
        bot_username = await get_bot_username()
        link = f"https://t.me/{bot_username}?start=inv_{token}"
        await callback.message.answer(
            f"Ссылка для {tab_name} ({kind}):\n{link}"
        )
        await callback.answer()

    @router.message(Command("parse_participants"))
    async def cmd_parse_participants(message: Message, command: CommandObject) -> None:
        if not is_admin(message.from_user.id):
            await message.answer("Команда доступна только администратору")
            return
        if not command.args:
            await message.answer("Формат: /parse_participants <faculty_slug>")
            return
        faculty = command.args.strip()
        sheet_id = state.faculty_sheets.get(faculty, {}).get("svod")
        if not sheet_id:
            await message.answer("Сначала задайте таблицы через /set_sheets")
            return
        try:
            rows = gs.read_participants(sheet_id, worksheet_title="участники")
        except Exception as e:
            await message.answer(f"Ошибка чтения: {e}")
            return
        state.participants[faculty] = rows
        await message.answer(f"Импортировано участников: {len(rows)}")

    # Wizard text inputs
    @router.message()
    async def wizard_inputs(message: Message) -> None:
        if not is_admin(message.from_user.id):
            return
        pending = state.pending.get(message.from_user.id)
        if not pending:
            return
        action = pending.get("type")
        if action == "set_sheets":
            parts = message.text.split()
            if len(parts) != 4:
                await message.answer("Формат: <faculty_slug> <ne_opyt_id> <opyt_id> <svod_id>")
                return
            faculty, ne_opyt_id, opyt_id, svod_id = parts
            state.faculty_sheets[faculty] = {
                "ne_opyt": ne_opyt_id,
                "opyt": opyt_id,
                "svod": svod_id,
            }
            state.pending.pop(message.from_user.id, None)
            await message.answer("Сохранено", reply_markup=admin_menu_kb())
            return

        if action == "list_tabs":
            parts = message.text.split()
            if len(parts) != 2 or parts[1] not in ("ne_opyt", "opyt"):
                await message.answer("Формат: <faculty_slug> <ne_opyt|opyt>")
                return
            faculty, kind = parts
            sheet_id = state.faculty_sheets.get(faculty, {}).get(kind)
            if not sheet_id:
                await message.answer("Сначала задайте таблицы через /admin → Задать таблицы")
                return
            try:
                tabs = gs.list_worksheet_titles(sheet_id)
            except Exception as e:
                await message.answer(f"Ошибка чтения: {e}")
                return
            if not tabs:
                await message.answer("Листов не найдено")
                return
            buttons = [
                [InlineKeyboardButton(text=title, callback_data=f"geninv|{faculty}|{kind}|{title}")]
                for title in tabs
            ]
            kb = InlineKeyboardMarkup(inline_keyboard=buttons)
            state.pending.pop(message.from_user.id, None)
            await message.answer("Выберите лист (собеседующего) для создания ссылки:", reply_markup=kb)
            return

        if action == "parse_participants":
            faculty = message.text.strip()
            sheet_id = state.faculty_sheets.get(faculty, {}).get("svod")
            if not sheet_id:
                await message.answer("Сначала задайте таблицы через /admin → Задать таблицы")
                return
            try:
                rows = gs.read_participants(sheet_id, worksheet_title="участники")
            except Exception as e:
                await message.answer(f"Ошибка чтения: {e}")
                return
            state.participants[faculty] = rows
            state.pending.pop(message.from_user.id, None)
            await message.answer(f"Импортировано участников: {len(rows)}", reply_markup=admin_menu_kb())
            return

    return router



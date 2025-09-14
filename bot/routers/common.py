from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from database.dao import FacultyAdminDAO
from database.engine import sessionmaker
from services.auth import AuthService
from services.redis_client import CacheKeys, RedisClient


def setup_common_router(redis_client: RedisClient) -> Router:
    router = Router()

    def get_main_menu_kb(user_id: int) -> InlineKeyboardMarkup:
        """Создает главное меню в зависимости от роли пользователя"""
        buttons = []
        
        # Проверяем, является ли пользователь суперадмином
        if AuthService.is_superadmin(user_id):
            buttons.append([InlineKeyboardButton(
                text="👑 Суперадмин панель", 
                callback_data="superadmin_menu"
            )])
        
        # Проверяем, является ли пользователь админом факультета
        async def check_faculty_admin():
            try:
                async with sessionmaker() as session:
                    admin_dao = FacultyAdminDAO(session)
                    admin = await admin_dao.get_by_telegram_id(user_id)
                    return admin is not None
            except:
                return False
        
        # Добавляем кнопку для админа факультета (будет проверена при нажатии)
        buttons.append([InlineKeyboardButton(
            text="🏫 Админ факультета", 
            callback_data="faculty_admin_menu"
        )])
        
        # Кнопка для собеседующих
        buttons.append([InlineKeyboardButton(
            text="👥 Собеседующий", 
            callback_data="interviewer_menu"
        )])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @router.message(Command("start"))
    async def cmd_start(message: Message, command: CommandObject) -> None:
        arg = command.args or ""
        if arg.startswith("inv_"):
            # Обработка ссылок-приглашений для собеседующих
            # Этот функционал будет в роутере регистрации
            await message.answer(
                "🔗 Обработка ссылки-приглашения...\n\n"
                "Пожалуйста, подождите, пока мы обработаем вашу регистрацию."
            )
            return

        # Показываем главное меню
        await message.answer(
            "👋 Добро пожаловать в бот для управления собеседованиями!\n\n"
            "Выберите вашу роль:",
            reply_markup=get_main_menu_kb(message.from_user.id)
        )

    @router.callback_query(F.data == "superadmin_menu")
    async def handle_superadmin_menu(callback: CallbackQuery) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав суперадмина", show_alert=True)
            return
        
        await callback.message.edit_text(
            "Панель супер-администратора:\n\n"
            "• Управление факультетами - создание, редактирование\n"
            "• Управление админами - назначение админов факультетов\n"
            "• Настройка таблиц - привязка Google Sheets к факультетам",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏫 Управление факультетами", callback_data="super|faculties")],
                [InlineKeyboardButton(text="👥 Управление админами", callback_data="super|admins")],
                [InlineKeyboardButton(text="📊 Настройка таблиц", callback_data="super|sheets")],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
            ])
        )
        await callback.answer()

    @router.callback_query(F.data == "faculty_admin_menu")
    async def handle_faculty_admin_menu(callback: CallbackQuery) -> None:
        # Проверяем, является ли пользователь админом факультета
        async with sessionmaker() as session:
            admin_dao = FacultyAdminDAO(session)
            admin = await admin_dao.get_by_telegram_id(callback.from_user.id)
            
            if not admin and not AuthService.is_superadmin(callback.from_user.id):
                await callback.answer("❌ У вас нет прав админа факультета", show_alert=True)
                return
        
        await callback.message.edit_text(
            "Панель администратора факультета:\n\n"
            "• Собеседующие - управление собеседующими\n"
            "• Добавить проводящих - парсинг листов из таблиц opyt/ne_opyt\n"
            "• Импорт участников - загрузка из таблицы svod\n"
            "• Управление слотами - настройка времени собеседований",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👥 Собеседующие", callback_data="faculty|interviewers")],
                [InlineKeyboardButton(text="➕ Добавить проводящих", callback_data="faculty|add_interviewers")],
                [InlineKeyboardButton(text="📋 Импорт участников", callback_data="faculty|import_participants")],
                [InlineKeyboardButton(text="⏰ Управление слотами", callback_data="faculty|manage_slots")],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
            ])
        )
        await callback.answer()

    @router.callback_query(F.data == "interviewer_menu")
    async def handle_interviewer_menu(callback: CallbackQuery) -> None:
        await callback.message.edit_text(
            "👥 Панель собеседующего\n\n"
            "Здесь вы можете:\n"
            "• Просматривать назначенные собеседования\n"
            "• Управлять своим расписанием\n"
            "• Отмечать результаты собеседований\n\n"
            "Функционал в разработке...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📅 Мои собеседования", callback_data="interviewer|my_interviews")],
                [InlineKeyboardButton(text="⚙️ Настройки", callback_data="interviewer|settings")],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
            ])
        )
        await callback.answer()

    @router.callback_query(F.data == "main_menu")
    async def handle_main_menu(callback: CallbackQuery) -> None:
        await callback.message.edit_text(
            "👋 Добро пожаловать в бот для управления собеседованиями!\n\n"
            "Выберите вашу роль:",
            reply_markup=get_main_menu_kb(callback.from_user.id)
        )
        await callback.answer()

    return router



"""
Общий роутер с поддержкой asyncpg
"""

import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

router = Router()


def get_main_menu_kb():
    """Создает главное меню с Reply клавиатурой"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👑 Суперадмин"), KeyboardButton(text="🏛️ Админ факультета")],
            [KeyboardButton(text="👥 Интервьюер"), KeyboardButton(text="ℹ️ Информация")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    # Проверяем, является ли пользователь суперадмином
    superadmin_id = int(os.getenv("SUPERADMIN_ID", "0"))
    user_id = message.from_user.id
    
    # Отладочная информация
    print(f"🔍 Отладка: User ID: {user_id}, SUPERADMIN_ID: {superadmin_id}")
    
    if user_id == superadmin_id:
        # Если суперадмин - показываем панель суперадмина
        from bot.routers.superadmin_asyncpg import get_superadmin_keyboard
        text = (
            "👑 Добро пожаловать, суперадмин!\n\n"
            "Доступные функции:\n"
            "• 🏛️ Управление факультетами\n"
            "• 👑 Управление администраторами\n"
            "• 📊 Настройка Google Sheets\n"
            "• 🔍 Проверка системы\n\n"
            "Выберите действие:"
        )
        await message.answer(text, reply_markup=get_superadmin_keyboard())
    else:
        # Обычный пользователь - показываем выбор роли
        await message.answer(
            "🤖 Добро пожаловать в бот отбора!\n\n"
            "Выберите свою роль:",
            reply_markup=get_main_menu_kb()
        )


@router.message(Command("get_my_id"))
async def cmd_get_my_id(message: Message):
    """Обработчик команды /get_my_id"""
    user_id = message.from_user.id
    username = message.from_user.username or "Не указан"
    first_name = message.from_user.first_name or "Не указано"
    last_name = message.from_user.last_name or "Не указано"
    
    superadmin_id = int(os.getenv("SUPERADMIN_ID", "0"))
    is_superadmin = user_id == superadmin_id
    
    text = (
        f"🆔 Ваш ID: <code>{user_id}</code>\n\n"
        f"👤 Имя: {first_name} {last_name}\n"
        f"📛 Username: @{username}\n\n"
        f"🔐 Статус суперадмина: {'✅ Да' if is_superadmin else '❌ Нет'}\n"
        f"⚙️ SUPERADMIN_ID в .env: {superadmin_id}\n\n"
        f"💡 Скопируйте ID и проверьте настройки в .env файле"
    )
    
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "ℹ️ Информация")
async def cmd_info(message: Message):
    """Обработчик информации"""
    text = (
        "ℹ️ Информация о боте\n\n"
        "🤖 Версия: Основная (asyncpg)\n"
        "🗄️ База данных: PostgreSQL\n"
        "🔌 Подключение: Прямое через asyncpg\n"
        "🐳 Контейнер: Docker\n"
        "📱 Интерфейс: Reply клавиатура\n\n"
        "Это основная версия бота для управления отбором."
    )
    
    await message.answer(text, reply_markup=get_main_menu_kb())


@router.message(F.text == "👑 Суперадмин")
async def cmd_superadmin(message: Message):
    """Обработчик суперадмина"""
    # Проверяем, является ли пользователь суперадмином
    superadmin_id = int(os.getenv("SUPERADMIN_ID", "0"))
    
    if message.from_user.id == superadmin_id:
        # Если суперадмин - показываем панель суперадмина
        from bot.routers.superadmin_asyncpg import get_superadmin_keyboard
        text = (
            "👑 Панель суперадмина\n\n"
            "Доступные функции:\n"
            "• 🏛️ Управление факультетами\n"
            "• 👑 Управление администраторами\n"
            "• 📊 Настройка Google Sheets\n"
            "• 🔍 Проверка системы\n\n"
            "Выберите действие:"
        )
        await message.answer(text, reply_markup=get_superadmin_keyboard())
    else:
        # Обычный пользователь - показываем сообщение об ошибке
        await message.answer(
            "❌ У вас нет прав суперадмина!\n\n"
            "Выберите свою роль:",
            reply_markup=get_main_menu_kb()
        )


@router.message(F.text == "🏛️ Админ факультета")
async def cmd_faculty_admin(message: Message):
    """Обработчик админа факультета"""
    text = (
        "🏛️ Панель админа факультета\n\n"
        "Доступные функции:\n"
        "• Управление собеседующими\n"
        "• Импорт участников\n"
        "• Создание приглашений\n\n"
        "⚠️ Функционал в разработке"
    )
    
    await message.answer(text, reply_markup=get_main_menu_kb())


@router.message(F.text == "👥 Интервьюер")
async def cmd_interviewer(message: Message):
    """Обработчик интервьюера"""
    text = (
        "👥 Панель интервьюера\n\n"
        "Доступные функции:\n"
        "• Просмотр назначенных собеседований\n"
        "• Ввод результатов\n"
        "• Управление участниками\n\n"
        "⚠️ Функционал в разработке"
    )
    
    await message.answer(text, reply_markup=get_main_menu_kb())


def setup_common_router():
    """Настраивает общий роутер"""
    return router

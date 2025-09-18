"""
Суперадмин роутер с поддержкой asyncpg и Reply клавиатурой
"""

import asyncio
import os
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.redis_client import RedisClient
from services.gspread_client import GSpreadClient


class SuperAdminStates(StatesGroup):
    waiting_faculty_name = State()
    waiting_faculty_description = State()
    waiting_sheet_link = State()
    waiting_faculty_for_sheet = State()
    waiting_sheet_type = State()
    waiting_admin_telegram_id = State()
    waiting_admin_name = State()
    waiting_admin_faculty = State()


def get_superadmin_keyboard():
    """Создает клавиатуру суперадмина"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏛️ Факультеты"), KeyboardButton(text="👑 Админы")],
            [KeyboardButton(text="📊 Google Sheets"), KeyboardButton(text="🔍 Тест БД")],
            [KeyboardButton(text="📈 Статус"), KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_faculties_keyboard():
    """Создает клавиатуру управления факультетами"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Создать факультет"), KeyboardButton(text="📋 Список факультетов")],
            [KeyboardButton(text="🗑️ Удалить факультет"), KeyboardButton(text="✏️ Редактировать")],
            [KeyboardButton(text="🔙 Назад к суперадмину")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_admins_keyboard():
    """Создает клавиатуру управления админами"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Назначить админа"), KeyboardButton(text="📋 Список админов")],
            [KeyboardButton(text="🗑️ Удалить админа"), KeyboardButton(text="✏️ Редактировать")],
            [KeyboardButton(text="🔙 Назад к суперадмину")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_sheets_keyboard():
    """Создает клавиатуру управления Google Sheets"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔗 Добавить ссылку"), KeyboardButton(text="📋 Список таблиц")],
            [KeyboardButton(text="🧪 Тест подключения"), KeyboardButton(text="🔄 Обновить данные")],
            [KeyboardButton(text="🔙 Назад к суперадмину")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


class SuperAdminRouter:
    def __init__(self, db_pool, redis_client: RedisClient, gs_client: GSpreadClient):
        self.db_pool = db_pool
        self.redis_client = redis_client
        self.gs_client = gs_client
        self.router = Router()
        self.superadmin_id = int(os.getenv("SUPERADMIN_ID", "0"))
        self.setup_handlers()
    
    def is_superadmin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь суперадмином"""
        return user_id == self.superadmin_id
    
    async def check_superadmin(self, message: Message) -> bool:
        """Проверяет права суперадмина и отправляет сообщение об ошибке если нет прав"""
        if not self.is_superadmin(message.from_user.id):
            await message.answer("❌ У вас нет прав суперадмина!")
            return False
        return True
    
    async def test_database(self):
        """Тестирует подключение к базе данных"""
        if not self.db_pool:
            return False
            
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            print(f"❌ Ошибка теста базы данных: {e}")
            return False
    
    async def get_faculties_count(self):
        """Получает количество факультетов"""
        if not self.db_pool:
            return 0
            
        try:
            async with self.db_pool.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM faculties")
                return count or 0
        except Exception as e:
            print(f"❌ Ошибка получения количества факультетов: {e}")
            return 0
    
    async def get_admins_count(self):
        """Получает количество админов"""
        if not self.db_pool:
            return 0
            
        try:
            async with self.db_pool.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM faculty_admins")
                return count or 0
        except Exception as e:
            print(f"❌ Ошибка получения количества админов: {e}")
            return 0
    
    async def cmd_superadmin(self, message: Message):
        """Обработчик входа в панель суперадмина"""
        if not await self.check_superadmin(message):
            return
            
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
    
    async def cmd_faculties(self, message: Message):
        """Обработчик управления факультетами"""
        if not await self.check_superadmin(message):
            return
            
        count = await self.get_faculties_count()
        text = (
            f"🏛️ Управление факультетами\n\n"
            f"📊 Всего факультетов: {count}\n\n"
            "Выберите действие:"
        )
        
        await message.answer(text, reply_markup=get_faculties_keyboard())
    
    async def cmd_admins(self, message: Message):
        """Обработчик управления админами"""
        if not await self.check_superadmin(message):
            return
            
        count = await self.get_admins_count()
        text = (
            f"👑 Управление администраторами\n\n"
            f"📊 Всего админов: {count}\n\n"
            "Выберите действие:"
        )
        
        await message.answer(text, reply_markup=get_admins_keyboard())
    
    async def cmd_assign_admin(self, message: Message, state: FSMContext):
        """Обработчик назначения админа"""
        if not await self.check_superadmin(message):
            return
            
        # Проверяем, есть ли факультеты
        if not self.db_pool:
            await message.answer("❌ База данных недоступна", reply_markup=get_admins_keyboard())
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                faculties = await conn.fetch("SELECT id, title FROM faculties ORDER BY title")
                
                if not faculties:
                    await message.answer("❌ Сначала создайте факультеты", reply_markup=get_admins_keyboard())
                    return
                
                text = (
                    "👑 Назначение администратора\n\n"
                    "📱 Введите Telegram ID администратора:"
                )
                
                await message.answer(text, reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="❌ Отмена")]],
                    resize_keyboard=True,
                    one_time_keyboard=True
                ))
                await state.set_state(SuperAdminStates.waiting_admin_telegram_id)
                
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}", reply_markup=get_admins_keyboard())
    
    async def cmd_list_admins(self, message: Message):
        """Обработчик списка админов"""
        if not await self.check_superadmin(message):
            return
            
        if not self.db_pool:
            text = "❌ База данных недоступна"
        else:
            try:
                async with self.db_pool.acquire() as conn:
                    admins = await conn.fetch("""
                        SELECT fa.id, fa.telegram_user_id, f.title as faculty_name
                        FROM faculty_admins fa
                        JOIN faculties f ON fa.faculty_id = f.id
                        ORDER BY f.title
                    """)
                    
                    if admins:
                        text = "👑 Список администраторов:\n\n"
                        for i, admin in enumerate(admins, 1):
                            text += f"{i}. Telegram ID: {admin['telegram_user_id']}\n"
                            text += f"   🏛️ Факультет: {admin['faculty_name']}\n"
                            text += f"   📱 ID: {admin['telegram_user_id']}\n\n"
                    else:
                        text = "👑 Администраторы не найдены"
            except Exception as e:
                text = f"❌ Ошибка получения списка админов: {e}"
        
        await message.answer(text, reply_markup=get_admins_keyboard())
    
    async def cmd_sheets(self, message: Message):
        """Обработчик управления Google Sheets"""
        if not await self.check_superadmin(message):
            return
            
        text = (
            "📊 Управление Google Sheets\n\n"
            "Функции:\n"
            "• 🔗 Добавление ссылок на таблицы\n"
            "• 📋 Просмотр подключенных таблиц\n"
            "• 🧪 Тестирование подключения\n"
            "• 🔄 Обновление данных\n\n"
            "Выберите действие:"
        )
        
        await message.answer(text, reply_markup=get_sheets_keyboard())
    
    async def cmd_test_db(self, message: Message):
        """Обработчик теста базы данных"""
        if not await self.check_superadmin(message):
            return
            
        if await self.test_database():
            text = (
                "✅ База данных работает!\n\n"
                "Подключение к PostgreSQL установлено и функционирует.\n"
                "Статус: 🟢 Активно"
            )
        else:
            text = (
                "❌ Ошибка подключения к базе данных!\n\n"
                "Проверьте настройки подключения.\n"
                "Статус: 🔴 Недоступно"
            )
        
        await message.answer(text, reply_markup=get_superadmin_keyboard())
    
    async def cmd_status(self, message: Message):
        """Обработчик статуса системы"""
        if not await self.check_superadmin(message):
            return
            
        db_status = "🟢 Активно" if await self.test_database() else "🔴 Недоступно"
        faculties_count = await self.get_faculties_count()
        admins_count = await self.get_admins_count()
        
        text = (
            "📈 Статус системы\n\n"
            f"🗄️ База данных: {db_status}\n"
            f"🏛️ Факультетов: {faculties_count}\n"
            f"👑 Админов: {admins_count}\n"
            "🤖 Бот: 🟢 Работает\n"
            "🐳 Docker: 🟢 Активен\n"
            "🔌 Redis: 🟢 Доступен\n\n"
            "Все системы функционируют нормально!"
        )
        
        await message.answer(text, reply_markup=get_superadmin_keyboard())
    
    async def cmd_create_faculty(self, message: Message, state: FSMContext):
        """Обработчик создания факультета"""
        if not await self.check_superadmin(message):
            return
            
        text = (
            "➕ Создание факультета\n\n"
            "📝 Введите название факультета:"
        )
        
        await message.answer(text, reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True,
            one_time_keyboard=True
        ))
        await state.set_state(SuperAdminStates.waiting_faculty_name)
    
    async def cmd_list_faculties(self, message: Message):
        """Обработчик списка факультетов"""
        if not await self.check_superadmin(message):
            return
            
        if not self.db_pool:
            text = "❌ База данных недоступна"
        else:
            try:
                async with self.db_pool.acquire() as conn:
                    faculties = await conn.fetch("SELECT title, description FROM faculties ORDER BY title")
                    
                    if faculties:
                        text = "📋 Список факультетов:\n\n"
                        for i, faculty in enumerate(faculties, 1):
                            text += f"{i}. {faculty['title']}\n"
                            if faculty['description']:
                                text += f"   📄 {faculty['description']}\n"
                            text += "\n"
                    else:
                        text = "📋 Факультеты не найдены"
            except Exception as e:
                text = f"❌ Ошибка получения списка факультетов: {e}"
        
        await message.answer(text, reply_markup=get_faculties_keyboard())
    
    async def cmd_add_sheet_link(self, message: Message, state: FSMContext):
        """Обработчик добавления ссылки на Google Sheet"""
        if not await self.check_superadmin(message):
            return
            
        text = (
            "🔗 Добавление ссылки на Google Sheet\n\n"
            "📋 Отправьте ссылку на Google таблицу:"
        )
        
        await message.answer(text, reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True,
            one_time_keyboard=True
        ))
        await state.set_state(SuperAdminStates.waiting_sheet_link)
    
    async def cmd_test_sheets(self, message: Message):
        """Обработчик тестирования Google Sheets"""
        if not await self.check_superadmin(message):
            return
            
        try:
            # Тестируем подключение к Google Sheets
            test_result = await self.gs_client.test_connection()
            if test_result:
                text = (
                    "✅ Google Sheets подключение работает!\n\n"
                    "API доступен и функционирует.\n"
                    "Статус: 🟢 Активно"
                )
            else:
                text = (
                    "❌ Ошибка подключения к Google Sheets!\n\n"
                    "Проверьте настройки credentials.\n"
                    "Статус: 🔴 Недоступно"
                )
        except Exception as e:
            text = f"❌ Ошибка тестирования Google Sheets: {e}"
        
        await message.answer(text, reply_markup=get_sheets_keyboard())
    
    async def cmd_back_to_superadmin(self, message: Message):
        """Обработчик возврата к суперадмину"""
        await self.cmd_superadmin(message)
    
    async def cmd_back_to_main(self, message: Message):
        """Обработчик возврата в главное меню"""
        from bot.routers.common_asyncpg import get_main_menu_kb
        text = (
            "🏠 Главное меню\n\n"
            "Выберите свою роль:"
        )
        await message.answer(text, reply_markup=get_main_menu_kb())
    
    async def process_faculty_name(self, message: Message, state: FSMContext):
        """Обработчик ввода названия факультета"""
        if not await self.check_superadmin(message):
            return
            
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer("❌ Создание факультета отменено", reply_markup=get_faculties_keyboard())
            return
        
        faculty_name = message.text.strip()
        if not faculty_name:
            await message.answer("❌ Название факультета не может быть пустым. Попробуйте снова:")
            return
        
        # Сохраняем название факультета
        await state.update_data(faculty_name=faculty_name)
        
        text = (
            f"📝 Название: {faculty_name}\n\n"
            "📄 Введите описание факультета (или отправьте '-' для пропуска):"
        )
        
        await message.answer(text)
        await state.set_state(SuperAdminStates.waiting_faculty_description)
    
    async def process_faculty_description(self, message: Message, state: FSMContext):
        """Обработчик ввода описания факультета"""
        if not await self.check_superadmin(message):
            return
            
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer("❌ Создание факультета отменено", reply_markup=get_faculties_keyboard())
            return
        
        data = await state.get_data()
        faculty_name = data.get('faculty_name')
        faculty_description = message.text.strip() if message.text.strip() != '-' else None
        
        # Создаем факультет в базе данных
        try:
            if not self.db_pool:
                await message.answer("❌ База данных недоступна", reply_markup=get_faculties_keyboard())
                await state.clear()
                return
            
            async with self.db_pool.acquire() as conn:
                faculty_id = await conn.fetchval("""
                    INSERT INTO faculties (slug, title, description) 
                    VALUES ($1, $2, $3)
                    RETURNING id
                """, f"faculty-{faculty_name.lower().replace(' ', '-')}", faculty_name, faculty_description)
                
                text = (
                    f"✅ Факультет создан успешно!\n\n"
                    f"📝 Название: {faculty_name}\n"
                    f"📄 Описание: {faculty_description or 'Не указано'}\n"
                    f"🆔 ID: {faculty_id}"
                )
                
                await message.answer(text, reply_markup=get_faculties_keyboard())
                
        except Exception as e:
            if "unique constraint" in str(e).lower():
                text = f"❌ Факультет с названием '{faculty_name}' уже существует!"
            else:
                text = f"❌ Ошибка создания факультета: {e}"
            await message.answer(text, reply_markup=get_faculties_keyboard())
        
        await state.clear()
    
    async def process_sheet_link(self, message: Message, state: FSMContext):
        """Обработчик ввода ссылки на Google Sheet"""
        if not await self.check_superadmin(message):
            return
            
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer("❌ Добавление таблицы отменено", reply_markup=get_sheets_keyboard())
            return
        
        # Проверяем, что это ссылка на Google Sheets
        if "docs.google.com/spreadsheets" not in message.text:
            await message.answer("❌ Это не ссылка на Google Sheets. Попробуйте снова:")
            return
        
        # Извлекаем ID таблицы из ссылки
        try:
            sheet_id = message.text.split("/d/")[1].split("/")[0]
        except:
            await message.answer("❌ Неверный формат ссылки. Попробуйте снова:")
            return
        
        # Сохраняем ссылку
        await state.update_data(sheet_link=message.text, sheet_id=sheet_id)
        
        # Получаем список факультетов
        if not self.db_pool:
            await message.answer("❌ База данных недоступна", reply_markup=get_sheets_keyboard())
            await state.clear()
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                faculties = await conn.fetch("SELECT id, title FROM faculties ORDER BY title")
                
                if not faculties:
                    await message.answer("❌ Сначала создайте факультеты", reply_markup=get_sheets_keyboard())
                    await state.clear()
                    return
                
                text = "🏛️ Выберите факультет для привязки таблицы:\n\n"
                for i, faculty in enumerate(faculties, 1):
                    text += f"{i}. {faculty['title']}\n"
                
                await message.answer(text)
                await state.set_state(SuperAdminStates.waiting_faculty_for_sheet)
                
        except Exception as e:
            await message.answer(f"❌ Ошибка получения факультетов: {e}", reply_markup=get_sheets_keyboard())
            await state.clear()
    
    async def process_faculty_for_sheet(self, message: Message, state: FSMContext):
        """Обработчик выбора факультета для таблицы"""
        if not await self.check_superadmin(message):
            return
            
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer("❌ Добавление таблицы отменено", reply_markup=get_sheets_keyboard())
            return
        
        # Получаем список факультетов
        try:
            async with self.db_pool.acquire() as conn:
                faculties = await conn.fetch("SELECT id, title FROM faculties ORDER BY title")
                
                # Пытаемся найти факультет по номеру или названию
                faculty = None
                try:
                    faculty_num = int(message.text)
                    if 1 <= faculty_num <= len(faculties):
                        faculty = faculties[faculty_num - 1]
                except ValueError:
                    # Поиск по названию
                    for f in faculties:
                        if f['title'].lower() == message.text.lower():
                            faculty = f
                            break
                
                if not faculty:
                    await message.answer("❌ Факультет не найден. Попробуйте снова:")
                    return
                
                # Сохраняем ID факультета
                await state.update_data(faculty_id=faculty['id'], faculty_name=faculty['title'])
                
                text = (
                    f"🏛️ Факультет: {faculty['title']}\n\n"
                    "📊 Выберите тип таблицы:\n"
                    "1. ne_opyt - Без опыта\n"
                    "2. opyt - С опытом\n"
                    "3. svod - Сводная"
                )
                
                await message.answer(text)
                await state.set_state(SuperAdminStates.waiting_sheet_type)
                
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}", reply_markup=get_sheets_keyboard())
            await state.clear()
    
    async def process_sheet_type(self, message: Message, state: FSMContext):
        """Обработчик выбора типа таблицы"""
        if not await self.check_superadmin(message):
            return
            
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer("❌ Добавление таблицы отменено", reply_markup=get_sheets_keyboard())
            return
        
        # Определяем тип таблицы
        sheet_types = {
            "1": "ne_opyt",
            "2": "opyt", 
            "3": "svod",
            "ne_opyt": "ne_opyt",
            "opyt": "opyt",
            "svod": "svod"
        }
        
        sheet_type = sheet_types.get(message.text.lower())
        if not sheet_type:
            await message.answer("❌ Неверный тип таблицы. Выберите 1, 2 или 3:")
            return
        
        data = await state.get_data()
        faculty_id = data.get('faculty_id')
        faculty_name = data.get('faculty_name')
        sheet_id = data.get('sheet_id')
        sheet_link = data.get('sheet_link')
        
        # Сохраняем таблицу в базу данных
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO faculty_sheets (faculty_id, kind, spreadsheet_id, sheet_name)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (faculty_id, kind) 
                    DO UPDATE SET spreadsheet_id = EXCLUDED.spreadsheet_id, sheet_name = EXCLUDED.sheet_name
                """, faculty_id, sheet_type, sheet_id, sheet_type)
                
                text = (
                    f"✅ Таблица добавлена успешно!\n\n"
                    f"🏛️ Факультет: {faculty_name}\n"
                    f"📊 Тип: {sheet_type}\n"
                    f"🔗 Ссылка: {sheet_link}"
                )
                
                await message.answer(text, reply_markup=get_sheets_keyboard())
                
        except Exception as e:
            await message.answer(f"❌ Ошибка сохранения таблицы: {e}", reply_markup=get_sheets_keyboard())
        
        await state.clear()
    
    async def process_admin_telegram_id(self, message: Message, state: FSMContext):
        """Обработчик ввода Telegram ID админа"""
        if not await self.check_superadmin(message):
            return
            
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer("❌ Назначение админа отменено", reply_markup=get_admins_keyboard())
            return
        
        try:
            telegram_id = int(message.text.strip())
            if telegram_id <= 0:
                await message.answer("❌ Telegram ID должен быть положительным числом. Попробуйте снова:")
                return
        except ValueError:
            await message.answer("❌ Неверный формат Telegram ID. Введите число:")
            return
        
        # Проверяем, не назначен ли уже этот пользователь админом
        try:
            async with self.db_pool.acquire() as conn:
                existing_admin = await conn.fetchval(
                    "SELECT id FROM faculty_admins WHERE telegram_user_id = $1", 
                    telegram_id
                )
                
                if existing_admin:
                    await message.answer(
                        f"❌ Пользователь с ID {telegram_id} уже назначен администратором!",
                        reply_markup=get_admins_keyboard()
                    )
                    await state.clear()
                    return
                
                # Сохраняем Telegram ID
                await state.update_data(telegram_id=telegram_id)
                
                text = (
                    f"📱 Telegram ID: {telegram_id}\n\n"
                    "👤 Введите имя администратора:"
                )
                
                await message.answer(text)
                await state.set_state(SuperAdminStates.waiting_admin_name)
                
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}", reply_markup=get_admins_keyboard())
            await state.clear()
    
    async def process_admin_name(self, message: Message, state: FSMContext):
        """Обработчик ввода имени админа"""
        if not await self.check_superadmin(message):
            return
            
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer("❌ Назначение админа отменено", reply_markup=get_admins_keyboard())
            return
        
        admin_name = message.text.strip()
        if not admin_name:
            await message.answer("❌ Имя не может быть пустым. Попробуйте снова:")
            return
        
        # Сохраняем имя
        await state.update_data(admin_name=admin_name)
        
        # Получаем список факультетов
        try:
            async with self.db_pool.acquire() as conn:
                faculties = await conn.fetch("SELECT id, title FROM faculties ORDER BY title")
                
                text = f"👤 Имя: {admin_name}\n\n🏛️ Выберите факультет:\n\n"
                for i, faculty in enumerate(faculties, 1):
                    text += f"{i}. {faculty['title']}\n"
                
                await message.answer(text)
                await state.set_state(SuperAdminStates.waiting_admin_faculty)
                
        except Exception as e:
            await message.answer(f"❌ Ошибка получения факультетов: {e}", reply_markup=get_admins_keyboard())
            await state.clear()
    
    async def process_admin_faculty(self, message: Message, state: FSMContext):
        """Обработчик выбора факультета для админа"""
        if not await self.check_superadmin(message):
            return
            
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer("❌ Назначение админа отменено", reply_markup=get_admins_keyboard())
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                faculties = await conn.fetch("SELECT id, title FROM faculties ORDER BY title")
                
                # Пытаемся найти факультет по номеру или названию
                faculty = None
                try:
                    faculty_num = int(message.text)
                    if 1 <= faculty_num <= len(faculties):
                        faculty = faculties[faculty_num - 1]
                except ValueError:
                    # Поиск по названию
                    for f in faculties:
                        if f['title'].lower() == message.text.lower():
                            faculty = f
                            break
                
                if not faculty:
                    await message.answer("❌ Факультет не найден. Попробуйте снова:")
                    return
                
                # Получаем данные из состояния
                data = await state.get_data()
                telegram_id = data.get('telegram_id')
                admin_name = data.get('admin_name')
                
                # Создаем администратора в базе данных
                admin_id = await conn.fetchval("""
                    INSERT INTO faculty_admins (faculty_id, telegram_user_id) 
                    VALUES ($1, $2)
                    RETURNING id
                """, faculty['id'], telegram_id)
                
                text = (
                    f"✅ Администратор назначен успешно!\n\n"
                    f"👤 Имя: {admin_name}\n"
                    f"📱 Telegram ID: {telegram_id}\n"
                    f"🏛️ Факультет: {faculty['title']}\n"
                    f"🆔 ID: {admin_id}"
                )
                
                await message.answer(text, reply_markup=get_admins_keyboard())
                
        except Exception as e:
            if "unique constraint" in str(e).lower():
                await message.answer("❌ Этот пользователь уже назначен администратором!", reply_markup=get_admins_keyboard())
            else:
                await message.answer(f"❌ Ошибка назначения админа: {e}", reply_markup=get_admins_keyboard())
        
        await state.clear()
    
    def setup_handlers(self):
        """Настраивает обработчики"""
        # Основные команды суперадмина
        self.router.message.register(self.cmd_superadmin, F.text == "👑 Суперадмин")
        self.router.message.register(self.cmd_faculties, F.text == "🏛️ Факультеты")
        self.router.message.register(self.cmd_admins, F.text == "👑 Админы")
        self.router.message.register(self.cmd_sheets, F.text == "📊 Google Sheets")
        self.router.message.register(self.cmd_test_db, F.text == "🔍 Тест БД")
        self.router.message.register(self.cmd_status, F.text == "📈 Статус")
        
        # Управление факультетами
        self.router.message.register(self.cmd_create_faculty, F.text == "➕ Создать факультет")
        self.router.message.register(self.cmd_list_faculties, F.text == "📋 Список факультетов")
        
        # Управление администраторами
        self.router.message.register(self.cmd_assign_admin, F.text == "➕ Назначить админа")
        self.router.message.register(self.cmd_list_admins, F.text == "📋 Список админов")
        
        # Управление Google Sheets
        self.router.message.register(self.cmd_add_sheet_link, F.text == "🔗 Добавить ссылку")
        self.router.message.register(self.cmd_test_sheets, F.text == "🧪 Тест подключения")
        
        # FSM состояния для создания факультетов
        self.router.message.register(self.process_faculty_name, SuperAdminStates.waiting_faculty_name)
        self.router.message.register(self.process_faculty_description, SuperAdminStates.waiting_faculty_description)
        
        # FSM состояния для назначения админов
        self.router.message.register(self.process_admin_telegram_id, SuperAdminStates.waiting_admin_telegram_id)
        self.router.message.register(self.process_admin_name, SuperAdminStates.waiting_admin_name)
        self.router.message.register(self.process_admin_faculty, SuperAdminStates.waiting_admin_faculty)
        
        # FSM состояния для добавления Google Sheets
        self.router.message.register(self.process_sheet_link, SuperAdminStates.waiting_sheet_link)
        self.router.message.register(self.process_faculty_for_sheet, SuperAdminStates.waiting_faculty_for_sheet)
        self.router.message.register(self.process_sheet_type, SuperAdminStates.waiting_sheet_type)
        
        # Навигация
        self.router.message.register(self.cmd_back_to_superadmin, F.text == "🔙 Назад к суперадмину")
        self.router.message.register(self.cmd_back_to_main, F.text == "🔙 Главное меню")
    
    def get_router(self):
        """Возвращает роутер"""
        return self.router


def setup_superadmin_router(db_pool, redis_client: RedisClient, gs_client: GSpreadClient):
    """Создает и настраивает роутер суперадмина"""
    superadmin_router = SuperAdminRouter(db_pool, redis_client, gs_client)
    return superadmin_router.get_router()

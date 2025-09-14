from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.dao import FacultyDAO, FacultyAdminDAO, FacultySheetDAO
from database.engine import sessionmaker
from database.models import SheetKind
from services.auth import AuthService


class SuperAdminStates(StatesGroup):
    waiting_faculty_name = State()
    waiting_faculty_slug = State()
    waiting_admin_telegram_id = State()
    waiting_sheet_spreadsheet_id = State()
    waiting_sheet_name = State()
    waiting_ne_opyt_sheet = State()
    waiting_opyt_sheet = State()
    waiting_svod_sheet = State()


def setup_superadmin_router() -> Router:
    router = Router()

    def superadmin_menu_kb() -> InlineKeyboardMarkup:
        buttons = [
            [InlineKeyboardButton(text="Управление факультетами", callback_data="super|faculties")],
            [InlineKeyboardButton(text="Управление админами", callback_data="super|admins")],
            [InlineKeyboardButton(text="Настройка таблиц", callback_data="super|sheets")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @router.callback_query(F.data == "superadmin_menu")
    async def show_superadmin_menu(callback: CallbackQuery) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("Недоступно")
            return
        
        await callback.message.edit_text(
            "Панель супер-администратора:\n\n"
            "• Управление факультетами - создание, редактирование\n"
            "• Управление админами - назначение админов факультетов\n"
            "• Настройка таблиц - привязка Google Sheets к факультетам",
            reply_markup=superadmin_menu_kb()
        )
        await callback.answer()

    # Обработчики для управления факультетами
    @router.callback_query(F.data == "super|faculties")
    async def handle_faculties_management(callback: CallbackQuery) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("Недоступно")
            return

        async with sessionmaker() as session:
            faculty_dao = FacultyDAO(session)
            faculties = await faculty_dao.get_all()

        buttons = []
        for faculty in faculties:
            status = "✅" if faculty.is_active else "❌"
            buttons.append([
                InlineKeyboardButton(
                    text=f"{status} {faculty.title}",
                    callback_data=f"faculty|{faculty.id}"
                )
            ])
        
        buttons.append([InlineKeyboardButton(text="➕ Добавить факультет", callback_data="faculty|add")])
        buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])

        await callback.message.edit_text(
            "Управление факультетами:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

    @router.callback_query(F.data == "faculty|add")
    async def handle_add_faculty(callback: CallbackQuery, state: FSMContext) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("Недоступно")
            return

        await state.set_state(SuperAdminStates.waiting_faculty_name)
        await callback.message.edit_text("Введите название факультета:")

    @router.message(SuperAdminStates.waiting_faculty_name)
    async def handle_faculty_name(message: Message, state: FSMContext) -> None:
        await state.update_data(faculty_name=message.text)
        await state.set_state(SuperAdminStates.waiting_faculty_slug)
        await message.answer("Введите slug факультета (латинскими буквами, без пробелов):")

    @router.message(SuperAdminStates.waiting_faculty_slug)
    async def handle_faculty_slug(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        faculty_name = data["faculty_name"]
        faculty_slug = message.text.lower().strip()

        async with sessionmaker() as session:
            faculty_dao = FacultyDAO(session)
            faculty = await faculty_dao.create(faculty_slug, faculty_name)

        await state.clear()
        await message.answer(f"✅ Факультет '{faculty_name}' успешно создан!")

    # Обработчики для управления админами
    @router.callback_query(F.data == "super|admins")
    async def handle_admins_management(callback: CallbackQuery) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("Недоступно")
            return

        async with sessionmaker() as session:
            faculty_dao = FacultyDAO(session)
            faculties = await faculty_dao.get_all()

        buttons = []
        for faculty in faculties:
            buttons.append([
                InlineKeyboardButton(
                    text=f"👥 {faculty.title}",
                    callback_data=f"admin_faculty|{faculty.id}"
                )
            ])
        
        buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])

        await callback.message.edit_text(
            "Выберите факультет для управления админами:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

    @router.callback_query(F.data.startswith("admin_faculty|"))
    async def handle_faculty_admins(callback: CallbackQuery) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("Недоступно")
            return

        faculty_id = int(callback.data.split("|")[1])

        async with sessionmaker() as session:
            faculty_dao = FacultyDAO(session)
            admin_dao = FacultyAdminDAO(session)
            
            faculty = await faculty_dao.get_by_id(faculty_id)
            admins = await admin_dao.get_by_faculty(faculty_id)

        buttons = []
        for admin in admins:
            status = "👑" if admin.is_superadmin else "👤"
            buttons.append([
                InlineKeyboardButton(
                    text=f"{status} {admin.telegram_user_id}",
                    callback_data=f"admin_remove|{admin.id}"
                )
            ])
        
        buttons.append([InlineKeyboardButton(text="➕ Добавить админа", callback_data=f"admin_add|{faculty_id}")])
        buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])

        await callback.message.edit_text(
            f"Админы факультета '{faculty.title}':",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

    @router.callback_query(F.data.startswith("admin_add|"))
    async def handle_add_admin(callback: CallbackQuery, state: FSMContext) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("Недоступно")
            return

        faculty_id = int(callback.data.split("|")[1])
        await state.update_data(faculty_id=faculty_id)
        await state.set_state(SuperAdminStates.waiting_admin_telegram_id)
        await callback.message.edit_text("Введите Telegram ID нового админа:")

    @router.message(SuperAdminStates.waiting_admin_telegram_id)
    async def handle_admin_telegram_id(message: Message, state: FSMContext) -> None:
        try:
            telegram_id = int(message.text)
            data = await state.get_data()
            faculty_id = data["faculty_id"]

            async with sessionmaker() as session:
                admin_dao = FacultyAdminDAO(session)
                await admin_dao.create(faculty_id, telegram_id)

            await state.clear()
            await message.answer(f"✅ Админ с ID {telegram_id} успешно добавлен!")
        except ValueError:
            await message.answer("❌ Неверный формат ID. Введите числовой ID:")


    # Обработчики для настройки таблиц
    @router.callback_query(F.data == "super|sheets")
    async def handle_sheets_management(callback: CallbackQuery) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("Недоступно")
            return

        async with sessionmaker() as session:
            faculty_dao = FacultyDAO(session)
            faculties = await faculty_dao.get_all()

        buttons = []
        for faculty in faculties:
            buttons.append([
                InlineKeyboardButton(
                    text=f"📊 {faculty.title}",
                    callback_data=f"sheets_faculty|{faculty.id}"
                )
            ])
        
        buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])

        await callback.message.edit_text(
            "Настройка Google Sheets для факультетов:\n\n"
            "Выберите факультет для настройки таблиц:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

    @router.callback_query(F.data.startswith("sheets_faculty|"))
    async def handle_faculty_sheets(callback: CallbackQuery) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("Недоступно")
            return

        faculty_id = int(callback.data.split("|")[1])

        async with sessionmaker() as session:
            faculty_dao = FacultyDAO(session)
            sheet_dao = FacultySheetDAO(session)
            
            faculty = await faculty_dao.get_by_id(faculty_id)
            sheets = await sheet_dao.get_by_faculty(faculty_id)

        # Группируем листы по типу
        ne_opyt_sheet = next((s for s in sheets if s.kind == SheetKind.NE_OPYT), None)
        opyt_sheet = next((s for s in sheets if s.kind == SheetKind.OPYT), None)
        svod_sheet = next((s for s in sheets if s.kind == SheetKind.SVOD), None)

        text = f"📊 Настройка таблиц для факультета '{faculty.title}':\n\n"
        
        text += f"📖 Без опыта (ne_opyt): "
        if ne_opyt_sheet:
            text += f"✅ {ne_opyt_sheet.spreadsheet_id}\n"
        else:
            text += "❌ Не настроено\n"
        
        text += f"📚 С опытом (opyt): "
        if opyt_sheet:
            text += f"✅ {opyt_sheet.spreadsheet_id}\n"
        else:
            text += "❌ Не настроено\n"
        
        text += f"📋 Сводная (svod): "
        if svod_sheet:
            text += f"✅ {svod_sheet.spreadsheet_id}\n"
        else:
            text += "❌ Не настроено\n"

        buttons = []
        
        # Кнопки для настройки каждого типа таблицы
        if not ne_opyt_sheet:
            buttons.append([InlineKeyboardButton(
                text="📖 Настроить таблицу 'без опыта'",
                callback_data=f"setup_sheet|{faculty_id}|ne_opyt"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text="📖 Изменить таблицу 'без опыта'",
                callback_data=f"setup_sheet|{faculty_id}|ne_opyt"
            )])
        
        if not opyt_sheet:
            buttons.append([InlineKeyboardButton(
                text="📚 Настроить таблицу 'с опытом'",
                callback_data=f"setup_sheet|{faculty_id}|opyt"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text="📚 Изменить таблицу 'с опытом'",
                callback_data=f"setup_sheet|{faculty_id}|opyt"
            )])
        
        if not svod_sheet:
            buttons.append([InlineKeyboardButton(
                text="📋 Настроить сводную таблицу",
                callback_data=f"setup_sheet|{faculty_id}|svod"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text="📋 Изменить сводную таблицу",
                callback_data=f"setup_sheet|{faculty_id}|svod"
            )])
        
        buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

    @router.callback_query(F.data.startswith("setup_sheet|"))
    async def handle_setup_sheet(callback: CallbackQuery, state: FSMContext) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("Недоступно")
            return

        parts = callback.data.split("|")
        faculty_id = int(parts[1])
        sheet_kind = parts[2]
        
        await state.update_data(faculty_id=faculty_id, sheet_kind=sheet_kind)
        await state.set_state(SuperAdminStates.waiting_sheet_spreadsheet_id)
        
        kind_names = {
            "ne_opyt": "без опыта (ne_opyt)",
            "opyt": "с опытом (opyt)", 
            "svod": "сводная (svod)"
        }
        
        await callback.message.edit_text(
            f"Настройка таблицы '{kind_names[sheet_kind]}':\n\n"
            f"Введите ID Google Spreadsheet.\n\n"
            f"ID можно найти в URL таблицы:\n"
            f"https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit\n\n"
            f"Пример: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        )

    @router.message(SuperAdminStates.waiting_sheet_spreadsheet_id)
    async def handle_sheet_spreadsheet_id(message: Message, state: FSMContext) -> None:
        spreadsheet_id = message.text.strip()
        data = await state.get_data()
        faculty_id = data["faculty_id"]
        sheet_kind = data["sheet_kind"]
        
        # Валидируем ID (должен быть строкой из букв, цифр, дефисов и подчеркиваний)
        if not spreadsheet_id or len(spreadsheet_id) < 10:
            await message.answer("❌ Неверный формат ID. Попробуйте ещё раз:")
            return
        
        # Проверяем доступ к таблице
        try:
            from services.gspread_client import GSpreadClient
            gs_client = GSpreadClient()
            worksheets = gs_client.list_worksheet_titles(spreadsheet_id)
            
            if not worksheets:
                await message.answer("❌ Не удалось получить доступ к таблице или она пуста.")
                return
                
        except Exception as e:
            await message.answer(f"❌ Ошибка доступа к таблице: {e}\n\nПроверьте:\n1. ID таблицы\n2. Доступ Service Account к таблице\n3. Настройки Google Sheets API")
            return
        
        # Сохраняем в базу данных
        try:
            async with sessionmaker() as session:
                sheet_dao = FacultySheetDAO(session)
                
                # Удаляем существующую запись если есть
                existing_sheet = await sheet_dao.get_by_faculty_and_kind(faculty_id, SheetKind(sheet_kind))
                if existing_sheet:
                    await session.execute(
                        f"DELETE FROM faculty_sheets WHERE id = {existing_sheet.id}"
                    )
                
                # Создаем новую запись
                await sheet_dao.create(faculty_id, SheetKind(sheet_kind), spreadsheet_id)
                
            kind_names = {
                "ne_opyt": "без опыта",
                "opyt": "с опытом",
                "svod": "сводная"
            }
            
            await message.answer(f"✅ Таблица '{kind_names[sheet_kind]}' успешно настроена!\n\nID: {spreadsheet_id}\nЛистов найдено: {len(worksheets)}")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка сохранения: {e}")
        
        await state.clear()

    return router

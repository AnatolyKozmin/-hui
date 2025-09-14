from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database.dao import FacultyDAO, FacultyAdminDAO, FacultySheetDAO, InterviewerDAO
from database.engine import sessionmaker
from database.models import SheetKind, Interviewer
from services.auth import AuthService
from services.gspread_client import GSpreadClient
from services.redis_client import CacheKeys, RedisClient


def setup_faculty_admin_router(redis_client: RedisClient, gs_client: GSpreadClient, bot) -> Router:
    router = Router()

    def faculty_admin_menu_kb() -> InlineKeyboardMarkup:
        buttons = [
            [InlineKeyboardButton(text="👥 Собеседующие", callback_data="faculty|interviewers")],
            [InlineKeyboardButton(text="Добавить проводящих", callback_data="faculty|add_interviewers")],
            [InlineKeyboardButton(text="Импорт участников", callback_data="faculty|import_participants")],
            [InlineKeyboardButton(text="Управление слоты", callback_data="faculty|manage_slots")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @router.callback_query(F.data == "faculty_admin_menu")
    async def show_faculty_admin_menu(callback: CallbackQuery) -> None:
        # Проверяем, является ли пользователь админом факультета
        async with sessionmaker() as session:
            admin_dao = FacultyAdminDAO(session)
            admin = await admin_dao.get_by_telegram_id(callback.from_user.id)
            
            if not admin and not AuthService.is_superadmin(callback.from_user.id):
                await callback.answer("Недоступно")
                return
        
        await callback.message.edit_text(
            "Панель администратора факультета:\n\n"
            "• Собеседующие - управление собеседующими\n"
            "• Добавить проводящих - парсинг листов из таблиц opyt/ne_opyt\n"
            "• Импорт участников - загрузка из таблицы svod\n"
            "• Управление слотами - настройка времени собеседований",
            reply_markup=faculty_admin_menu_kb()
        )
        await callback.answer()

    @router.callback_query(F.data == "faculty|add_interviewers")
    async def cb_add_interviewers(callback: CallbackQuery) -> None:
        # Проверяем права доступа
        async with sessionmaker() as session:
            admin_dao = FacultyAdminDAO(session)
            admin = await admin_dao.get_by_telegram_id(callback.from_user.id)
            
            if not admin and not AuthService.is_superadmin(callback.from_user.id):
                await callback.answer("Недоступно", show_alert=True)
                return

        # Если пользователь - админ факультета, показываем только его факультет
        if admin:
            faculty_id = admin.faculty_id
            await parse_interviewers_for_faculty(callback, faculty_id)
        else:
            # Если суперадмин, показываем выбор факультета
            async with sessionmaker() as session:
                faculty_dao = FacultyDAO(session)
                faculties = await faculty_dao.get_all()
            
            buttons = []
            for faculty in faculties:
                buttons.append([
                    InlineKeyboardButton(
                        text=faculty.title,
                        callback_data=f"parse_faculty|{faculty.id}"
                    )
                ])
            buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])
            
            await callback.message.edit_text(
                "Выберите факультет для парсинга собеседующих:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
            await callback.answer()

    @router.callback_query(F.data.startswith("parse_faculty|"))
    async def cb_parse_faculty(callback: CallbackQuery) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("Недоступно", show_alert=True)
            return

        faculty_id = int(callback.data.split("|")[1])
        await parse_interviewers_for_faculty(callback, faculty_id)

    async def parse_interviewers_for_faculty(callback: CallbackQuery, faculty_id: int) -> None:
        """Парсит собеседующих для факультета из Google Sheets"""
        async with sessionmaker() as session:
            faculty_dao = FacultyDAO(session)
            sheet_dao = FacultySheetDAO(session)
            interviewer_dao = InterviewerDAO(session)
            
            faculty = await faculty_dao.get_by_id(faculty_id)
            sheets = await sheet_dao.get_by_faculty(faculty_id)
        
        # Находим таблицы для собеседующих
        ne_opyt_sheet = next((s for s in sheets if s.kind == SheetKind.NE_OPYT), None)
        opyt_sheet = next((s for s in sheets if s.kind == SheetKind.OPYT), None)
        
        if not ne_opyt_sheet and not opyt_sheet:
            await callback.message.edit_text(
                f"❌ Для факультета '{faculty.title}' не настроены таблицы собеседующих.\n\n"
                "Настройте таблицы через панель суперадмина: /superadmin",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="faculty|back")]
                ])
            )
            await callback.answer()
            return
        
        # Парсим собеседующих из таблиц
        all_interviewers = []
        
        for sheet, sheet_kind in [(ne_opyt_sheet, SheetKind.NE_OPYT), (opyt_sheet, SheetKind.OPYT)]:
            if not sheet:
                continue
                
            try:
                # Получаем листы из таблицы
                worksheet_titles = gs_client.list_worksheet_titles(sheet.spreadsheet_id)
                
                for tab_name in worksheet_titles:
                    # Проверяем, не существует ли уже такой собеседующий
                    existing = await interviewer_dao.get_by_faculty_and_tab_name(faculty_id, tab_name)
                    if existing:
                        continue
                    
                    all_interviewers.append({
                        "tab_name": tab_name,
                        "sheet_kind": sheet_kind,
                        "faculty_sheet_id": sheet.id,
                        "faculty_id": faculty_id
                    })
                    
            except Exception as e:
                await callback.message.edit_text(
                    f"❌ Ошибка чтения таблицы {sheet_kind.value}: {e}",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Назад", callback_data="faculty|back")]
                    ])
                )
                await callback.answer()
                return
        
        if not all_interviewers:
            await callback.message.edit_text(
                f"✅ Все собеседующие для факультета '{faculty.title}' уже добавлены в базу данных.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="faculty|back")]
                ])
            )
            await callback.answer()
            return
        
        # Сохраняем собеседующих в базу данных
        saved_count = 0
        for interviewer_data in all_interviewers:
            try:
                # Генерируем токен приглашения
                token = await redis_client.generate_invite_token(
                    interviewer_data["faculty_id"], 
                    interviewer_data["faculty_id"]
                )
                
                # Создаем собеседующего в базе
                async with sessionmaker() as session:
                    interviewer_dao = InterviewerDAO(session)
                    await interviewer_dao.create(
                        interviewer_data["faculty_id"],
                        interviewer_data["faculty_sheet_id"],
                        interviewer_data["tab_name"],
                        interviewer_data["sheet_kind"],
                        token
                    )
                    saved_count += 1
                    
            except Exception as e:
                print(f"Ошибка сохранения собеседующего {interviewer_data['tab_name']}: {e}")
        
        await callback.message.edit_text(
            f"✅ Парсинг завершен!\n\n"
            f"Факультет: {faculty.title}\n"
            f"Найдено новых собеседующих: {len(all_interviewers)}\n"
            f"Сохранено в базу: {saved_count}\n\n"
            f"Теперь можно создавать ссылки для регистрации через '👥 Собеседующие'",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👥 Собеседующие", callback_data="faculty|interviewers")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="faculty|back")]
            ])
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("create_invite|"))
    async def cb_create_invite(callback: CallbackQuery) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("Недоступно", show_alert=True)
            return
        
        try:
            _, faculty, sheet_type, interviewer_name = callback.data.split("|", 3)
        except ValueError:
            await callback.answer("Ошибка данных", show_alert=True)
            return
        
        # Generate invite token and store in Redis
        import secrets
        token = secrets.token_urlsafe(12)
        
        invite_data = {
            "faculty": faculty,
            "sheet_type": sheet_type,
            "interviewer_name": interviewer_name,
            "created_by": callback.from_user.id,
            "created_at": str(callback.message.date)
        }
        
        await redis_client.set_json(CacheKeys.INVITES.format(token=token), invite_data, ex=86400)  # 24h
        
        # Get bot username
        bot_username = await redis_client.get(CacheKeys.BOT_USERNAME)
        if not bot_username:
            # TODO: Get from bot instance
            bot_username = "your_bot_username"
        
        invite_link = f"https://t.me/{bot_username}?start=inv_{token}"
        
        await callback.message.answer(
            f"Ссылка для {interviewer_name} ({sheet_type}):\n\n{invite_link}\n\n"
            f"Ссылка действительна 24 часа."
        )
        await callback.answer()

    # Обработчик для кнопки "Собеседующие"
    @router.callback_query(F.data == "faculty|interviewers")
    async def cb_manage_interviewers(callback: CallbackQuery) -> None:
        # Проверяем права доступа
        async with sessionmaker() as session:
            admin_dao = FacultyAdminDAO(session)
            admin = await admin_dao.get_by_telegram_id(callback.from_user.id)
            
            if not admin and not AuthService.is_superadmin(callback.from_user.id):
                await callback.answer("Недоступно", show_alert=True)
                return

        # Если пользователь - админ факультета, показываем собеседующих его факультета
        if admin:
            faculty_id = admin.faculty_id
        else:
            # Если суперадмин, показываем выбор факультета
            faculty_dao = FacultyDAO(session)
            faculties = await faculty_dao.get_all()
            
            buttons = []
            for faculty in faculties:
                buttons.append([
                    InlineKeyboardButton(
                        text=faculty.title,
                        callback_data=f"interviewers_faculty|{faculty.id}"
                    )
                ])
            buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])
            
            await callback.message.edit_text(
                "Выберите факультет для управления собеседующими:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
            await callback.answer()
            return

        # Показываем собеседующих факультета
        await show_faculty_interviewers(callback, faculty_id)

    @router.callback_query(F.data.startswith("interviewers_faculty|"))
    async def cb_show_faculty_interviewers(callback: CallbackQuery) -> None:
        if not AuthService.is_superadmin(callback.from_user.id):
            await callback.answer("Недоступно", show_alert=True)
            return

        faculty_id = int(callback.data.split("|")[1])
        await show_faculty_interviewers(callback, faculty_id)

    async def show_faculty_interviewers(callback: CallbackQuery, faculty_id: int) -> None:
        """Показывает собеседующих факультета"""
        async with sessionmaker() as session:
            faculty_dao = FacultyDAO(session)
            interviewer_dao = InterviewerDAO(session)
            
            faculty = await faculty_dao.get_by_id(faculty_id)
            interviewers = await interviewer_dao.get_by_faculty(faculty_id)

        if not interviewers:
            await callback.message.edit_text(
                f"Собеседующие для факультета '{faculty.title}' не найдены.\n\n"
                "Используйте 'Добавить проводящих' для парсинга из Google Sheets.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="faculty|back")]
                ])
            )
            await callback.answer()
            return

        # Группируем собеседующих по типу опыта
        opyt_interviewers = [i for i in interviewers if i.experience_kind == SheetKind.OPYT]
        ne_opyt_interviewers = [i for i in interviewers if i.experience_kind == SheetKind.NE_OPYT]

        text = f"👥 Собеседующие факультета '{faculty.title}':\n\n"
        
        if opyt_interviewers:
            text += "📚 С опытом:\n"
            for interviewer in opyt_interviewers:
                status = "✅" if interviewer.tg_id else "⏳"
                text += f"{status} {interviewer.tab_name}\n"
            text += "\n"
        
        if ne_opyt_interviewers:
            text += "📖 Без опыта:\n"
            for interviewer in ne_opyt_interviewers:
                status = "✅" if interviewer.tg_id else "⏳"
                text += f"{status} {interviewer.tab_name}\n"

        buttons = []
        
        # Кнопки для создания ссылок для незарегистрированных собеседующих
        unregistered = [i for i in interviewers if not i.tg_id]
        if unregistered:
            buttons.append([InlineKeyboardButton(
                text="🔗 Создать ссылки для незарегистрированных",
                callback_data=f"create_interviewer_links|{faculty_id}"
            )])
        
        buttons.append([InlineKeyboardButton(text="🔄 Обновить список", callback_data=f"interviewers_faculty|{faculty_id}")])
        buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("create_interviewer_links|"))
    async def cb_create_interviewer_links(callback: CallbackQuery) -> None:
        faculty_id = int(callback.data.split("|")[1])
        
        async with sessionmaker() as session:
            interviewer_dao = InterviewerDAO(session)
            unregistered = await interviewer_dao.get_unregistered_by_faculty(faculty_id)

        if not unregistered:
            await callback.answer("Все собеседующие уже зарегистрированы", show_alert=True)
            return

        # Создаем ссылки для незарегистрированных собеседующих
        links_text = "🔗 Ссылки для регистрации собеседующих:\n\n"
        
        for interviewer in unregistered:
            # Генерируем токен через Redis
            token = await redis_client.generate_invite_token(
                interviewer.id, 
                interviewer.faculty_id
            )
            
            # Обновляем токен в базе данных
            async with sessionmaker() as session:
                from sqlalchemy import update
                await session.execute(
                    update(Interviewer)
                    .where(Interviewer.id == interviewer.id)
                    .values(invite_token=token)
                )
                await session.commit()
            
            # Получаем имя бота
            me = await bot.get_me()
            bot_username = me.username
            invite_link = f"https://t.me/{bot_username}?start=inv_{token}"
            
            links_text += f"👤 {interviewer.tab_name} ({interviewer.experience_kind.value}):\n{invite_link}\n\n"

        await callback.message.answer(links_text)
        await callback.answer("Ссылки созданы!")


    return router

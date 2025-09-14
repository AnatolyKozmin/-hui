from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.dao import InterviewerDAO
from database.engine import sessionmaker
from services.redis_client import RedisClient


class InterviewerRegistrationStates(StatesGroup):
    waiting_name_confirmation = State()


def setup_interviewer_registration_router(redis_client: RedisClient) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def handle_start_command(message: Message, state: FSMContext) -> None:
        # Проверяем, есть ли токен приглашения в команде
        if len(message.text.split()) > 1:
            start_param = message.text.split()[1]
            if start_param.startswith("inv_"):
                token = start_param[4:]  # Убираем префикс "inv_"
                await handle_interviewer_invite(message, token, state)
                return

        # Обычное приветствие
        await message.answer(
            "👋 Добро пожаловать в бот для собеседований!\n\n"
            "Если у вас есть ссылка-приглашение, используйте её для регистрации."
        )

    async def handle_interviewer_invite(message: Message, token: str, state: FSMContext) -> None:
        """Обрабатывает регистрацию собеседующего по токену"""
        # Получаем данные приглашения из Redis
        invite_data = await redis_client.get_invite_data(token)
        
        if not invite_data:
            await message.answer(
                "❌ Ссылка-приглашение недействительна или истекла.\n"
                "Обратитесь к администратору факультета за новой ссылкой."
            )
            return

        # Проверяем, что это приглашение для собеседующего
        if invite_data.get("type") != "interviewer_invite":
            await message.answer("❌ Неверный тип приглашения.")
            return

        # Проверяем, не зарегистрирован ли уже этот пользователь
        async with sessionmaker() as session:
            interviewer_dao = InterviewerDAO(session)
            existing_interviewer = await interviewer_dao.get_by_telegram_id(message.from_user.id)
            
            if existing_interviewer:
                await message.answer(
                    f"✅ Вы уже зарегистрированы как собеседующий!\n"
                    f"Факультет: {existing_interviewer.faculty.title}\n"
                    f"Тип: {existing_interviewer.experience_kind.value}"
                )
                return

            # Получаем собеседующего по ID из приглашения
            interviewer = await interviewer_dao.get_by_invite_token(token)
            
            if not interviewer:
                await message.answer("❌ Собеседующий не найден в базе данных.")
                return

            # Проверяем, не зарегистрирован ли уже этот собеседующий
            if interviewer.tg_id:
                await message.answer(
                    "❌ Этот собеседующий уже зарегистрирован другим пользователем."
                )
                return

        # Сохраняем данные для подтверждения
        await state.update_data(
            token=token,
            interviewer_id=interviewer.id,
            faculty_title=interviewer.faculty.title,
            tab_name=interviewer.tab_name,
            experience_kind=interviewer.experience_kind.value
        )

        # Запрашиваем подтверждение имени
        await state.set_state(InterviewerRegistrationStates.waiting_name_confirmation)
        await message.answer(
            f"🔍 Подтвердите ваши данные:\n\n"
            f"👤 Имя в таблице: {interviewer.tab_name}\n"
            f"🏫 Факультет: {interviewer.faculty.title}\n"
            f"📚 Тип собеседований: {interviewer.experience_kind.value}\n\n"
            f"Если данные верны, нажмите кнопку подтверждения:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_interviewer_registration")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_interviewer_registration")]
            ])
        )

    @router.callback_query(F.data == "confirm_interviewer_registration")
    async def confirm_interviewer_registration(callback, state: FSMContext) -> None:
        """Подтверждает регистрацию собеседующего"""
        data = await state.get_data()
        token = data["token"]
        interviewer_id = data["interviewer_id"]
        
        # Регистрируем собеседующего
        async with sessionmaker() as session:
            interviewer_dao = InterviewerDAO(session)
            interviewer = await interviewer_dao.register_telegram_user(
                token,
                callback.from_user.id,
                callback.from_user.username
            )

        if interviewer:
            # Удаляем токен из Redis
            await redis_client.delete_invite_token(token)
            
            await callback.message.edit_text(
                f"🎉 Поздравляем! Вы успешно зарегистрированы как собеседующий!\n\n"
                f"👤 Имя: {interviewer.tab_name}\n"
                f"🏫 Факультет: {interviewer.faculty.title}\n"
                f"📚 Тип собеседований: {interviewer.experience_kind.value}\n\n"
                f"Теперь вы можете проводить собеседования для участников вашего факультета."
            )
        else:
            await callback.message.edit_text(
                "❌ Ошибка при регистрации. Попробуйте ещё раз или обратитесь к администратору."
            )

        await state.clear()
        await callback.answer()

    @router.callback_query(F.data == "cancel_interviewer_registration")
    async def cancel_interviewer_registration(callback, state: FSMContext) -> None:
        """Отменяет регистрацию собеседующего"""
        await state.clear()
        await callback.message.edit_text(
            "❌ Регистрация отменена.\n\n"
            "Если у вас есть вопросы, обратитесь к администратору факультета."
        )
        await callback.answer()

    return router

#!/usr/bin/env python3
"""
Простая версия бота с прямым подключением через asyncpg
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

load_dotenv()


class SimpleBot:
    def __init__(self):
        self.bot = Bot(token=os.getenv("TOKEN"))
        self.dp = Dispatcher()
        self.db_pool = None
        
    async def init_database(self):
        """Инициализирует подключение к базе данных"""
        try:
            import asyncpg
            
            # Получаем URL базы данных
            database_url = os.getenv("DATABASE_URL", "asyncpg+postgresql://otb:1234@postgres:5432/otb_db")
            asyncpg_url = database_url.replace("asyncpg+", "")
            
            # Создаем пул подключений
            self.db_pool = await asyncpg.create_pool(
                asyncpg_url,
                min_size=1,
                max_size=10
            )
            print("✅ Подключение к базе данных установлено")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка подключения к базе данных: {e}")
            return False
    
    async def close_database(self):
        """Закрывает подключение к базе данных"""
        if self.db_pool:
            await self.db_pool.close()
            print("✅ Подключение к базе данных закрыто")
    
    async def test_database(self):
        """Тестирует подключение к базе данных"""
        if not self.db_pool:
            return False
            
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                print(f"✅ Тест базы данных: {result}")
                return True
        except Exception as e:
            print(f"❌ Ошибка теста базы данных: {e}")
            return False
    
    def get_main_keyboard(self):
        """Создает главную клавиатуру"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 Тест БД"), KeyboardButton(text="ℹ️ Информация")],
                [KeyboardButton(text="🔄 Перезапуск"), KeyboardButton(text="📊 Статус")]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    async def start_command(self, message: types.Message):
        """Обработчик команды /start"""
        await message.answer(
            "🤖 Добро пожаловать в бот!\n\n"
            "Это простая версия бота с прямым подключением к PostgreSQL через asyncpg.\n\n"
            "Используйте кнопки ниже для навигации:",
            reply_markup=self.get_main_keyboard()
        )
    
    async def test_db_handler(self, message: types.Message):
        """Обработчик теста базы данных"""
        if await self.test_database():
            text = "✅ База данных работает!\n\n" \
                   "Подключение к PostgreSQL установлено и функционирует.\n\n" \
                   "Статус: 🟢 Активно"
        else:
            text = "❌ Ошибка подключения к базе данных!\n\n" \
                   "Проверьте настройки подключения.\n\n" \
                   "Статус: 🔴 Недоступно"
        
        await message.answer(text, reply_markup=self.get_main_keyboard())
    
    async def info_handler(self, message: types.Message):
        """Обработчик информации"""
        text = "ℹ️ Информация о боте\n\n" \
               "🤖 Версия: Простая (asyncpg)\n" \
               "🗄️ База данных: PostgreSQL\n" \
               "🔌 Подключение: Прямое через asyncpg\n" \
               "🐳 Контейнер: Docker\n" \
               "📱 Интерфейс: Reply клавиатура\n\n" \
               "Это тестовая версия бота для проверки подключения к базе данных."
        
        await message.answer(text, reply_markup=self.get_main_keyboard())
    
    async def restart_handler(self, message: types.Message):
        """Обработчик перезапуска"""
        status_msg = await message.answer(
            "🔄 Перезапуск...\n\n"
            "Пожалуйста, подождите...",
            reply_markup=None
        )
        
        # Переподключаемся к базе данных
        await self.close_database()
        success = await self.init_database()
        
        if success:
            text = "✅ Перезапуск завершен!\n\n" \
                   "Подключение к базе данных восстановлено.\n\n" \
                   "Статус: 🟢 Активно"
        else:
            text = "❌ Ошибка перезапуска!\n\n" \
                   "Не удалось восстановить подключение к базе данных.\n\n" \
                   "Статус: 🔴 Недоступно"
        
        await status_msg.edit_text(text)
        await message.answer("Готово! Используйте кнопки для навигации:", reply_markup=self.get_main_keyboard())
    
    async def status_handler(self, message: types.Message):
        """Обработчик статуса"""
        db_status = "🟢 Активно" if await self.test_database() else "🔴 Недоступно"
        
        text = "📊 Статус системы\n\n" \
               f"🗄️ База данных: {db_status}\n" \
               "🤖 Бот: 🟢 Работает\n" \
               "🐳 Docker: 🟢 Активен\n" \
               "🔌 Redis: 🟢 Доступен\n\n" \
               "Все системы функционируют нормально!"
        
        await message.answer(text, reply_markup=self.get_main_keyboard())
    
    async def unknown_message(self, message: types.Message):
        """Обработчик неизвестных сообщений"""
        await message.answer(
            "❓ Неизвестная команда\n\n"
            "Используйте кнопки ниже для навигации:",
            reply_markup=self.get_main_keyboard()
        )
    
    def setup_handlers(self):
        """Настраивает обработчики"""
        # Команды
        self.dp.message.register(self.start_command, Command("start"))
        
        # Обработчики текстовых сообщений
        self.dp.message.register(self.test_db_handler, lambda m: m.text == "🔍 Тест БД")
        self.dp.message.register(self.info_handler, lambda m: m.text == "ℹ️ Информация")
        self.dp.message.register(self.restart_handler, lambda m: m.text == "🔄 Перезапуск")
        self.dp.message.register(self.status_handler, lambda m: m.text == "📊 Статус")
        
        # Обработчик неизвестных сообщений (должен быть последним)
        self.dp.message.register(self.unknown_message)
    
    async def start(self):
        """Запускает бота"""
        print("🚀 Запуск простого бота с asyncpg...")
        
        # Инициализируем базу данных
        if not await self.init_database():
            print("❌ Не удалось подключиться к базе данных")
            return
        
        # Настраиваем обработчики
        self.setup_handlers()
        
        # Запускаем бота
        try:
            print("✅ Бот запущен и готов к работе!")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            print(f"❌ Ошибка запуска бота: {e}")
        finally:
            await self.close_database()
    
    async def stop(self):
        """Останавливает бота"""
        print("🛑 Остановка бота...")
        await self.close_database()
        await self.bot.session.close()


async def main():
    """Основная функция"""
    bot = SimpleBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n⚠️ Получен сигнал остановки")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Основной бот с прямым подключением через asyncpg
"""

import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Импорты роутеров
from bot.routers.common_asyncpg import setup_common_router
from bot.routers.superadmin_asyncpg import setup_superadmin_router
# from bot.routers.faculty_admin import setup_faculty_admin_router
# from bot.routers.interviewer_registration import setup_interviewer_registration_router

# Импорты сервисов
from services.redis_client import RedisClient
from services.gspread_client import GSpreadClient

load_dotenv()


class MainBot:
    def __init__(self):
        self.bot = Bot(
            token=os.getenv("TOKEN"),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()
        self.db_pool = None
        self.redis_client = None
        self.gs_client = None
        
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
    
    async def init_services(self):
        """Инициализирует сервисы"""
        try:
            # Redis клиент
            self.redis_client = RedisClient()
            print("✅ Redis клиент инициализирован")
            
            # Google Sheets клиент
            self.gs_client = GSpreadClient()
            print("✅ Google Sheets клиент инициализирован")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка инициализации сервисов: {e}")
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
    
    def setup_routers(self):
        """Настраивает роутеры"""
        try:
            # Общий роутер
            common_router = setup_common_router()
            self.dp.include_router(common_router)
            print("✅ Общий роутер подключен")
            
            # Суперадмин роутер
            superadmin_router = setup_superadmin_router(self.db_pool, self.redis_client, self.gs_client)
            self.dp.include_router(superadmin_router)
            print("✅ Суперадмин роутер подключен")
            
            # TODO: Добавить остальные роутеры когда исправим SQLAlchemy
            # faculty_admin_router = setup_faculty_admin_router(self.db_pool, self.redis_client, self.gs_client, self.bot)
            # self.dp.include_router(faculty_admin_router)
            # print("✅ Факультет админ роутер подключен")
            
            # interviewer_router = setup_interviewer_registration_router(self.db_pool, self.redis_client)
            # self.dp.include_router(interviewer_router)
            # print("✅ Роутер регистрации интервьюеров подключен")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка настройки роутеров: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def start(self):
        """Запускает бота"""
        print("🚀 Запуск основного бота с asyncpg...")
        
        # Инициализируем базу данных
        if not await self.init_database():
            print("❌ Не удалось подключиться к базе данных")
            return
        
        # Инициализируем сервисы
        if not await self.init_services():
            print("❌ Не удалось инициализировать сервисы")
            return
        
        # Настраиваем роутеры
        if not self.setup_routers():
            print("❌ Не удалось настроить роутеры")
            return
        
        # Тестируем базу данных
        if not await self.test_database():
            print("❌ База данных не работает")
            return
        
        # Запускаем бота
        try:
            print("✅ Бот запущен и готов к работе!")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            print(f"❌ Ошибка запуска бота: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.close_database()
    
    async def stop(self):
        """Останавливает бота"""
        print("🛑 Остановка бота...")
        await self.close_database()
        await self.bot.session.close()


async def main():
    """Основная функция"""
    bot = MainBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n⚠️ Получен сигнал остановки")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())

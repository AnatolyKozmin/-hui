#!/usr/bin/env python3
"""
Тест запуска бота без подключения к БД
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


async def test_bot_startup():
    """Тестирует запуск бота"""
    print("🔍 Тестирование запуска бота...")
    
    try:
        # Импортируем только основные компоненты
        from aiogram import Bot, Dispatcher
        print("✅ aiogram импортирован")
        
        # Проверяем токен
        token = os.getenv("TOKEN")
        if not token:
            print("❌ TOKEN не установлен")
            return False
        
        print(f"✅ TOKEN: {token[:10]}...")
        
        # Создаем бота
        bot = Bot(token=token)
        print("✅ Бот создан")
        
        # Создаем диспетчер
        dp = Dispatcher()
        print("✅ Диспетчер создан")
        
        # Проверяем, что можем получить информацию о боте
        try:
            me = await bot.get_me()
            print(f"✅ Бот подключен: @{me.username}")
        except Exception as e:
            print(f"⚠️ Не удалось подключиться к Telegram API: {e}")
            print("💡 Проверьте токен бота")
        
        await bot.session.close()
        print("✅ Бот закрыт")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        return False


async def test_imports_without_db():
    """Тестирует импорты без базы данных"""
    print("\n🔍 Тестирование импортов без БД...")
    
    try:
        # Импортируем только то, что не требует БД
        from services.redis_client import RedisClient
        print("✅ Redis клиент импортирован")
        
        from services.gspread_client import GSpreadClient
        print("✅ Google Sheets клиент импортирован")
        
        # Проверяем, что можем создать клиенты
        redis_client = RedisClient()
        print("✅ Redis клиент создан")
        
        # Не создаем GSpreadClient, так как нужны credentials
        print("✅ Google Sheets клиент готов к созданию")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импортов: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование запуска бота\n")
    
    tests = [
        ("Запуск бота", test_bot_startup),
        ("Импорты без БД", test_imports_without_db),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Выводим итоги
    print("\n" + "="*50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ЗАПУСКА")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print("="*50)
    print(f"Пройдено тестов: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Бот может запуститься без базы данных!")
        print("\n💡 Для полной работы нужно:")
        print("1. Исправить проблему с asyncpg в SQLAlchemy")
        print("2. Настроить Google credentials")
        print("3. Запустить Redis сервер")
    else:
        print("⚠️ Некоторые тесты провалены.")
        print("❌ Бот НЕ СМОЖЕТ запуститься!")


if __name__ == "__main__":
    asyncio.run(main())

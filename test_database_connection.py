#!/usr/bin/env python3
"""
Тест подключения к базе данных
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


async def test_database_connection():
    """Тестирует подключение к базе данных"""
    print("🔍 Тестирование подключения к базе данных...")
    
    try:
        # Проверяем переменные окружения
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL не установлен")
            return False
        
        print(f"✅ DATABASE_URL: {database_url}")
        
        # Проверяем, что asyncpg установлен
        import asyncpg
        print("✅ asyncpg импортирован успешно")
        
        # Пытаемся подключиться к базе данных
        try:
            # asyncpg использует схему postgresql://, а не asyncpg+postgresql://
            asyncpg_url = database_url.replace("asyncpg+", "")
            conn = await asyncpg.connect(asyncpg_url)
            print("✅ Подключение к базе данных успешно!")
            
            # Проверяем, что можем выполнить запрос
            result = await conn.fetchval("SELECT 1")
            print(f"✅ Запрос выполнен: {result}")
            
            await conn.close()
            print("✅ Соединение закрыто")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка подключения к базе данных: {e}")
            print("\n💡 Возможные причины:")
            print("1. PostgreSQL сервер не запущен")
            print("2. Неправильные данные подключения")
            print("3. База данных не существует")
            print("4. Пользователь не имеет прав доступа")
            return False
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False


async def test_sqlalchemy_connection():
    """Тестирует подключение через SQLAlchemy"""
    print("\n🔍 Тестирование подключения через SQLAlchemy...")
    
    try:
        from database.engine import sessionmaker
        
        async with sessionmaker() as session:
            # Простой запрос для проверки подключения
            result = await session.execute("SELECT 1")
            print("✅ SQLAlchemy подключение работает!")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка SQLAlchemy подключения: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование подключения к базе данных\n")
    
    # Тест 1: Прямое подключение через asyncpg
    db_test = await test_database_connection()
    
    # Тест 2: Подключение через SQLAlchemy
    sqlalchemy_test = await test_sqlalchemy_connection()
    
    print("\n" + "="*50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ БД")
    print("="*50)
    
    if db_test:
        print("✅ Прямое подключение asyncpg: РАБОТАЕТ")
    else:
        print("❌ Прямое подключение asyncpg: НЕ РАБОТАЕТ")
    
    if sqlalchemy_test:
        print("✅ SQLAlchemy подключение: РАБОТАЕТ")
    else:
        print("❌ SQLAlchemy подключение: НЕ РАБОТАЕТ")
    
    if db_test and sqlalchemy_test:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ База данных готова к работе!")
        print("✅ Бот может запуститься!")
    else:
        print("\n⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        print("❌ Бот НЕ СМОЖЕТ запуститься!")
        print("\n🔧 Что нужно сделать:")
        if not db_test:
            print("1. Запустите PostgreSQL сервер")
            print("2. Создайте базу данных 'otb_db'")
            print("3. Создайте пользователя 'otb' с паролем '1234'")
            print("4. Дайте пользователю права на базу данных")
        if not sqlalchemy_test:
            print("5. Проверьте настройки SQLAlchemy")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Тест asyncpg в Docker контейнере
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_asyncpg_direct():
    """Тестирует прямое подключение через asyncpg"""
    print("🔍 Тестирование прямого подключения через asyncpg...")
    
    try:
        import asyncpg
        print("✅ asyncpg импортирован")
        
        # Получаем URL базы данных
        database_url = os.getenv("DATABASE_URL", "asyncpg+postgresql://otb:1234@postgres:5432/otb_db")
        print(f"URL: {database_url}")
        
        # Конвертируем URL для asyncpg
        asyncpg_url = database_url.replace("asyncpg+", "")
        print(f"AsyncPG URL: {asyncpg_url}")
        
        # Пытаемся подключиться
        conn = await asyncpg.connect(asyncpg_url)
        print("✅ Прямое подключение через asyncpg работает!")
        
        # Тестируем запрос
        result = await conn.fetchval("SELECT 1")
        print(f"✅ Запрос выполнен: {result}")
        
        await conn.close()
        print("✅ Соединение закрыто")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка прямого подключения: {e}")
        return False


async def test_sqlalchemy_async():
    """Тестирует SQLAlchemy с asyncpg"""
    print("\n🔍 Тестирование SQLAlchemy с asyncpg...")
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        print("✅ create_async_engine импортирован")
        
        database_url = os.getenv("DATABASE_URL", "asyncpg+postgresql://otb:1234@postgres:5432/otb_db")
        print(f"URL: {database_url}")
        
        # Пытаемся создать движок
        engine = create_async_engine(database_url, echo=True)
        print("✅ Асинхронный движок создан!")
        
        # Тестируем подключение
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print(f"✅ Запрос через SQLAlchemy выполнен: {result.scalar()}")
        
        await engine.dispose()
        print("✅ Движок закрыт")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка SQLAlchemy: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_sqlalchemy_sync():
    """Тестирует синхронный SQLAlchemy с psycopg2"""
    print("\n🔍 Тестирование синхронного SQLAlchemy с psycopg2...")
    
    try:
        from sqlalchemy import create_engine
        print("✅ create_engine импортирован")
        
        # Используем psycopg2 для синхронного подключения
        sync_url = "postgresql+psycopg2://otb:1234@postgres:5432/otb_db"
        print(f"Sync URL: {sync_url}")
        
        # Пытаемся создать движок
        engine = create_engine(sync_url, echo=True)
        print("✅ Синхронный движок создан!")
        
        # Тестируем подключение
        with engine.begin() as conn:
            result = conn.execute("SELECT 1")
            print(f"✅ Запрос через синхронный SQLAlchemy выполнен: {result.scalar()}")
        
        engine.dispose()
        print("✅ Синхронный движок закрыт")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка синхронного SQLAlchemy: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Основная функция тестирования"""
    print("🐳 Тестирование asyncpg в Docker контейнере\n")
    
    tests = [
        ("Прямое подключение asyncpg", test_asyncpg_direct),
        ("SQLAlchemy async", test_sqlalchemy_async),
        ("SQLAlchemy sync", test_sqlalchemy_sync),
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
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ASYNCPG В DOCKER")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
    
    print("="*60)
    print(f"Пройдено тестов: {passed}/{len(results)}")
    
    if passed > 0:
        print("🎉 НЕКОТОРЫЕ ТЕСТЫ ПРОЙДЕНЫ!")
        if results[0][1]:  # Прямое подключение работает
            print("✅ Прямое подключение к PostgreSQL работает!")
            print("💡 Можно использовать прямое подключение вместо SQLAlchemy")
        if results[2][1]:  # Синхронный SQLAlchemy работает
            print("✅ Синхронный SQLAlchemy работает!")
            print("💡 Можно использовать синхронный SQLAlchemy для миграций")
    else:
        print("❌ ВСЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        print("❌ Проблема с подключением к базе данных!")


if __name__ == "__main__":
    asyncio.run(main())

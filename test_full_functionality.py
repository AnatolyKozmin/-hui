#!/usr/bin/env python3
"""
Скрипт для тестирования полного функционала бота
"""

import os
import asyncio
from dotenv import load_dotenv

from database.dao import FacultyDAO, FacultyAdminDAO, FacultySheetDAO, InterviewerDAO
from database.engine import sessionmaker
from database.models import SheetKind
from services.gspread_client import GSpreadClient
from services.redis_client import RedisClient

load_dotenv()


async def test_database_connection():
    """Тестирует подключение к базе данных"""
    print("🔍 Тестирование подключения к базе данных...")
    
    try:
        async with sessionmaker() as session:
            faculty_dao = FacultyDAO(session)
            faculties = await faculty_dao.get_all()
            print(f"✅ Подключение к БД работает. Факультетов в базе: {len(faculties)}")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False


async def test_google_sheets_connection():
    """Тестирует подключение к Google Sheets"""
    print("\n🔍 Тестирование подключения к Google Sheets...")
    
    try:
        gs_client = GSpreadClient()
        print("✅ GSpreadClient создан успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания GSpreadClient: {e}")
        return False


async def test_redis_connection():
    """Тестирует подключение к Redis"""
    print("\n🔍 Тестирование подключения к Redis...")
    
    try:
        redis_client = RedisClient()
        await redis_client.set("test_key", "test_value")
        value = await redis_client.get("test_key")
        await redis_client.delete("test_key")
        
        if value == "test_value":
            print("✅ Подключение к Redis работает")
            return True
        else:
            print("❌ Ошибка работы с Redis")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Redis: {e}")
        return False


async def test_faculty_creation():
    """Тестирует создание факультета"""
    print("\n🔍 Тестирование создания факультета...")
    
    try:
        async with sessionmaker() as session:
            faculty_dao = FacultyDAO(session)
            
            # Создаем тестовый факультет
            faculty = await faculty_dao.create("test_faculty", "Тестовый факультет")
            print(f"✅ Факультет создан: {faculty.title} (ID: {faculty.id})")
            
            # Проверяем, что он сохранился
            retrieved = await faculty_dao.get_by_id(faculty.id)
            if retrieved:
                print(f"✅ Факультет найден в базе: {retrieved.title}")
            
            # Удаляем тестовый факультет
            await faculty_dao.delete(faculty.id)
            print("✅ Тестовый факультет удален")
            
            return True
    except Exception as e:
        print(f"❌ Ошибка тестирования факультетов: {e}")
        return False


async def test_interviewer_creation():
    """Тестирует создание собеседующего"""
    print("\n🔍 Тестирование создания собеседующего...")
    
    try:
        async with sessionmaker() as session:
            faculty_dao = FacultyDAO(session)
            sheet_dao = FacultySheetDAO(session)
            interviewer_dao = InterviewerDAO(session)
            
            # Создаем тестовый факультет
            faculty = await faculty_dao.create("test_interviewer_faculty", "Факультет для тестирования собеседующих")
            
            # Создаем тестовую таблицу
            sheet = await sheet_dao.create(faculty.id, SheetKind.OPYT, "test_spreadsheet_id")
            
            # Создаем собеседующего
            interviewer = await interviewer_dao.create(
                faculty.id, 
                sheet.id, 
                "Тестовый собеседующий", 
                SheetKind.OPYT, 
                "test_token_123"
            )
            
            print(f"✅ Собеседующий создан: {interviewer.tab_name} (ID: {interviewer.id})")
            
            # Проверяем поиск по токену
            found = await interviewer_dao.get_by_invite_token("test_token_123")
            if found:
                print(f"✅ Собеседующий найден по токену: {found.tab_name}")
            
            # Удаляем тестовые данные
            await interviewer_dao.delete(interviewer.id)
            await sheet_dao.delete(sheet.id)
            await faculty_dao.delete(faculty.id)
            print("✅ Тестовые данные удалены")
            
            return True
    except Exception as e:
        print(f"❌ Ошибка тестирования собеседующих: {e}")
        return False


async def test_redis_tokens():
    """Тестирует работу с токенами в Redis"""
    print("\n🔍 Тестирование токенов в Redis...")
    
    try:
        redis_client = RedisClient()
        
        # Генерируем тестовый токен
        token = await redis_client.generate_invite_token(1, 1)
        print(f"✅ Токен сгенерирован: {token[:20]}...")
        
        # Получаем данные токена
        data = await redis_client.get_invite_data(token)
        if data:
            print(f"✅ Данные токена получены: {data}")
        
        # Удаляем токен
        await redis_client.delete_invite_token(token)
        print("✅ Токен удален")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования токенов: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование полного функционала бота\n")
    
    tests = [
        ("База данных", test_database_connection),
        ("Google Sheets", test_google_sheets_connection),
        ("Redis", test_redis_connection),
        ("Создание факультетов", test_faculty_creation),
        ("Создание собеседующих", test_interviewer_creation),
        ("Токены Redis", test_redis_tokens),
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
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
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
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Бот готов к работе!")
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте настройки.")
    
    print("\n📋 Следующие шаги:")
    print("1. Настройте Google Sheets credentials")
    print("2. Создайте факультеты через /superadmin")
    print("3. Настройте таблицы для факультетов")
    print("4. Запустите парсинг собеседующих")
    print("5. Создайте ссылки для регистрации")


if __name__ == "__main__":
    asyncio.run(main())

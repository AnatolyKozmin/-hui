#!/usr/bin/env python3
"""
Базовый тест функционала без подключения к БД
"""

import os
from dotenv import load_dotenv

load_dotenv()


def test_environment_variables():
    """Тестирует переменные окружения"""
    print("🔍 Проверка переменных окружения...")
    
    required_vars = ["TOKEN", "DATABASE_URL"]
    optional_vars = ["GOOGLE_CREDENTIALS_JSON", "REDIS_URL"]
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: установлен")
        else:
            print(f"❌ {var}: не установлен")
            all_good = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: установлен")
        else:
            print(f"⚠️ {var}: не установлен (опционально)")
    
    return all_good


def test_imports():
    """Тестирует импорты модулей"""
    print("\n🔍 Проверка импортов...")
    
    try:
        from database.models import Faculty, Interviewer, SheetKind
        print("✅ Модели базы данных импортированы")
    except Exception as e:
        print(f"❌ Ошибка импорта моделей: {e}")
        return False
    
    try:
        from database.dao import FacultyDAO, InterviewerDAO
        print("✅ DAO классы импортированы")
    except Exception as e:
        print(f"❌ Ошибка импорта DAO: {e}")
        return False
    
    try:
        from services.redis_client import RedisClient
        print("✅ Redis клиент импортирован")
    except Exception as e:
        print(f"❌ Ошибка импорта Redis: {e}")
        return False
    
    try:
        from services.gspread_client import GSpreadClient
        print("✅ Google Sheets клиент импортирован")
    except Exception as e:
        print(f"❌ Ошибка импорта Google Sheets: {e}")
        return False
    
    try:
        from bot.routers.superadmin import setup_superadmin_router
        from bot.routers.faculty_admin import setup_faculty_admin_router
        from bot.routers.interviewer_registration import setup_interviewer_registration_router
        print("✅ Роутеры бота импортированы")
    except Exception as e:
        print(f"❌ Ошибка импорта роутеров: {e}")
        return False
    
    return True


def test_google_credentials():
    """Тестирует наличие Google credentials"""
    print("\n🔍 Проверка Google credentials...")
    
    creds_path = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not creds_path:
        print("⚠️ GOOGLE_CREDENTIALS_JSON не установлен")
        return False
    
    if os.path.exists(creds_path):
        print(f"✅ Файл credentials найден: {creds_path}")
        return True
    else:
        print(f"❌ Файл credentials не найден: {creds_path}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Базовое тестирование функционала бота\n")
    
    tests = [
        ("Переменные окружения", test_environment_variables),
        ("Импорты модулей", test_imports),
        ("Google credentials", test_google_credentials),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Выводим итоги
    print("\n" + "="*50)
    print("📊 РЕЗУЛЬТАТЫ БАЗОВОГО ТЕСТИРОВАНИЯ")
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
        print("🎉 БАЗОВЫЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("\n📋 Следующие шаги:")
        print("1. Настройте Google Cloud Console")
        print("2. Создайте google_credentials.json")
        print("3. Исправьте DATABASE_URL в .env (уберите % в конце)")
        print("4. Запустите полное тестирование")
    else:
        print("⚠️ Некоторые базовые тесты провалены.")
        print("Проверьте настройки и зависимости.")


if __name__ == "__main__":
    main()

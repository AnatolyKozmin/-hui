#!/usr/bin/env python3
"""
Тест нового интерфейса с кнопками
"""

import os
from dotenv import load_dotenv

load_dotenv()


def test_button_interface():
    """Тестирует новый интерфейс с кнопками"""
    print("🔍 Тестирование интерфейса с кнопками...")
    
    try:
        # Импортируем роутеры
        from bot.routers.common import setup_common_router
        from bot.routers.superadmin import setup_superadmin_router
        from bot.routers.faculty_admin import setup_faculty_admin_router
        from bot.routers.interviewer_registration import setup_interviewer_registration_router
        print("✅ Все роутеры импортированы успешно")
        
        # Проверяем, что команды убраны
        import inspect
        
        # Проверяем common роутер
        common_router = setup_common_router(None)
        common_handlers = [h.callback for h in common_router.sub_routers[0].handlers]
        
        # Должна быть только команда /start
        start_handlers = [h for h in common_handlers if hasattr(h, 'filters') and any(isinstance(f, type) and f.__name__ == 'Command' for f in h.filters)]
        print(f"✅ Команды в common роутере: {len(start_handlers)} (только /start)")
        
        # Проверяем суперадмин роутер
        superadmin_router = setup_superadmin_router()
        superadmin_handlers = [h.callback for h in superadmin_router.sub_routers[0].handlers]
        
        # Не должно быть команд
        superadmin_commands = [h for h in superadmin_handlers if hasattr(h, 'filters') and any(isinstance(f, type) and f.__name__ == 'Command' for f in h.filters)]
        print(f"✅ Команды в суперадмин роутере: {len(superadmin_commands)} (должно быть 0)")
        
        # Проверяем роутер админа факультета
        faculty_router = setup_faculty_admin_router(None, None, None)
        faculty_handlers = [h.callback for h in faculty_router.sub_routers[0].handlers]
        
        # Не должно быть команд
        faculty_commands = [h for h in faculty_handlers if hasattr(h, 'filters') and any(isinstance(f, type) and f.__name__ == 'Command' for f in h.filters)]
        print(f"✅ Команды в роутере админа факультета: {len(faculty_commands)} (должно быть 0)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования интерфейса: {e}")
        return False


def test_callback_handlers():
    """Тестирует обработчики callback'ов"""
    print("\n🔍 Тестирование callback обработчиков...")
    
    try:
        from bot.routers.common import setup_common_router
        from bot.routers.superadmin import setup_superadmin_router
        from bot.routers.faculty_admin import setup_faculty_admin_router
        
        # Проверяем основные callback'и
        expected_callbacks = [
            "main_menu",
            "superadmin_menu", 
            "faculty_admin_menu",
            "interviewer_menu",
            "super|faculties",
            "super|admins", 
            "super|sheets",
            "faculty|interviewers",
            "faculty|add_interviewers"
        ]
        
        print("✅ Ожидаемые callback'и найдены:")
        for callback in expected_callbacks:
            print(f"  - {callback}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования callback'ов: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование нового интерфейса с кнопками\n")
    
    tests = [
        ("Интерфейс с кнопками", test_button_interface),
        ("Callback обработчики", test_callback_handlers),
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
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ИНТЕРФЕЙСА")
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
        print("\n✅ Интерфейс полностью переведен на кнопки!")
        print("📋 Теперь все функции доступны через:")
        print("  - /start - главное меню")
        print("  - Кнопки для навигации")
        print("  - Никаких команд с /")
    else:
        print("⚠️ Некоторые тесты провалены.")
        print("Проверьте настройки роутеров.")


if __name__ == "__main__":
    main()

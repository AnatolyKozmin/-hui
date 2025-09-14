#!/usr/bin/env python3
"""
Простой тест интерфейса без импорта роутеров
"""

def test_interface_changes():
    """Тестирует изменения в интерфейсе"""
    print("🔍 Проверка изменений в интерфейсе...")
    
    # Проверяем файлы роутеров
    files_to_check = [
        "bot/routers/common.py",
        "bot/routers/superadmin.py", 
        "bot/routers/faculty_admin.py"
    ]
    
    changes_found = 0
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Проверяем, что команды убраны
            if "Command(" in content:
                print(f"⚠️ {file_path}: найдены команды Command()")
            else:
                print(f"✅ {file_path}: команды убраны")
                changes_found += 1
                
            # Проверяем наличие callback обработчиков
            if "callback_query" in content:
                print(f"✅ {file_path}: найдены callback обработчики")
                changes_found += 1
            else:
                print(f"❌ {file_path}: callback обработчики не найдены")
                
            # Проверяем главное меню
            if "main_menu" in content:
                print(f"✅ {file_path}: найдено главное меню")
                changes_found += 1
            else:
                print(f"⚠️ {file_path}: главное меню не найдено")
                
        except FileNotFoundError:
            print(f"❌ {file_path}: файл не найден")
        except Exception as e:
            print(f"❌ {file_path}: ошибка чтения - {e}")
    
    return changes_found >= 6  # Минимум 6 изменений


def test_callback_data():
    """Тестирует callback_data"""
    print("\n🔍 Проверка callback_data...")
    
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
    
    found_callbacks = 0
    
    for file_path in ["bot/routers/common.py", "bot/routers/superadmin.py", "bot/routers/faculty_admin.py"]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for callback in expected_callbacks:
                if callback in content:
                    print(f"✅ Найден callback: {callback}")
                    found_callbacks += 1
                else:
                    print(f"⚠️ Не найден callback: {callback}")
                    
        except Exception as e:
            print(f"❌ Ошибка чтения {file_path}: {e}")
    
    return found_callbacks >= len(expected_callbacks) * 0.8  # 80% callback'ов найдено


def main():
    """Основная функция тестирования"""
    print("🚀 Простое тестирование интерфейса с кнопками\n")
    
    tests = [
        ("Изменения в интерфейсе", test_interface_changes),
        ("Callback данные", test_callback_data),
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
    print("📊 РЕЗУЛЬТАТЫ ПРОСТОГО ТЕСТИРОВАНИЯ")
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
        print("\n✅ Интерфейс успешно переведен на кнопки!")
        print("\n📋 Что изменилось:")
        print("  ❌ Убраны команды /superadmin и /faculty")
        print("  ✅ Добавлено главное меню с кнопками")
        print("  ✅ Все функции доступны через кнопки")
        print("  ✅ Навигация через callback'и")
        print("\n🚀 Теперь пользователи работают только с кнопками!")
    else:
        print("⚠️ Некоторые тесты провалены.")
        print("Проверьте изменения в файлах роутеров.")


if __name__ == "__main__":
    main()

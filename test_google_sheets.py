#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к Google Sheets
"""

import os
import asyncio
from dotenv import load_dotenv

from services.gspread_client import GSpreadClient

load_dotenv()


async def test_google_sheets_connection():
    """Тестирует подключение к Google Sheets"""
    print("🔍 Тестирование подключения к Google Sheets...")
    
    try:
        # Проверяем наличие файла credentials
        creds_path = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not creds_path:
            print("❌ GOOGLE_CREDENTIALS_JSON не установлен в .env файле")
            return False
            
        if not os.path.exists(creds_path):
            print(f"❌ Файл credentials не найден: {creds_path}")
            return False
            
        print(f"✅ Файл credentials найден: {creds_path}")
        
        # Создаем клиент
        gs_client = GSpreadClient()
        print("✅ GSpreadClient создан успешно")
        
        # Тестируем с примером таблицы (замените на реальный ID)
        test_spreadsheet_id = input("Введите ID тестовой Google Sheet (или нажмите Enter для пропуска): ").strip()
        
        if test_spreadsheet_id:
            print(f"🔍 Тестирование с таблицей: {test_spreadsheet_id}")
            
            try:
                # Получаем список листов
                worksheets = gs_client.list_worksheet_titles(test_spreadsheet_id)
                print(f"✅ Найдено листов: {len(worksheets)}")
                for i, title in enumerate(worksheets, 1):
                    print(f"  {i}. {title}")
                
                # Тестируем чтение первого листа
                if worksheets:
                    first_sheet = worksheets[0]
                    print(f"🔍 Читаем лист: {first_sheet}")
                    
                    try:
                        records = gs_client.read_participants(test_spreadsheet_id, first_sheet)
                        print(f"✅ Прочитано записей: {len(records)}")
                        if records:
                            print("📋 Пример записи:")
                            for key, value in records[0].items():
                                print(f"  {key}: {value}")
                    except Exception as e:
                        print(f"⚠️ Ошибка чтения листа: {e}")
                
            except Exception as e:
                print(f"❌ Ошибка доступа к таблице: {e}")
                print("💡 Убедитесь, что:")
                print("  1. Service Account имеет доступ к таблице")
                print("  2. ID таблицы указан правильно")
                print("  3. Google Sheets API включен")
                return False
        else:
            print("⏭️ Тестирование таблицы пропущено")
        
        print("✅ Подключение к Google Sheets работает!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


async def create_test_sheet_structure():
    """Создает пример структуры таблиц для тестирования"""
    print("\n📋 Создание примера структуры таблиц...")
    
    print("""
Для тестирования создайте Google Sheet со следующей структурой:

1. Лист "ne_opyt" (собеседующие без опыта):
   A1: Имя
   B1: ФИО  
   C1: Контакты
   D1: Статус
   
   A2: Иван Петров
   B2: Иван Петрович Петров
   C2: @ivan_petrov
   D2: Активен

2. Лист "opyt" (собеседующие с опытом):
   A1: Имя
   B1: ФИО
   C1: Контакты  
   D1: Статус
   
   A2: Мария Сидорова
   B2: Мария Ивановна Сидорова
   C2: @maria_sid
   D2: Активна

3. Лист "svod" (участники):
   A1: VK ID
   B1: Имя
   C1: Фамилия
   D1: Статус
   
   A2: 123456789
   B2: Иван
   C2: Петров
   D2: Зарегистрирован

После создания:
1. Скопируйте ID таблицы из URL
2. Предоставьте доступ Service Account (email из JSON файла)
3. Запустите тест снова с ID таблицы
""")


if __name__ == "__main__":
    print("🚀 Тестирование Google Sheets интеграции\n")
    
    # Проверяем подключение
    success = asyncio.run(test_google_sheets_connection())
    
    if not success:
        print("\n❌ Тестирование не пройдено")
        print("📖 Следуйте инструкциям в setup_google_sheets.md")
    else:
        print("\n✅ Тестирование пройдено успешно!")
        print("🎉 Google Sheets готов к использованию!")
    
    # Показываем пример структуры
    asyncio.run(create_test_sheet_structure())

#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных в Docker контейнере
"""

import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


async def init_database():
    """Инициализирует базу данных"""
    print("🚀 Инициализация базы данных...")
    
    try:
        # Импортируем компоненты базы данных
        from database.engine import sessionmaker
        from database.models import Base, Faculty, FacultyAdmin, FacultySheet, Participant, Interviewer
        from database.dao import FacultyDAO, FacultyAdminDAO, FacultySheetDAO, InterviewerDAO
        
        print("✅ Модели базы данных импортированы")
        
        # Создаем таблицы
        async with sessionmaker() as session:
            # Создаем все таблицы
            await session.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
            await session.commit()
            print("✅ Расширение UUID создано")
            
            # Создаем таблицы через SQLAlchemy
            from database.engine import engine
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Таблицы созданы")
            
            # Создаем тестовые данные
            faculty_dao = FacultyDAO(session)
            admin_dao = FacultyAdminDAO(session)
            sheet_dao = FacultySheetDAO(session)
            
            # Создаем тестовый факультет
            test_faculty = await faculty_dao.create(
                name="Тестовый факультет",
                description="Факультет для тестирования"
            )
            print(f"✅ Создан тестовый факультет: {test_faculty.name}")
            
            # Создаем тестового админа
            test_admin = await admin_dao.create(
                faculty_id=test_faculty.id,
                telegram_id=123456789,
                name="Тестовый админ"
            )
            print(f"✅ Создан тестовый админ: {test_admin.name}")
            
            # Создаем тестовые листы
            sheet_kinds = ["ne_opyt", "opyt", "svod"]
            for kind in sheet_kinds:
                sheet = await sheet_dao.create(
                    faculty_id=test_faculty.id,
                    kind=kind,
                    spreadsheet_id=f"test_{kind}_sheet_id",
                    sheet_name=f"test_{kind}_sheet"
                )
                print(f"✅ Создан лист {kind}: {sheet.sheet_name}")
            
            await session.commit()
            print("✅ Тестовые данные созданы")
        
        print("🎉 База данных успешно инициализирована!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Основная функция"""
    print("🐳 Инициализация базы данных в Docker контейнере\n")
    
    # Проверяем переменные окружения
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL не установлен")
        return
    
    print(f"✅ DATABASE_URL: {database_url}")
    
    # Инициализируем базу данных
    success = await init_database()
    
    if success:
        print("\n🎉 ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("✅ База данных готова к работе")
        print("✅ Бот может быть запущен")
    else:
        print("\n❌ ОШИБКА ИНИЦИАЛИЗАЦИИ!")
        print("❌ Проверьте настройки базы данных")


if __name__ == "__main__":
    asyncio.run(main())

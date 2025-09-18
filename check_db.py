#!/usr/bin/env python3
"""
Скрипт для проверки состояния базы данных
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import asyncpg

load_dotenv()


async def check_database():
    """Проверяет состояние базы данных"""
    database_url = os.getenv("DATABASE_URL", "asyncpg+postgresql://otb:1234@postgres:5432/otb_db")
    asyncpg_url = database_url.replace("asyncpg+", "")
    
    print("🔍 Проверка состояния базы данных...")
    print(f"URL: {asyncpg_url}")
    
    try:
        conn = await asyncpg.connect(asyncpg_url)
        print("✅ Подключение к базе данных установлено")
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False
    
    try:
        # Проверяем существование таблиц
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"\n📋 Найдено таблиц: {len(tables)}")
        for table in tables:
            print(f"  ✅ {table['table_name']}")
        
        # Проверяем данные в таблицах
        print("\n📊 Проверка данных:")
        
        # Факультеты
        faculties_count = await conn.fetchval("SELECT COUNT(*) FROM faculties")
        print(f"  🏛️ Факультетов: {faculties_count}")
        
        # Админы
        admins_count = await conn.fetchval("SELECT COUNT(*) FROM faculty_admins")
        print(f"  👑 Админов: {admins_count}")
        
        # Листы
        sheets_count = await conn.fetchval("SELECT COUNT(*) FROM faculty_sheets")
        print(f"  📊 Листов: {sheets_count}")
        
        # Собеседующие
        interviewers_count = await conn.fetchval("SELECT COUNT(*) FROM interviewers")
        print(f"  👥 Собеседующих: {interviewers_count}")
        
        # Участники
        participants_count = await conn.fetchval("SELECT COUNT(*) FROM participants")
        print(f"  👤 Участников: {participants_count}")
        
        print("\n✅ База данных готова к работе!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки базы данных: {e}")
        return False
    finally:
        await conn.close()


async def main():
    """Основная функция"""
    print("🔍 Проверка состояния базы данных\n")
    
    success = await check_database()
    
    if success:
        print("\n🎉 БАЗА ДАННЫХ ГОТОВА К РАБОТЕ!")
        sys.exit(0)
    else:
        print("\n❌ ПРОБЛЕМЫ С БАЗОЙ ДАННЫХ!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных в Docker контейнере
Использует прямое подключение через asyncpg
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import asyncpg

# Загружаем переменные окружения
load_dotenv()


async def create_tables():
    """Создает все необходимые таблицы"""
    database_url = os.getenv("DATABASE_URL", "asyncpg+postgresql://otb:1234@postgres:5432/otb_db")
    asyncpg_url = database_url.replace("asyncpg+", "")
    
    print("🔗 Подключение к базе данных...")
    print(f"URL: {asyncpg_url}")
    
    try:
        conn = await asyncpg.connect(asyncpg_url)
        print("✅ Подключение к базе данных установлено")
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False
    
    try:
        # Создаем таблицу faculties
        print("📋 Создание таблицы faculties...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS faculties (
                id SERIAL PRIMARY KEY,
                slug VARCHAR(64) UNIQUE NOT NULL,
                title VARCHAR(256) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем таблицу faculty_admins
        print("📋 Создание таблицы faculty_admins...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS faculty_admins (
                id SERIAL PRIMARY KEY,
                faculty_id INTEGER REFERENCES faculties(id) ON DELETE CASCADE,
                telegram_user_id BIGINT NOT NULL,
                is_superadmin BOOLEAN DEFAULT FALSE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(faculty_id, telegram_user_id)
            )
        """)
        
        # Создаем таблицу faculty_sheets
        print("📋 Создание таблицы faculty_sheets...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS faculty_sheets (
                id SERIAL PRIMARY KEY,
                faculty_id INTEGER REFERENCES faculties(id) ON DELETE CASCADE,
                kind VARCHAR(50) NOT NULL,
                spreadsheet_id VARCHAR(128) NOT NULL,
                sheet_name VARCHAR(128),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(faculty_id, kind)
            )
        """)
        
        # Создаем таблицу participants
        print("📋 Создание таблицы participants...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id SERIAL PRIMARY KEY,
                faculty_id INTEGER REFERENCES faculties(id) ON DELETE CASCADE,
                vk_id BIGINT NOT NULL,
                first_name VARCHAR(128) NOT NULL,
                last_name VARCHAR(128) NOT NULL,
                is_name_verified BOOLEAN DEFAULT FALSE NOT NULL,
                tg_id BIGINT,
                tg_username VARCHAR(64),
                source_sheet_id INTEGER REFERENCES faculty_sheets(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(faculty_id, vk_id)
            )
        """)
        
        # Создаем таблицу interviewers
        print("📋 Создание таблицы interviewers...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS interviewers (
                id SERIAL PRIMARY KEY,
                faculty_id INTEGER REFERENCES faculties(id) ON DELETE CASCADE,
                faculty_sheet_id INTEGER REFERENCES faculty_sheets(id) ON DELETE CASCADE,
                tab_name VARCHAR(128) NOT NULL,
                experience_kind VARCHAR(50) NOT NULL,
                invite_token VARCHAR(64) NOT NULL UNIQUE,
                tg_id BIGINT,
                tg_username VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(faculty_sheet_id, tab_name),
                UNIQUE(tg_id)
            )
        """)
        
        # Создаем индексы для производительности
        print("📊 Создание индексов...")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_faculty_admins_telegram_user_id ON faculty_admins(telegram_user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_interviewers_tg_id ON interviewers(tg_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_interviewers_invite_token ON interviewers(invite_token)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_participants_vk_id ON participants(vk_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_participants_tg_id ON participants(tg_id)")
        
        print("✅ Все таблицы созданы успешно!")
        
        # Проверяем созданные таблицы
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print("\n📋 Созданные таблицы:")
        for table in tables:
            print(f"  ✅ {table['table_name']}")
        
        # Добавляем тестовые данные
        print("\n🌱 Добавление тестовых данных...")
        
        # Создаем тестовый факультет
        faculty_id = await conn.fetchval("""
            INSERT INTO faculties (slug, title) 
            VALUES ('test-faculty', 'Тестовый факультет')
            ON CONFLICT (slug) DO UPDATE SET title = EXCLUDED.title
            RETURNING id
        """)
        
        print(f"✅ Создан тестовый факультет (ID: {faculty_id})")
        
        # Создаем тестового админа
        admin_id = await conn.fetchval("""
            INSERT INTO faculty_admins (faculty_id, telegram_user_id, is_superadmin) 
            VALUES ($1, $2, TRUE)
            ON CONFLICT (faculty_id, telegram_user_id) DO UPDATE SET is_superadmin = EXCLUDED.is_superadmin
            RETURNING id
        """, faculty_id, 922109605)
        
        print(f"✅ Создан тестовый админ (ID: {admin_id})")
        
        # Создаем тестовые листы
        sheet_kinds = ["ne_opyt", "opyt", "svod"]
        for kind in sheet_kinds:
            sheet_id = await conn.fetchval("""
                INSERT INTO faculty_sheets (faculty_id, kind, spreadsheet_id, sheet_name) 
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (faculty_id, kind) DO UPDATE SET spreadsheet_id = EXCLUDED.spreadsheet_id
                RETURNING id
            """, faculty_id, kind, f"test_{kind}_sheet_id", f"test_{kind}_sheet")
            print(f"✅ Создан лист {kind} (ID: {sheet_id})")
        
        print("\n🎉 Инициализация базы данных завершена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await conn.close()


async def main():
    """Основная функция"""
    print("🚀 Инициализация базы данных в Docker контейнере\n")
    
    # Проверяем переменные окружения
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL не установлен")
        sys.exit(1)
    
    print(f"✅ DATABASE_URL: {database_url}")
    
    # Инициализируем базу данных
    success = await create_tables()
    
    if success:
        print("\n🎉 ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("✅ База данных готова к работе")
        print("✅ Бот может быть запущен")
        sys.exit(0)
    else:
        print("\n❌ ОШИБКА ИНИЦИАЛИЗАЦИИ!")
        print("❌ Проверьте настройки базы данных")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

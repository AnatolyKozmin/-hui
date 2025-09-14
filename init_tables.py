#!/usr/bin/env python3
"""
Скрипт для создания таблиц в базе данных
"""

import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()


async def create_tables():
    """Создает все необходимые таблицы"""
    database_url = os.getenv("DATABASE_URL", "asyncpg+postgresql://otb:1234@postgres:5432/otb_db")
    asyncpg_url = database_url.replace("asyncpg+", "")
    
    print("🔗 Подключение к базе данных...")
    conn = await asyncpg.connect(asyncpg_url)
    
    try:
        # Создаем таблицу faculties
        print("📋 Создание таблицы faculties...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS faculties (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
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
                telegram_id BIGINT NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем таблицу faculty_sheets
        print("📋 Создание таблицы faculty_sheets...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS faculty_sheets (
                id SERIAL PRIMARY KEY,
                faculty_id INTEGER REFERENCES faculties(id) ON DELETE CASCADE,
                kind VARCHAR(50) NOT NULL,
                spreadsheet_id VARCHAR(255) NOT NULL,
                sheet_name VARCHAR(255) NOT NULL,
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
                vk_id BIGINT,
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем таблицу interviewers
        print("📋 Создание таблицы interviewers...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS interviewers (
                id SERIAL PRIMARY KEY,
                faculty_id INTEGER REFERENCES faculties(id) ON DELETE CASCADE,
                telegram_id BIGINT,
                name VARCHAR(255) NOT NULL,
                tab_name VARCHAR(255),
                invite_token VARCHAR(255) UNIQUE,
                is_registered BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем индексы для производительности
        print("📊 Создание индексов...")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_faculty_admins_telegram_id ON faculty_admins(telegram_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_interviewers_telegram_id ON interviewers(telegram_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_interviewers_invite_token ON interviewers(invite_token)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_participants_vk_id ON participants(vk_id)")
        
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
            INSERT INTO faculties (name, description) 
            VALUES ('Тестовый факультет', 'Факультет для тестирования системы')
            ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
            RETURNING id
        """)
        
        print(f"✅ Создан тестовый факультет (ID: {faculty_id})")
        
        # Создаем тестового админа
        admin_id = await conn.fetchval("""
            INSERT INTO faculty_admins (faculty_id, telegram_id, name) 
            VALUES ($1, $2, 'Тестовый админ')
            ON CONFLICT (telegram_id) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
        """, faculty_id, 922109605)
        
        print(f"✅ Создан тестовый админ (ID: {admin_id})")
        
        print("\n🎉 Инициализация базы данных завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        raise
    finally:
        await conn.close()


async def main():
    """Основная функция"""
    print("🚀 Инициализация базы данных...")
    await create_tables()


if __name__ == "__main__":
    asyncio.run(main())

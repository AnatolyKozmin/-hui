#!/bin/bash

echo "🚀 Настройка базы данных для бота отбора"
echo "========================================"

# Проверяем, запущен ли Docker Compose
if ! docker-compose ps | grep -q "postgres"; then
    echo "❌ PostgreSQL не запущен. Запускаем Docker Compose..."
    docker-compose up -d postgres redis
    echo "⏳ Ждем запуска PostgreSQL..."
    sleep 10
fi

echo "🔍 Проверяем состояние базы данных..."

# Запускаем инициализацию базы данных
echo "📋 Инициализируем базу данных..."
docker-compose run --rm db-init

if [ $? -eq 0 ]; then
    echo "✅ База данных успешно инициализирована!"
    
    # Проверяем состояние
    echo "🔍 Проверяем состояние базы данных..."
    docker-compose run --rm bot python check_db.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 ВСЕ ГОТОВО К РАБОТЕ!"
        echo "✅ База данных инициализирована"
        echo "✅ Таблицы созданы"
        echo "✅ Тестовые данные добавлены"
        echo ""
        echo "🚀 Теперь можно запустить бота:"
        echo "   docker-compose up bot"
    else
        echo "❌ Проблемы с проверкой базы данных"
        exit 1
    fi
else
    echo "❌ Ошибка инициализации базы данных"
    exit 1
fi

#!/bin/bash

# Скрипт для запуска бота в Docker

echo "🐳 Запуск бота в Docker контейнере"
echo "=================================="

# Проверяем, что Docker установлен
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

# Проверяем, что docker-compose установлен
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose не установлен. Установите docker-compose и попробуйте снова."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден. Создайте файл .env с переменными окружения."
    echo "Пример содержимого .env:"
    echo "TOKEN=your_bot_token_here"
    echo "DATABASE_URL=asyncpg+postgresql://otb:1234@postgres:5432/otb_db"
    echo "REDIS_URL=redis://redis:6379/0"
    echo "GOOGLE_CREDENTIALS_JSON=./google_credentials.json"
    exit 1
fi

# Проверяем наличие Google credentials
if [ ! -f google_credentials.json ]; then
    echo "⚠️  Файл google_credentials.json не найден."
    echo "Создайте файл google_credentials.json с учетными данными Google Sheets API."
    echo "См. README_GOOGLE_SHEETS.md для инструкций."
fi

echo "✅ Проверки пройдены"

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose down

# Собираем образ
echo "🔨 Собираем Docker образ..."
docker-compose build

# Запускаем контейнеры
echo "🚀 Запускаем контейнеры..."
docker-compose up -d postgres redis

# Ждем, пока база данных будет готова
echo "⏳ Ждем готовности базы данных..."
sleep 10

# Инициализируем базу данных
echo "🗄️  Инициализируем базу данных..."
docker-compose run --rm bot python init_db.py

# Запускаем бота
echo "🤖 Запускаем бота..."
docker-compose up bot

echo "✅ Готово!"

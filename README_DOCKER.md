# 🐳 Запуск бота в Docker

Этот документ описывает, как запустить бота в Docker контейнере.

## 📋 Требования

- Docker
- docker-compose
- Файл `.env` с переменными окружения
- Файл `google_credentials.json` с учетными данными Google Sheets API

## 🚀 Быстрый старт

### 1. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
TOKEN=your_bot_token_here
DATABASE_URL=asyncpg+postgresql://otb:1234@postgres:5432/otb_db
REDIS_URL=redis://redis:6379/0
GOOGLE_CREDENTIALS_JSON=./google_credentials.json
```

### 2. Настройка Google Sheets API

Следуйте инструкциям в `README_GOOGLE_SHEETS.md` для создания файла `google_credentials.json`.

### 3. Запуск

```bash
./run_docker.sh
```

Или вручную:

```bash
# Сборка и запуск
docker-compose up --build

# В фоновом режиме
docker-compose up -d
```

## 🔧 Управление контейнерами

### Остановка
```bash
docker-compose down
```

### Просмотр логов
```bash
# Все сервисы
docker-compose logs

# Только бот
docker-compose logs bot

# Следить за логами в реальном времени
docker-compose logs -f bot
```

### Перезапуск
```bash
docker-compose restart bot
```

### Вход в контейнер
```bash
docker-compose exec bot bash
```

## 🗄️ База данных

### Инициализация
База данных автоматически инициализируется при первом запуске.

### Ручная инициализация
```bash
docker-compose run --rm bot python init_db.py
```

### Миграции Alembic
```bash
# Создание новой миграции
docker-compose run --rm bot alembic revision --autogenerate -m "Описание изменений"

# Применение миграций
docker-compose run --rm bot alembic upgrade head
```

## 🔍 Отладка

### Проверка состояния сервисов
```bash
docker-compose ps
```

### Проверка подключения к базе данных
```bash
docker-compose exec postgres psql -U otb -d otb_db -c "SELECT 1;"
```

### Проверка Redis
```bash
docker-compose exec redis redis-cli ping
```

## 📁 Структура проекта

```
.
├── Dockerfile              # Образ для бота
├── docker-compose.yml      # Конфигурация сервисов
├── .dockerignore           # Исключения для Docker
├── init_db.py             # Инициализация БД
├── run_docker.sh          # Скрипт запуска
└── README_DOCKER.md       # Этот файл
```

## ⚠️ Важные замечания

1. **Токен бота**: Убедитесь, что токен в `.env` действителен
2. **Google credentials**: Файл `google_credentials.json` должен быть в корне проекта
3. **Порты**: PostgreSQL (5432) и Redis (6379) доступны на localhost
4. **Данные**: Данные PostgreSQL и Redis сохраняются в Docker volumes

## 🐛 Решение проблем

### Бот не запускается
1. Проверьте токен в `.env`
2. Проверьте логи: `docker-compose logs bot`
3. Убедитесь, что база данных готова: `docker-compose logs postgres`

### Ошибки подключения к БД
1. Проверьте, что PostgreSQL запущен: `docker-compose ps`
2. Проверьте логи PostgreSQL: `docker-compose logs postgres`
3. Попробуйте пересоздать контейнеры: `docker-compose down && docker-compose up --build`

### Ошибки Google Sheets
1. Проверьте файл `google_credentials.json`
2. Убедитесь, что API включен в Google Cloud Console
3. Проверьте права доступа к таблицам

## 📞 Поддержка

Если возникли проблемы, проверьте:
1. Логи контейнеров
2. Настройки в `.env`
3. Наличие всех необходимых файлов
4. Состояние сервисов: `docker-compose ps`

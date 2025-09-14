# Настройка Google Sheets для бота

## 1. Создание Google Cloud Project

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Запомните Project ID

## 2. Включение Google Sheets API

1. В Google Cloud Console перейдите в "APIs & Services" > "Library"
2. Найдите "Google Sheets API" и включите его
3. Найдите "Google Drive API" и включите его

## 3. Создание Service Account

1. Перейдите в "APIs & Services" > "Credentials"
2. Нажмите "Create Credentials" > "Service Account"
3. Заполните:
   - Service account name: `otbor-bot-service`
   - Service account ID: `otbor-bot-service`
   - Description: `Service account for otbor bot Google Sheets access`
4. Нажмите "Create and Continue"
5. Пропустите шаг "Grant access" (нажмите "Done")

## 4. Создание ключа для Service Account

1. В списке Service Accounts найдите созданный аккаунт
2. Нажмите на него
3. Перейдите на вкладку "Keys"
4. Нажмите "Add Key" > "Create new key"
5. Выберите "JSON" и нажмите "Create"
6. Файл автоматически скачается

## 5. Настройка файла credentials

1. Переименуйте скачанный файл в `google_credentials.json`
2. Поместите его в корень проекта (рядом с main.py)
3. Добавьте в .gitignore:
   ```
   google_credentials.json
   *.json
   ```

## 6. Настройка Google Sheets

### Структура таблиц для каждого факультета:

Каждый факультет должен иметь 3 таблицы:
- `{faculty_slug}_ne_opyt` - собеседующие без опыта
- `{faculty_slug}_opyt` - собеседующие с опытом  
- `{faculty_slug}_svod` - участники

### Пример структуры таблицы собеседующих:

| Имя | ФИО | Контакты | Статус |
|-----|-----|----------|--------|
| Иван Петров | Иван Петрович Петров | @ivan_petrov | Активен |
| Мария Сидорова | Мария Ивановна Сидорова | @maria_sid | Активна |

### Пример структуры таблицы участников:

| VK ID | Имя | Фамилия | Статус |
|-------|-----|---------|--------|
| 123456789 | Иван | Петров | Зарегистрирован |
| 987654321 | Мария | Сидорова | Зарегистрирована |

## 7. Предоставление доступа к таблицам

1. Откройте каждую Google Sheet
2. Нажмите "Share" (Поделиться)
3. Добавьте email Service Account (найдите в JSON файле в поле "client_email")
4. Дайте права "Editor" (Редактор)

## 8. Настройка переменных окружения

Добавьте в .env файл:
```
GOOGLE_CREDENTIALS_JSON=./google_credentials.json
```

## 9. Тестирование

Запустите бота и проверьте:
1. Создание факультета через суперадмин панель
2. Настройку таблиц для факультета
3. Парсинг собеседующих из таблиц
4. Создание ссылок для регистрации

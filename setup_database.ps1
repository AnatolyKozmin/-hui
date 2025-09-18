# PowerShell скрипт для настройки базы данных

Write-Host "🚀 Настройка базы данных для бота отбора" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Проверяем, запущен ли Docker Compose
$postgresRunning = docker-compose ps | Select-String "postgres"
if (-not $postgresRunning) {
    Write-Host "❌ PostgreSQL не запущен. Запускаем Docker Compose..." -ForegroundColor Red
    docker-compose up -d postgres redis
    Write-Host "⏳ Ждем запуска PostgreSQL..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

Write-Host "🔍 Проверяем состояние базы данных..." -ForegroundColor Blue

# Запускаем инициализацию базы данных
Write-Host "📋 Инициализируем базу данных..." -ForegroundColor Blue
docker-compose run --rm db-init

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ База данных успешно инициализирована!" -ForegroundColor Green
    
    # Проверяем состояние
    Write-Host "🔍 Проверяем состояние базы данных..." -ForegroundColor Blue
    docker-compose run --rm bot python check_db.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 ВСЕ ГОТОВО К РАБОТЕ!" -ForegroundColor Green
        Write-Host "✅ База данных инициализирована" -ForegroundColor Green
        Write-Host "✅ Таблицы созданы" -ForegroundColor Green
        Write-Host "✅ Тестовые данные добавлены" -ForegroundColor Green
        Write-Host ""
        Write-Host "🚀 Теперь можно запустить бота:" -ForegroundColor Cyan
        Write-Host "   docker-compose up bot" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Проблемы с проверкой базы данных" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Ошибка инициализации базы данных" -ForegroundColor Red
    exit 1
}

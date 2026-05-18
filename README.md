# Генератор отмазок

Веб-сервис для генерации убедительных отмазок через DeepSeek AI.

## Запуск локально

```bash
pip install -r requirements.txt
cp .env.example .env
# заполни OPENROUTER_API_KEY в .env
uvicorn main:app --reload
```

Открыть: http://localhost:8000

## Деплой на Railway

1. Залить репо на GitHub
2. Подключить репо к Railway
3. Добавить переменную окружения `OPENROUTER_API_KEY`
4. Deploy — получишь живую ссылку

## Стек

Python · FastAPI · DeepSeek via OpenRouter · vanilla JS

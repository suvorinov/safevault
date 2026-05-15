# SafeVault

SafeVault — self-hosted менеджер секретов и конфигураций с акцентом на безопасность и простоту.

## Возможности

- **Self-hosted** — полный контроль над данными
- **Envelope Encryption** — двухуроневое шифрование (данные → DEK → Master Key)
- **Multi-user** — изоляция данных между пользователями
- **Audit Logging** — логирование всех операций с секретами
- **Rate Limiting** — защита от брутфорса
- **Web UI + CLI** — два интерфейса для работы

## Стек технологий

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI, Python 3.10+ |
| База данных | MongoDB (async motor) |
| Шифрование | cryptography (Fernet) |
| Rate Limiting | slowapi |
| Контейнеризация | Docker / Docker Compose |

## Быстрый старт

### 1. Генерация ключей

```bash
# MASTER_KEY — ключ для Fernet шифрования
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# SECRET_KEY — pepper для хеширования и дополнительной защиты
openssl rand -hex 32
```

### 2. Настройка .env

```bash
cp .env.example .env
# Заполните MASTER_KEY, SECRET_KEY, MONGO_URI
```

### 3. Запуск

```bash
docker-compose up --build -d
```

Приложение доступно:
- Web UI: http://localhost:8400
- API Docs: http://localhost:8400/docs

## API Endpoints

### Аутентификация

| Метод | Endpoint | Описание | Лимит |
|-------|----------|----------|-------|
| POST | `/api/v1/auth/register` | Регистрация | 5/мин |

### Проекты

| Метод | Endpoint | Описание | Лимит |
|-------|----------|----------|-------|
| GET | `/api/v1/projects/` | Список проектов | 60/мин |
| POST | `/api/v1/projects/` | Создать проект | 20/мин |
| GET | `/api/v1/projects/{id}` | Информация о проекте | 60/мин |
| DELETE | `/api/v1/projects/{id}` | Удалить проект | 20/мин |

### Секреты

| Метод | Endpoint | Описание | Лимит |
|-------|----------|----------|-------|
| GET | `/api/v1/secrets/{project_id}` | Список секретов | 60/мин |
| POST | `/api/v1/secrets/{project_id}` | Добавить секрет | 30/мин |
| DELETE | `/api/v1/secrets/{secret_id}` | Удалить секрет | 30/мин |

### Авторизация

Все API запросы требуют заголовок:
```
X-API-Key: sv_live_xxxxxxxxxxxxxx
```

## Структура проекта

```
safevault/
├── app/
│   ├── main.py              # Точка входа
│   ├── config.py           # Конфигурация (Pydantic Settings)
│   ├── database.py          # Подключение к MongoDB
│   ├── models/              # Pydantic модели (User, Project, Secret)
│   ├── services/
│   │   ├── audit.py         # Логирование аудита
│   │   ├── auth.py          # Аутентификация, хеширование
│   │   ├── crypto.py        # Шифрование (Envelope Encryption)
│   │   ├── project_service.py
│   │   └── secret_service.py
│   ├── routers/
│   │   ├── auth_router.py   # /api/v1/auth
│   │   ├── project_router.py
│   │   ├── secret_router.py
│   │   └── web_router.py    # Web UI эндпоинты
│   ├── utils/
│   │   ├── auth_deps.py     # Dependency injection для авторизации
│   │   └── rate_limit.py    # Rate limiting конфигурация
│   └── templates/           # Jinja2 шаблоны
├── cli/
│   └── vault_cli.py         # CLI клиент (Pure Python)
├── scripts/
│   └── generate_keys.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── requirements.txt
```

## Безопасность

### Архитектура шифрования

```
┌─────────────────────────────────────────────────┐
│                  Master Key                      │
│         (шифруется SECRET_KEY pepper)           │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│              Data Key (DEK)                      │
│     (уникальный для каждого проекта)            │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│           Secret Value                           │
│        (шифруется DEK проекта)                  │
└─────────────────────────────────────────────────┘
```

### Защита API ключей

API ключи хешируются с использованием:
1. bcrypt (защита от rainbow tables)
2. HMAC-SHA256 с SECRET_KEY как pepper

### Rate Limiting

| Endpoint | Лимит |
|----------|-------|
| `/api/v1/auth/register` | 5/мин |
| `/api/v1/secrets` (create/delete) | 30/мин |
| `/api/v1/secrets` (read) | 60/мин |
| `/api/v1/projects` (create/delete) | 20/мин |
| `/api/v1/projects` (read) | 60/мин |

### Audit Logging

Все операции логируются в коллекцию `audit_logs`:
- Регистрация пользователей
- Успешные/неуспешные логины
- Создание/удаление проектов
- Доступ к секретам

## CLI клиент

```bash
# Регистрация
python cli/vault_cli.py register --name "MyApp"

# Создание проекта
python cli/vault_cli.py project create "my-project" --desc "Production"

# Добавление секрета
python cli/vault_cli.py secret add "my-project" API_KEY "secret_value"

# Получение секретов (.env формат)
python cli/vault_cli.py secret get "my-project" --env

# Настройка
python cli/vault_cli.py config --key "sv_live_xxx" --url "http://localhost:8400"
```

## Команды Make

```bash
make up          # Запуск в фоне
make logs        # Просмотр логов
make build       # Пересборка
make clean       # Остановка и удаление volumes
make fresh       # Полный перезапуск
make lint        # Проверка кода (flake8)
make format      # Форматирование (black, isort)
```

## Переменные окружения

| Переменная | Обязательно | Описание |
|------------|-------------|----------|
| `MASTER_KEY` | ✅ | Fernet ключ для DEK шифрования |
| `SECRET_KEY` | ✅ | Pepper для хеширования API ключей |
| `MONGO_URI` | ✅ | MongoDB connection string |
| `MONGO_DB_NAME` | ✅ | Имя базы данных |
| `APP_NAME` | Нет | Название приложения (default: SafeVault) |
| `DEBUG` | Нет | Режим отладки |

## Важно

⚠️ **Потеря MASTER_KEY или SECRET_KEY = потеря всех данных!**

Не коммитьте `.env` файл в git!

## Лицензия

MIT
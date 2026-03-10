SafeVault

SafeVault — это self-hosted менеджер секретов и конфигураций, созданный с акцентом на простоту (KISS), безопасность и удобство развертывания.
Особенности

    Self-hosted: Полный контроль над данными.
    Безопасность: Envelope Encryption (шифрование данных уникальными ключами, которые сами зашифрованы Master Key).
    Технологии: FastAPI, MongoDB, Docker.
    Python Style: Google Style Guide.

Стек

    Python 3.10+
    FastAPI (Web Framework)
    MongoDB (NoSQL Database)
    Docker / Docker Compose

Быстрый старт

    Клонируйте репозиторий:

    git clone <repo_url>cd safevault

 

    Сгенерируйте ключи:
    Вам нужно сгенерировать MASTER_KEY и SECRET_KEY. 
    bash
     
      
     
    # Generate Master Key
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # Generate Secret Key (random string)
    openssl rand -hex 32
     
     
      

    Настройте .env:
    Скопируйте .env.example в .env и вставьте сгенерированные ключи.  

    Запустите проект: 
    bash
     
      
     
    docker-compose up --build
     
     
      

    Откройте документацию:
    Перейдите по адресу http://localhost:8000/docs.  

Структура проекта 

     app/ - Основной код приложения.
         services/ - Бизнес-логика (шифрование, работа с БД).
         models/ - Pydantic модели.
         routers/ - API эндпоинты.
         
     tests/ - Тесты.
     

Безопасность 

Внимание! MASTER_KEY — это самое важное. Если вы его потеряете, вы потеряете доступ ко всем данным. Не коммитьте .env файл в git! 

#!/usr/bin/env python3
"""Скрипт для генерации секретных ключей конфигурации."""
import os
import sys

# Добавляем корневую директорию в путь для импорта библиотек
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptography.fernet import Fernet
import secrets


def generate_keys():
    """Генерирует MASTER_KEY и SECRET_KEY и выводит их в формате .env."""

    print("#" + "=" * 50)
    print("# Сгенерированные ключи для файла .env")
    print("#" + "=" * 50)

    # 1. Генерация MASTER_KEY (Fernet Key)
    # Используется для шифрования ключей проектов
    master_key = Fernet.generate_key().decode("utf-8")
    print(f"MASTER_KEY={master_key}")

    # 2. Генерация SECRET_KEY (Session Key)
    # Используется для подписи сессий/токенов (случайная hex строка)
    secret_key = secrets.token_hex(32)
    print(f"SECRET_KEY={secret_key}")

    print("#" + "=" * 50)
    print("# Скопируйте эти строки в ваш файл .env")
    print("#" + "=" * 50)


if __name__ == "__main__":
    generate_keys()

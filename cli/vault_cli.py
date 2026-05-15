#!/usr/bin/env python3
"""CLI клиент для SafeVault (Pure Python).

Полный функционал: регистрация, CRUD для проектов и секретов.
Не требует внешних зависимостей.
"""

import argparse
import json
import os
import sys
import getpass
import urllib.request
import urllib.error
from pathlib import Path

# Конфигурация
DEFAULT_SERVER_URL = "http://localhost:8000"
CONFIG_DIR = Path.home() / ".safevault"
CONFIG_FILE = CONFIG_DIR / "config.json"


# --- Вспомогательные функции ---

def load_config():
    """Загружает конфигурацию из файла."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_config(data):
    """Сохраняет конфигурацию в файл."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    os.chmod(CONFIG_FILE, 0o600)


def make_request(endpoint, method="GET", data=None, auth_required=True):
    """Выполняет HTTP запрос к API."""
    config = load_config()
    base_url = config.get("server_url", DEFAULT_SERVER_URL)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if auth_required:
        api_key = config.get("api_key")
        if not api_key:
            print("Ошибка: API ключ не настроен. Используйте 'register' или 'config --key'.")
            sys.exit(1)
        headers["X-API-Key"] = api_key

    url = f"{base_url}{endpoint}"
    req_data = None
    if data:
        req_data = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(url, data=req_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request) as response:
            if response.status == 204:  # No Content
                return {}
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        try:
            error_json = json.loads(error_body)
            detail = error_json.get("detail", error_body)
        except json.JSONDecodeError:
            detail = error_body
        print(f"Ошибка API [{e.code}]: {detail}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Ошибка соединения: {e.reason}")
        print(f"Проверьте, запущен ли сервер: {base_url}")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)


def resolve_project_id(project_ref):
    """Разрешает ID проекта по ссылке (ID или Имя)."""
    if len(project_ref) > 10:
        return project_ref

    print(f"Ищем проект с именем '{project_ref}'...")
    projects = make_request("/api/v1/projects/")
    
    found_id = None
    matches = 0
    
    for p in projects:
        if p.get("name") == project_ref:
            found_id = p.get("id")
            matches += 1
    
    if matches == 1:
        print(f"Найден ID: {found_id}")
        return found_id
    elif matches > 1:
        print(f"Ошибка: Найдено несколько проектов с именем '{project_ref}'. Используйте ID.")
        for p in projects:
             if p.get("name") == project_ref:
                 print(f"  - ID: {p.get('id')}")
        sys.exit(1)
    else:
        print(f"Ошибка: Проект с именем '{project_ref}' не найден.")
        sys.exit(1)


# --- Команды ---

def cmd_register(args):
    """Регистрирует нового пользователя."""
    if not args.name:
        print("Ошибка: Укажите имя пользователя через аргумент --name")
        sys.exit(1)
    
    print(f"Регистрация пользователя '{args.name}'...")
    data = make_request("/api/v1/auth/register", method="POST", 
                        data={"name": args.name}, auth_required=False)
    
    api_key = data.get("api_key")
    if not api_key:
        print("Ошибка: Сервер не вернул API ключ.")
        return

    print("\nУспешная регистрация!")
    print(f"Ваш API ключ: {api_key}")
    print("ВНИМАНИЕ: Сохраните этот ключ, он показывается только один раз!")
    
    ans = input("Сохранить ключ в конфиг ~/.safevault/config.json? [Y/n]: ").strip().lower()
    if ans in ['', 'y', 'yes']:
        save_config({"api_key": api_key, "server_url": load_config().get("server_url", DEFAULT_SERVER_URL)})
        print("Ключ сохранен.")


def cmd_config(args):
    """Настраивает клиент."""
    config = load_config()
    if args.key:
        config["api_key"] = args.key
        print("API ключ сохранен.")
    if args.url:
        config["server_url"] = args.url
        print(f"URL сервера: {args.url}")
    if args.key or args.url:
        save_config(config)
    else:
        print(f"Сервер: {config.get('server_url', DEFAULT_SERVER_URL)}")
        key = config.get('api_key')
        print(f"API ключ: {key[:10]}...{key[-4:]}" if key else "Ключ не установлен.")


# --- PROJECT COMMANDS ---

def cmd_create_project(args):
    """Создает новый проект."""
    payload = {"name": args.name, "description": args.desc}
    data = make_request("/api/v1/projects/", method="POST", data=payload)
    print("Проект создан!")
    print(f"  ID: {data.get('id')}")
    print(f"  Имя: {data.get('name')}")


def cmd_list_projects(args):
    """Выводит список проектов."""
    projects = make_request("/api/v1/projects/")
    if not projects:
        print("Проекты не найдены.")
        return
    print("Список проектов:")
    for p in projects:
        print(f"  [{p.get('id')}] {p.get('name')}")


def cmd_delete_project(args):
    """Удаляет проект и его секреты."""
    project_id = resolve_project_id(args.project_ref)
    
    confirm = input(f"Вы уверены, что хотите удалить проект {project_id} и ВСЕ его секреты? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Отмена.")
        return

    # Вызываем API (API должен поддерживать удаление, добавим это в шаге 2)
    # Пока предполагаем, что эндпоинт есть
    make_request(f"/api/v1/projects/{project_id}", method="DELETE")
    print(f"Проект {project_id} успешно удален.")


# --- SECRET COMMANDS ---

def cmd_add_secret(args):
    """Добавляет секрет в проект."""
    project_id = resolve_project_id(args.project_ref)
    
    secret_value = args.value
    if not secret_value:
        secret_value = getpass.getpass("Введите значение секрета (скрытый ввод): ")

    payload = {
        "key": args.key,
        "value": secret_value,
        "description": args.desc
    }
    
    endpoint = f"/api/v1/secrets/{project_id}"
    make_request(endpoint, method="POST", data=payload)
    print("Секрет успешно добавлен.")


def cmd_get_secrets(args):
    """Получает секреты проекта."""
    project_id = resolve_project_id(args.project_ref)
    endpoint = f"/api/v1/secrets/{project_id}"
    secrets = make_request(endpoint)

    if args.env:
        for s in secrets:
            val = s['value']
            if " " in val or val == "":
                val = f'"{val}"'
            print(f"{s['key']}={val}")
    else:
        print(f"Секреты проекта (ID: {project_id}):")
        for s in secrets:
            print(f"  - {s['key']}: {s['value']}")
            if s.get('description'):
                print(f"    Описание: {s['description']}")


def cmd_delete_secret(args):
    """Удаляет секрет."""
    # Сначала найдем ID проекта, если передано имя
    project_id = resolve_project_id(args.project_ref)
    
    # Нужно найти ID секрета по имени ключа (так как пользователь вводит ключ, а не ID)
    # Для этого получим список секретов
    secrets = make_request(f"/api/v1/secrets/{project_id}")
    secret_id = None
    for s in secrets:
        if s['key'] == args.key:
            secret_id = s['id']
            break
    
    if not secret_id:
        print(f"Ошибка: Секрет с ключом '{args.key}' не найден в проекте.")
        sys.exit(1)

    make_request(f"/api/v1/secrets/{secret_id}", method="DELETE")
    print(f"Секрет '{args.key}' успешно удален.")


def main():
    """Точка входа."""
    parser = argparse.ArgumentParser(description="SafeVault CLI Client (Pure Python)")
    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # REGISTER
    p_reg = subparsers.add_parser("register", help="Регистрация")
    p_reg.add_argument("--name", required=True, help="Имя пользователя")
    p_reg.set_defaults(func=cmd_register)

    # CONFIG
    p_config = subparsers.add_parser("config", help="Настройка")
    p_config.add_argument("--key", help="API ключ")
    p_config.add_argument("--url", help="URL сервера")
    p_config.set_defaults(func=cmd_config)

    # PROJECT
    p_project = subparsers.add_parser("project", help="Управление проектами")
    p_project_sp = p_project.add_subparsers(dest="project_cmd")

    p_create = p_project_sp.add_parser("create", help="Создать проект")
    p_create.add_argument("name", help="Имя проекта")
    p_create.add_argument("--desc", default="", help="Описание")
    p_create.set_defaults(func=cmd_create_project)

    p_list = p_project_sp.add_parser("list", help="Список проектов")
    p_list.set_defaults(func=cmd_list_projects)

    # NEW: Delete Project
    p_del_proj = p_project_sp.add_parser("delete", help="Удалить проект")
    p_del_proj.add_argument("project_ref", help="ID или Имя проекта")
    p_del_proj.set_defaults(func=cmd_delete_project)

    # SECRET
    p_secret = subparsers.add_parser("secret", help="Управление секретами")
    p_secret_sp = p_secret.add_subparsers(dest="secret_cmd")

    s_add = p_secret_sp.add_parser("add", help="Добавить секрет")
    s_add.add_argument("project_ref", help="ID или Имя проекта")
    s_add.add_argument("key", help="Ключ (напр. DB_PASS)")
    s_add.add_argument("--value", help="Значение")
    s_add.add_argument("--desc", default="", help="Описание")
    s_add.set_defaults(func=cmd_add_secret)

    s_get = p_secret_sp.add_parser("get", help="Получить секреты")
    s_get.add_argument("project_ref", help="ID или Имя проекта")
    s_get.add_argument("--env", action="store_true", help="Формат .env")
    s_get.set_defaults(func=cmd_get_secrets)

    # NEW: Delete Secret
    s_del = p_secret_sp.add_parser("delete", help="Удалить секрет")
    s_del.add_argument("project_ref", help="ID или Имя проекта")
    s_del.add_argument("key", help="Имя ключа для удаления")
    s_del.set_defaults(func=cmd_delete_secret)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
# Переменные
PROJECT_NAME=safevault
COMPOSE_FILE=docker-compose.yml

.DEFAULT_GOAL := help

# --- Управление контейнерами ---

stop:
	@echo "Stopping services..."
	docker-compose -f $(COMPOSE_FILE) stop

start:
	@echo "Starting services..."
	docker-compose -f $(COMPOSE_FILE) start

restart: stop start

# --- Сборка и запуск ---

build:
	@echo "Building Docker images..."
	docker-compose -f $(COMPOSE_FILE) build

up:
	@echo "Starting services in detached mode..."
	docker-compose -f $(COMPOSE_FILE) up -d

logs:
	@echo "Starting services (logs follow)..."
	docker-compose -f $(COMPOSE_FILE) up

# --- Очистка ---

down:
	@echo "Stopping and removing containers..."
	docker-compose -f $(COMPOSE_FILE) down

clean: down
	@echo "Removing volumes..."
	docker-compose -f $(COMPOSE_FILE) down -v

fresh: clean build up
	@echo "Project fresh started."

# --- Утилиты ---

keys:
	@echo "Generating security keys..."
	@python3 scripts/generate_keys.py

ps:
	@docker-compose -f $(COMPOSE_FILE) ps

shell:
	docker-compose -f $(COMPOSE_FILE) exec web python -i -c "from app.database import *; from app.config import *"

web-logs:
	docker-compose -f $(COMPOSE_FILE) logs -f web

# --- NEW: Качество кода (Linting) ---

lint:
	@echo "Running linters..."
	@docker-compose -f $(COMPOSE_FILE) exec web flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
	@docker-compose -f $(COMPOSE_FILE) exec web flake8 app/ --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

format:
	@echo "Formatting code with black and isort..."
	docker-compose -f $(COMPOSE_FILE) exec web black app/
	docker-compose -f $(COMPOSE_FILE) exec web isort app/

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build   - Build Docker images"
	@echo "  up      - Start services in background"
	@echo "  down    - Stop and remove containers"
	@echo "  clean   - Remove containers and DB volumes"
	@echo "  fresh   - Clean, build and up"
	@echo "  keys    - Generate MASTER_KEY and SECRET_KEY"
	@echo "  lint    - Check code quality"
	@echo "  format  - Auto-format code"
	@echo "  logs    - Start with logs in console"
	@echo "  ps      - Show container status"

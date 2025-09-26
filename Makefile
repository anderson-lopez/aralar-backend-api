.PHONY: help install run test clean docker-build docker-up docker-down docker-logs docker-init docker-restart

help:
	@echo "=== Aralar API - Comandos Disponibles ==="
	@echo ""
	@echo "Desarrollo local:"
	@echo "  install       - Instalar dependencias Python"
	@echo "  run           - Ejecutar aplicación en desarrollo"
	@echo "  test          - Ejecutar tests"
	@echo "  clean         - Limpiar archivos temporales"
	@echo ""
	@echo "Docker:"
	@echo "  docker-init   - Configuración inicial completa con Docker"
	@echo "  docker-build  - Construir imagen Docker"
	@echo "  docker-up     - Iniciar servicios con Docker Compose"
	@echo "  docker-down   - Detener servicios Docker Compose"
	@echo "  docker-restart- Reiniciar servicios Docker"
	@echo "  docker-logs   - Ver logs de Docker en tiempo real"
	@echo "  docker-clean  - Limpiar contenedores y volúmenes"
	@echo ""
	@echo "Base de datos:"
	@echo "  seed          - Ejecutar seed de datos iniciales"
	@echo "  migrate       - Ejecutar migraciones"

# Desarrollo local
install:
	pip install -r requirements.txt

run:
	flask --app aralar.app run --debug

test:
	python -m pytest tests/ -v

clean:
	find . -type f -name "*.pyc" -delete || true
	find . -type d -name "__pycache__" -delete || true

# Docker - Configuración inicial completa
docker-init:
	@echo "Iniciando configuración completa con Docker..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Archivo .env creado. Por favor, edítalo con tus configuraciones."; fi
	docker-compose up --build -d
	@echo "Esperando que los servicios estén listos..."
	sleep 15
	docker-compose exec api python scripts/migrate.py
	docker-compose exec api python scripts/seed.py
	@echo "¡Configuración completa! API disponible en http://localhost:8000"

# Docker - Operaciones básicas
docker-build:
	docker-compose build --no-cache

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-restart:
	docker-compose restart

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
	docker system prune -f

# Base de datos
seed:
	python scripts/seed.py

migrate:
	python scripts/migrate.py

# Docker - Base de datos
docker-seed:
	docker-compose exec api python scripts/seed.py

docker-migrate:
	docker-compose exec api python scripts/migrate.py
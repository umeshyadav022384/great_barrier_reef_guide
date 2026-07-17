.PHONY: help build up down logs clean restart

help:
	@echo "🌊 Great Barrier Reef Voice Guide - Makefile Commands"
	@echo ""
	@echo "  make build     - Build all Docker containers"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make restart   - Restart all services"
	@echo "  make logs      - View logs from all services"
	@echo "  make clean     - Clean up containers, volumes, and images"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo ""
	@echo "🌊 Great Barrier Reef Voice Guide is running!"
	@echo "📱 Frontend: http://localhost:8080"
	@echo "🔗 Backend API: http://localhost:8000"
	@echo "🔗 Health Check: http://localhost:8000/health"
	@echo ""

down:
	docker-compose down

restart: down up

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	@echo "🧹 Cleaning up..."
	@echo "✅ Cleanup complete"
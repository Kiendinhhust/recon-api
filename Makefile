# Makefile for Recon API

.PHONY: help install dev test clean docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  install     - Install Python dependencies"
	@echo "  dev         - Start development server"
	@echo "  worker      - Start Celery worker"
	@echo "  worker-multi - Start multiple Celery workers for different queues"
	@echo "  test        - Run tests"
	@echo "  test-pipeline - Test the recon pipeline"
	@echo "  clean       - Clean up temporary files"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up   - Start Docker stack"
	@echo "  docker-down - Stop Docker stack"
	@echo "  init-db     - Initialize database"

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	celery -A app.workers.celery_app worker --loglevel=info --concurrency=2

worker-multi:
	@echo "Starting multiple Celery workers for different queues..."
	@echo "Worker 1: Full recon scans"
	celery -A app.workers.celery_app worker --loglevel=info --queues=recon_full --concurrency=1 --hostname=worker-full@%h &
	@echo "Worker 2: Subdomain enumeration"
	celery -A app.workers.celery_app worker --loglevel=info --queues=recon_enum --concurrency=2 --hostname=worker-enum@%h &
	@echo "Worker 3: Live host checking"
	celery -A app.workers.celery_app worker --loglevel=info --queues=recon_check --concurrency=3 --hostname=worker-check@%h &
	@echo "Worker 4: Screenshot capture"
	celery -A app.workers.celery_app worker --loglevel=info --queues=recon_screenshot --concurrency=1 --hostname=worker-screenshot@%h &
	@echo "Worker 5: Maintenance tasks"
	celery -A app.workers.celery_app worker --loglevel=info --queues=maintenance --concurrency=1 --hostname=worker-maintenance@%h &
	@echo "All workers started. Use 'pkill -f celery' to stop all workers."

flower:
	celery -A app.workers.celery_app flower

test-pipeline:
	python scripts/test_pipeline.py

test-amass:
	python scripts/test_amass_filter.py

quick-start:
	chmod +x scripts/quick_start.sh
	./scripts/quick_start.sh

test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=app --cov-report=html

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

init-db:
	python scripts/init_db.py

format:
	black app/ tests/
	isort app/ tests/

lint:
	black --check app/ tests/
	isort --check-only app/ tests/

# Database migrations
migration:
	alembic revision --autogenerate -m "$(msg)"

migrate:
	alembic upgrade head

# Development setup
setup-dev: install init-db
	@echo "Development environment setup complete!"
	@echo "Run 'make dev' to start the API server"
	@echo "Run 'make worker' in another terminal to start the worker"

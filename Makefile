.PHONY: dev dev-reset dev-periodic up down logs migrate seed superuser test lint fmt audit-chain

dev:           ## run everything locally with just Python + Node (no Docker)
	./scripts/dev.sh
dev-reset:     ## same, starting from a fresh database
	./scripts/dev.sh --reset
dev-periodic:  ## run the scheduled jobs once (digest, expiry, audit check) in local mode
	cd backend && DJANGO_SETTINGS_MODULE=wof.settings.local .venv/bin/python manage.py run_periodic

up:            ## start the whole stack in Docker
	@test -f .env || cp .env.example .env
	docker compose up -d --build
down:
	docker compose down
logs:
	docker compose logs -f backend worker frontend
migrate:
	docker compose exec backend python manage.py migrate
seed:          ## demo founders + stories (DEBUG only)
	docker compose exec backend python manage.py seed_demo
superuser:
	docker compose exec backend python manage.py createsuperuser
audit-chain:   ## verify the tamper-evident audit log
	docker compose exec backend python manage.py verify_audit_chain
test:
	cd backend && DJANGO_SETTINGS_MODULE=wof.settings.test pytest
	cd frontend && npm run typecheck && npm run lint
lint:
	cd backend && ruff check . && ruff format --check .
	cd frontend && npm run lint
fmt:
	cd backend && ruff format . && ruff check --fix .

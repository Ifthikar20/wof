.PHONY: up down logs migrate seed superuser test lint fmt audit-chain

up:            ## start the whole stack
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

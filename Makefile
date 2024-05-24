.PHONY: up upd upp down clean_db test analysis

up:
	docker compose up -d

upd:
	docker compose --profile dev up -d

upp:
	docker compose --profile prod up -d

down:
	docker compose down

clean_db:
	docker compose exec db psql -U user -d database -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

test:
	pytest

analysis:
	docker compose exec app python /app/src/analysis.py

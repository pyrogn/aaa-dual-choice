.PHONY: up upd upp down clean_db test analysis copy_data

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
	docker compose exec redis redis-cli flushdb

test:
	pytest

analysis:
	docker compose exec app python results/process_selections.py

copy_data:
	scp -r data student@51.250.19.218:~/aaa-dual-choice

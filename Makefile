.PHONY: up upd upp down clean_db test analysis copy_data

up:
	docker compose up -d

upd:
	docker compose --profile dev up -d

upp:
	docker compose --profile prod up -d

down:
	docker compose --profile "*" down

clean_db:
	docker compose exec db psql -U user -d database -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	docker compose exec redis redis-cli flushdb

# test:
# 	pytest
test:
	pytest --ignore tests/integration/ 

# test:
# 	docker compose --profile test up --build --abort-on-container-exit --exit-code-from test
# 	docker compose --profile test down

analysis:
	docker compose exec app python results/process_selections.py

copy_data:
	rsync -av --delete data/ student@51.250.19.218:~/aaa-dual-choice/data/

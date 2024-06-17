set dotenv-load

# List all recipies
default:
    @just --list

# Start the application with core services
up:
    docker compose up --build -d

# Start the application in development mode
up-dev:
    docker compose --profile dev up --build -d

# Start the application in production mode
up-prod:
    docker compose --profile prod up --build -d

# Stop the application
down:
    docker compose --profile "*" down

# Clean the database
clean-db: up-dev && down
    docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    docker compose exec redis redis-cli flushdb

# Run unit tests
test:
    pytest --ignore tests/integration/

# Run tests on real redis and database
test-db-redis: up-dev && down
    docker compose run test pytest tests/integration/test_db.py tests/integration/test_redis.py

# Run an e2e test in a browser
test-browser: up-dev && clean-db
    pytest tests/integration/test_browser.py

# Run full test suite
test-full: up && down
    just test
    just test-db-redis
    just test-browser

# Process selections
analysis: up
    docker compose run app python results/process_selections.py

# Copy data to a remote server
copy-data:
    rsync -av --delete data/ student@51.250.19.218:~/aaa-dual-choice/data/

.PHONY: venv install db up etl eda down docker-up docker-down

venv:
	python -m venv .venv

install: venv
	. .venv/bin/activate && pip install -r requirements.txt

db:
	mysql -h 127.0.0.1 -P 3306 -uroot -proot < sql/db_schema.sql

up:
	cp -n .env.docker .env || true
	docker compose up -d --build

etl:
	. .venv/bin/activate && python pipeline.py

eda:
	. .venv/bin/activate && python scripts/eda_initial.py

down:
	docker compose down

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down -v

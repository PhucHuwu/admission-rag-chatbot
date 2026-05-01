.PHONY: install dev lint format test

install:
	python3 -m pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check app

format:
	ruff format app

test:
	pytest

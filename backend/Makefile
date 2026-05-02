.PHONY: install dev lint lint-all format test gen-qa

install:
	python3 -m pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check app

lint-all:
	pylint app scripts

format:
	ruff format app

test:
	pytest

gen-qa:
	python3 scripts/generate_qa_dataset.py --data-dir ../data --output ./storage/qa_dataset.jsonl

# Backend

FastAPI backend for the admission RAG chatbot (localhost scope).

## 1) Setup

Python ≥ 3.10.

### Option A: venv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Option B: Makefile

```bash
python3 -m venv .venv
source .venv/bin/activate
make install
cp .env.example .env
```
Set `OPENROUTER_API_KEY` in `.env` to enable LLM answer generation.

## 2) Generate Q&A dataset

```bash
make gen-qa
```

Output file:

- `./storage/qa_dataset.jsonl`

## 3) Run server

```bash
make dev
```

Server:

- `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## 4) Build vector index

Call ingest endpoint after generating Q&A:

```
curl -X 'POST' \
  'http://localhost:8000/api/v1/ingest' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "data_dir": "./storage/qa_dataset.jsonl",
  "rebuild_index": true
}'
```

## 5) Main endpoints

- `GET /api/v1/health`
- `POST /api/v1/ingest`
- `POST /api/v1/search`
- `POST /api/v1/chat`

## 6) Useful commands

```bash
make lint
make lint-all
make format
make test
```

## Notes

- This backend ingests from Q&A JSONL (`QA_DATASET_PATH`), not directly from raw `data/*.json`.
- Embedding is local and free by default (`sentence-transformers`).

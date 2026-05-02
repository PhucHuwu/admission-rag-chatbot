# Backend

FastAPI backend for the admission RAG chatbot (localhost scope).

## Requirements

- Python 3.10+
- Recommended: Python 3.11

## Setup

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

Set `OPENROUTER_API_KEY` in `.env` if you want LLM-generated answers.

## Generate Q&A dataset

```bash
make gen-qa
```

Generated file:

- `./storage/qa_dataset.jsonl`

## Run server

```bash
make dev
```

- API base: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## Build vector index

After generating Q&A, call ingest:

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"rebuild_index": true}'
```

Optional override path:

```json
{
  "data_dir": "./storage/qa_dataset.jsonl",
  "rebuild_index": true
}
```

## Main endpoints

- `GET /api/v1/health`
- `POST /api/v1/ingest`
- `POST /api/v1/search`
- `POST /api/v1/chat`

## Dev commands

```bash
make lint
make lint-all
make format
make test
```

## Notes

- Ingest reads Q&A JSONL (`QA_DATASET_PATH`), not raw `data/*.json`.
- Embedding is local and free by default (`sentence-transformers`).

## Embedding device

Set `EMBEDDING_DEVICE` in `.env`:

- `auto` (default): `cuda` -> `mps` -> `cpu`
- `cpu`: force CPU
- `cuda`: force NVIDIA GPU
- `mps`: force Apple Silicon GPU

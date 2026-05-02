# Backend Skeleton (FastAPI)

Backend cho chatbot RAG tu van tuyen sinh, pham vi localhost.

## Cau truc

- `app/main.py`: FastAPI app entrypoint.
- `app/api/v1/`: API routers (`health`, `chat`, `ingest`, `search`).
- `app/core/`: config va logging.
- `app/models/`: Pydantic schemas cho request/response.
- `app/services/`: business logic stubs (chat, ingest, retrieval).

## Chay local

1. Tao virtual env va cai dependency.
2. Copy `.env.example` thanh `.env` va dieu chinh gia tri.
3. Chay:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Hoac dung Makefile:

```bash
make install
make dev
```

## Quality tools

- `make lint`: lint code voi ruff
- `make format`: format code voi ruff
- `make test`: chay pytest

## Sinh bo Q&A tu dong

- `make gen-qa`: sinh bo Q&A full-case tu `../data/*.json` ra `./storage/qa_dataset.jsonl`.
- Sau khi sinh Q&A, goi `POST /api/v1/ingest` de index vao Chroma.
- Co the chay truc tiep script de tuy chinh:

```bash
python3 scripts/generate_qa_dataset.py --data-dir ../data --output ./storage/qa_dataset.jsonl --max-programs-per-school 50
```

## API co san

- `GET /health`
- `POST /api/v1/chat`
- `POST /api/v1/ingest`
- `POST /api/v1/search`

Luu y: ingest hien doc tu bo Q&A JSONL (`QA_DATASET_PATH`), khong ingest truc tiep tu raw `data/*.json`.

## OpenRouter

- Dat `OPENROUTER_API_KEY` trong `.env`.
- Co the doi model bang `OPENROUTER_MODEL`.
- Endpoint mac dinh: `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`.

## Embedding (free)

- Mac dinh dung `sentence-transformers` local (free):
  - `EMBEDDING_PROVIDER=sentence_transformers`
  - `EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2`
- Backend se tu embed khi ingest/query, khong dung ONNX embedding mac dinh cua Chroma.

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

## API co san

- `GET /health`
- `POST /api/v1/chat`
- `POST /api/v1/ingest`
- `POST /api/v1/search`

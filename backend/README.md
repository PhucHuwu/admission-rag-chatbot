# Backend

NestJS API for the Admission RAG Chatbot.

## Requirements

- Node.js 18+
- npm 9+

## Setup

```bash
npm install
cp .env.example .env
```

Required env values (example):

```env
PORT=8000
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=admission_chunks
OPENAI_API_KEY=your_key
DATABASE_URL=postgresql://user:password@localhost:5432/admission_db
```

## Run

```bash
npm run dev
```

Alternative:

```bash
npm run start:dev
```

API default URL: `http://localhost:8000`

## Build

```bash
npm run build
npm run start:prod
```

## Main Endpoints

- `GET /api/v1/health`
- `POST /api/v1/ingest`
- `POST /api/v1/search`
- `POST /api/v1/chat`

## Notes

- CORS is enabled for local frontend URLs.
- `prisma generate` runs on postinstall.

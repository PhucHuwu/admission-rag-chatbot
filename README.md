# Admission RAG Chatbot

A RAG chatbot for university admission consulting.

## Project Structure

```text
admission-rag-chatbot/
├── frontend/   # Next.js app
├── backend/    # NestJS API
└── crawler/    # Data crawler (TypeScript)
```

## Requirements

- Node.js 18+
- npm 9+

## Install

From repository root:

```bash
npm install
```

This installs dependencies for all workspaces (`frontend`, `backend`, `crawler`).

## Run in Development

### From root

- Run frontend + backend together:

```bash
npm run dev
```

- Run only frontend:

```bash
npm run dev:fe
```

- Run only backend:

```bash
npm run dev:be
```

- Run crawler:

```bash
npm run dev:crawler
```

### From each package

Frontend:

```bash
cd frontend
npm run dev
```

Backend:

```bash
cd backend
npm run dev
```

Crawler:

```bash
cd crawler
npm run crawl
```

## Environment

Create local env files from examples:

- `backend/.env` from `backend/.env.example`
- `frontend/.env.local` from `frontend/.env.example`

Example frontend API URL:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## Build and Lint

From root:

```bash
npm run build
npm run lint
```

## Format

From root:

```bash
npm run format
npm run format:check
```

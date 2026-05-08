# Frontend

Next.js frontend for the Admission RAG Chatbot.

## Requirements

- Node.js 18+
- npm 9+

## Setup

```bash
npm install
cp .env.example .env.local
```

Example env:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## Run

```bash
npm run dev
```

App URL: `http://localhost:3000`

## Build

```bash
npm run build
npm run start
```

## Main Routes

- `/`
- `/chatbot`
- `/tra-cuu`

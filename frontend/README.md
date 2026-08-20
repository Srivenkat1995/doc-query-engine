# Frontend

Next.js application for the document parsing and query engine.

## Local setup

Install Node.js 18.17 or newer, then from the `frontend/` directory install
dependencies:

```text
npm install
```

## Run the frontend

```text
npm run dev
```

The application is available at `http://localhost:3000`.

The frontend checks `/api/health` by default. Next.js proxies that request to
`BACKEND_URL`, which defaults to `http://localhost:8000`. Set
`NEXT_PUBLIC_API_BASE_URL` only when the browser must call a different
same-origin API path directly.

## Verify the frontend

```text
npm run lint
npm run build
```

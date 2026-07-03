# Yuri Maker

Browse a curated MangaDex catalog — **Japanese-origin, Drama + Girls' Love,
completed** titles — and rate each one out of 10. Ratings are saved to a local
JSON file.

## Stack
- Backend: FastAPI + httpx (Python)
- Frontend: Vite + React
- Storage: flat JSON file (`backend/data/catalog.json`)

## Setup

### 1. Backend
```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Sync the catalog from MangaDex (one-time, re-runnable)
Run from the **project root** so the `backend` package resolves:
```bash
python -m backend.sync
```
This writes `backend/data/catalog.json`. Re-running refreshes the catalog while
**preserving any ratings you've given**.

### 3. Run the backend
```bash
uvicorn backend.main:app --reload
# serves http://127.0.0.1:8000
```

### 4. Run the frontend
```bash
cd frontend
npm install
npm run dev
# opens http://127.0.0.1:5173
```

## How it works
- `backend/sync.py` queries the MangaDex `/manga` endpoint with the fixed filter
  and stores `{ id, title, coverUrl, rating }` per item.
- The React app shows a grid of covers; pick a rating 0–10 and it `PUT`s to the
  backend, which writes it straight back to the JSON file.

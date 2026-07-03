# Yuri Maker

A personal web app for browsing a **curated MangaDex catalog** — Japanese-origin,
**Drama + Girls' Love**, **completed** titles — and rating each one out of 10.

## Purpose

It's a private "watchlist / scorecard" for a specific slice of MangaDex. Instead
of searching MangaDex every time, the catalog is fetched once with a fixed filter
and stored locally, so you get a single fast grid of every matching title. You
rate what you've read, prune what you don't want, and your scores persist across
visits and devices.

## What the website does

- **Browse the catalog** as a grid of cover art, one card per title.
- **Rate a title 0–10** from a dropdown on each card; the score is saved
  immediately and shown as a badge. Ratings survive reloads and redeploys.
- **Search** titles by name (substring match).
- **Filter** the grid by:
  - **Rated only** — hide titles you haven't scored yet.
  - **Doujinshi** — All / Only / Exclude.
  - **Oneshot** — All / Only / Exclude.
  - **From year** — keep titles published in that year or later (titles with an
    unknown year are never hidden).
- **Bulk delete** — select titles via the checkbox on each cover and remove them
  in one action. Deletions are permanent: removed titles are tombstoned so a
  future catalog re-sync never re-adds them.
- **Refresh the catalog** from MangaDex on demand (via the sync command), which
  pulls new matching titles while **preserving every rating** you've given.

## Stack

- **Backend** — FastAPI + httpx (Python). Serves the catalog and accepts rating
  and delete updates.
- **Frontend** — Vite + React. A client-side grid UI.
- **Storage** — the whole catalog is one JSON document, kept either in a flat
  file (local dev) or a Postgres database (hosted). See below.
- **Covers** — URLs only, loaded live from `uploads.mangadex.org`.

## Storage: file locally, database when hosted

`backend/storage.py` chooses its backend at runtime from the `DATABASE_URL`
environment variable:

- **`DATABASE_URL` unset** → a flat JSON file at `backend/data/catalog.json`.
  Simplest for local development.
- **`DATABASE_URL` set** → Postgres (e.g. a free [Neon](https://neon.tech)
  database), storing the entire catalog as a single JSONB row. Use this when
  hosting, because free hosts have **ephemeral filesystems** that would wipe the
  JSON file on every restart.

Either way the app behaves identically — the whole catalog dict is loaded and
saved as one unit.

## Local setup

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
Writes `backend/data/catalog.json` (or the database, if `DATABASE_URL` is set).
Re-running refreshes the catalog while **preserving any ratings you've given**.

### 3. Run the backend
```bash
uvicorn backend.main:app --reload   # http://127.0.0.1:8000
```

### 4. Run the frontend
```bash
cd frontend
npm install
npm run dev                          # http://127.0.0.1:5173
```
In dev, Vite proxies `/api` to the backend. In production the backend serves the
built frontend itself (same origin), so no proxy or CORS config is needed.

## Deployment (free tier: Render + Neon)

The repo ships a multi-stage `Dockerfile` that builds the React app and runs
FastAPI serving both the API and the built frontend from one service.

1. **Create a free Postgres database** at [neon.tech](https://neon.tech) (no card
   required) and copy its connection string.
2. **Seed it once** with your local catalog so existing ratings carry over, from
   the project root with `DATABASE_URL` set to the Neon string:
   ```bash
   python -m backend.seed
   ```
3. **Deploy on [Render](https://render.com)** → New → Web Service → connect this
   GitHub repo → it auto-detects the `Dockerfile` → Free plan. Add an environment
   variable `DATABASE_URL` = your Neon connection string.
4. Render builds and serves the app at a `*.onrender.com` URL.

**Ongoing sync:** run `python -m backend.sync` locally with `DATABASE_URL` set to
Neon; it upserts straight into the hosted database.

**Note on the free tier:** Render's free instance spins down after ~15 min of
inactivity, so the first request after idle can take up to ~50s while it wakes.
The frontend rides this out by retrying API calls during a cold start rather than
erroring.

## API

- `GET  /api/items` → all catalog items + `syncedAt`.
- `PUT  /api/items/{id}/rating`  `{ "rating": 0-10 }` → update & persist a rating.
- `POST /api/items/delete`       `{ "ids": [...] }`   → bulk-remove titles and
  tombstone their ids so re-sync never re-adds them.

## Data model (`catalog.json` / DB row)

- Item fields: `id`, `title`, `coverUrl`, `rating` (int 0–10 or `null`),
  `year` (int | null), `isDoujinshi`, `isOneshot`.
- Top level: `items`, `deletedIds` (tombstones), `syncedAt`.

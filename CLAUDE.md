# Yuri Maker

Personal web app to browse a curated MangaDex catalog (Japanese-origin,
Drama + Girls' Love, completed) and rate each title 0–10. Ratings persist.

## Architecture
- **backend/** — FastAPI (Python). Serves the catalog + the built frontend, and
  accepts rating/delete updates.
- **frontend/** — Vite + React grid UI.
- **Storage** — the whole catalog is one JSON document. `backend/storage.py`
  picks its backend from the `DATABASE_URL` env var:
  - unset → flat file `backend/data/catalog.json` (local dev).
  - set → Postgres (e.g. Neon), catalog stored as a single JSONB row (hosting;
    free hosts have ephemeral disks that would wipe the file).
  Both keep the same `load()` / `save()` API over the whole catalog dict, so
  `main.py` and `sync.py` are backend-agnostic.
- **Covers** — URL only, loaded live from `uploads.mangadex.org`. MangaDex
  serves a "read at mangadex.org" placeholder when the request carries a
  third-party `Referer`, so the frontend sends **none**: `<meta name="referrer"
  content="no-referrer">` in `index.html` plus `referrerPolicy="no-referrer"` on
  the cover `<img>`.

## Hosting
- Single **Docker** service (multi-stage `Dockerfile`): Node builds
  `frontend/dist`, Python runs `uvicorn backend.main:app` and serves that dist
  via `StaticFiles` mounted at `/` (after the `/api` routes). Same origin → no
  CORS needed in prod; frontend keeps calling relative `/api` paths.
- Deployed on **Render free tier** + **Neon** Postgres (both no credit card);
  `$PORT` injected by Render. Seed the DB once with `python -m backend.seed`
  (reads local `catalog.json`, writes to `DATABASE_URL`).
- Render free spins down after ~15 min idle (first request ~50s). The frontend
  `wakeFetch` wrapper in `frontend/src/api.js` retries API calls through cold
  starts (edge 404/502/503 with a non-JSON body) instead of erroring.

## Catalog filter (MangaDex `GET /manga`)
- `originalLanguage[]=ja`
- `includedTags[]` = Drama `b9af3a63-f058-46de-a9a0-e0c13906197a`
  + Girls' Love `a3c67850-4684-404e-9b7f-c69850ee5da6`, `includedTagsMode=AND`
- `status[]=completed`
- include `safe,suggestive,erotica` content ratings; `includes[]=cover_art`
- Cover URL: `https://uploads.mangadex.org/covers/{mangaId}/{fileName}.512.jpg`

## Commands
- Install backend: `pip install -r backend/requirements.txt`
- Sync catalog (one-time / refresh): `python -m backend.sync`
  - Upserts by MangaDex id and **preserves existing ratings**. Writes to the file
    or the DB depending on `DATABASE_URL`.
- Seed DB from local file (one-time, needs `DATABASE_URL`): `python -m backend.seed`
- Run backend: `uvicorn backend.main:app --reload`
- Run frontend: `cd frontend && npm install && npm run dev`
- Build image / run like prod: `docker build -t yuri . && docker run -e DATABASE_URL=... -e PORT=8000 -p 8000:8000 yuri`

## API
- `GET /api/items` → all catalog items.
- `PUT /api/items/{id}/rating` `{ "rating": 0-10 }` → updates & persists.
- `POST /api/items/delete` `{ "ids": [...] }` → bulk-removes items and
  tombstones their ids in `deletedIds` so re-sync never re-adds them.

## Data model (`catalog.json`)
- Item fields: `id`, `title`, `coverUrl`, `rating`, `year` (int|null),
  `isDoujinshi` and `isOneshot` (bool, from the respective format tags).
- Top level: `items`, `deletedIds` (tombstones), `syncedAt`.

## Filters (frontend, client-side in App.jsx)
- Doujinshi: All / Only / Exclude (`isDoujinshi`).
- Oneshot: All / Only / Exclude (`isOneshot`).
- From year: typed minimum; keep titles with `year >= minYear`.
  **Unknown year (`null`) is never hidden.**

## Conventions
- `rating` is an int 0–10 or `null` (unrated).
- Never overwrite `catalog.json` ratings on re-sync — merge by `id`.
- Re-sync skips ids in `deletedIds`; deletions are permanent.
- Adding filterable fields requires a re-sync to backfill existing items.
- Respect MangaDex rate limits (~5 req/s, descriptive User-Agent).

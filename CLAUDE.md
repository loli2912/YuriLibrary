# Yuri Maker

Personal web app to browse a curated MangaDex catalog (Japanese-origin,
Drama + Girls' Love, completed) and rate each title 0–10. Ratings persist.

## Architecture
- **backend/** — FastAPI (Python). Serves the catalog and accepts rating updates.
- **frontend/** — Vite + React grid UI.
- **Storage** — single JSON file `backend/data/catalog.json` (no database).
- **Covers** — URL only, loaded live from `uploads.mangadex.org`.

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
  - Upserts by MangaDex id and **preserves existing ratings**.
- Run backend: `uvicorn backend.main:app --reload`
- Run frontend: `cd frontend && npm install && npm run dev`

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

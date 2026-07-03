# Yuri Maker

A dedicated personal library web app for storing a yuri title with the data from MangaDex

Link public hostsite: https://yurilibrary.onrender.com/
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



## Data model (`catalog.json` / DB row)

- Item fields: `id`, `title`, `coverUrl`, `rating` (int 0–10 or `null`),
  `year` (int | null), `isDoujinshi`, `isOneshot`.
- Top level: `items`, `deletedIds` (tombstones), `syncedAt`.

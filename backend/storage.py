"""Persistence for the catalog (items + ratings).

Two backends, chosen at runtime by the ``DATABASE_URL`` env var:

- **DATABASE_URL set** → Postgres (e.g. Neon). The entire catalog is stored as a
  single JSONB blob in one row, mirroring the flat-file model. Use this in
  production, where the host filesystem is ephemeral.
- **DATABASE_URL unset** → the original flat JSON file at
  ``backend/data/catalog.json``. Convenient for local dev.

Both backends expose the same ``load()`` / ``save()`` API operating on the whole
catalog dict, so ``main.py`` and ``sync.py`` are agnostic to which one is active.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
CATALOG_PATH = DATA_DIR / "catalog.json"

DATABASE_URL = os.environ.get("DATABASE_URL")

EMPTY_CATALOG = {"items": [], "deletedIds": [], "syncedAt": None}


def load() -> dict:
    """Load the catalog, returning an empty structure if none exists yet."""
    catalog = _load_db() if DATABASE_URL else _load_file()
    # Upgrade older catalogs that predate the tombstone list.
    catalog.setdefault("deletedIds", [])
    return catalog


def save(catalog: dict) -> None:
    """Persist the whole catalog to the active backend."""
    if DATABASE_URL:
        _save_db(catalog)
    else:
        _save_file(catalog)


# --- Postgres backend -------------------------------------------------------

def _connect():
    # Imported lazily so local file-mode dev needs no psycopg install.
    import psycopg

    return psycopg.connect(DATABASE_URL)


def _ensure_schema(conn) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS catalog (id int PRIMARY KEY, data jsonb NOT NULL)"
    )


def _load_db() -> dict:
    with _connect() as conn:
        _ensure_schema(conn)
        row = conn.execute("SELECT data FROM catalog WHERE id = 1").fetchone()
    if row is None:
        return dict(EMPTY_CATALOG)
    # psycopg returns jsonb as an already-parsed Python object.
    return row[0]


def _save_db(catalog: dict) -> None:
    payload = json.dumps(catalog, ensure_ascii=False)
    with _connect() as conn:
        _ensure_schema(conn)
        conn.execute(
            "INSERT INTO catalog (id, data) VALUES (1, %s::jsonb) "
            "ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data",
            (payload,),
        )
        conn.commit()


# --- Flat-file backend ------------------------------------------------------

def _load_file() -> dict:
    if not CATALOG_PATH.exists():
        return dict(EMPTY_CATALOG)
    with CATALOG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_file(catalog: dict) -> None:
    """Atomically write the catalog to disk (temp file + replace)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(catalog, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_path, CATALOG_PATH)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

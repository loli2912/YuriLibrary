"""One-time seed: push the local catalog.json into the configured database.

Run from the project root with DATABASE_URL pointing at your (Neon) database:

    # PowerShell
    $env:DATABASE_URL = "postgresql://...neon.tech/...?sslmode=require"
    python -m backend.seed

Reads backend/data/catalog.json straight from disk (not via storage.load, which
would read the empty DB) and writes it to the DB, preserving your current
ratings. Refuses to run unless DATABASE_URL is set, so it can't no-op into the
local file.
"""
from __future__ import annotations

import json
import sys

from backend import storage


def main() -> None:
    if not storage.DATABASE_URL:
        sys.exit("DATABASE_URL is not set — nothing to seed into. Aborting.")
    if not storage.CATALOG_PATH.exists():
        sys.exit(f"No local catalog at {storage.CATALOG_PATH}. Aborting.")

    with storage.CATALOG_PATH.open("r", encoding="utf-8") as fh:
        catalog = json.load(fh)

    storage.save(catalog)
    print(
        f"Seeded {len(catalog.get('items', []))} items "
        f"({len(catalog.get('deletedIds', []))} tombstones) into the database."
    )


if __name__ == "__main__":
    main()

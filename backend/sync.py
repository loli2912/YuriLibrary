"""One-time (re-runnable) catalog sync from MangaDex.

Run from the project root:  python -m backend.sync

Upserts fetched titles into backend/data/catalog.json keyed by MangaDex id,
preserving any ratings the user has already given.
"""
from __future__ import annotations

from datetime import datetime, timezone

from backend import mangadex, storage


def sync() -> dict:
    existing = storage.load()
    ratings_by_id = {
        item["id"]: item.get("rating")
        for item in existing.get("items", [])
    }
    deleted_ids = set(existing.get("deletedIds", []))

    fetched = mangadex.fetch_catalog()

    items = []
    added = 0
    preserved = 0
    skipped = 0
    for item in fetched:
        if item["id"] in deleted_ids:
            skipped += 1  # tombstoned: never re-add a deleted title
            continue
        prior = ratings_by_id.get(item["id"])
        if item["id"] in ratings_by_id:
            if prior is not None:
                preserved += 1
            item["rating"] = prior
        else:
            added += 1
        items.append(item)

    catalog = {
        "items": items,
        "deletedIds": sorted(deleted_ids),
        "syncedAt": datetime.now(timezone.utc).isoformat(),
    }
    storage.save(catalog)
    return {
        "total": len(items),
        "added": added,
        "preserved": preserved,
        "skipped": skipped,
    }


def main() -> None:
    print("Fetching catalog from MangaDex...")
    result = sync()
    print(
        f"Done. {result['total']} titles "
        f"({result['added']} new, {result['preserved']} ratings preserved, "
        f"{result['skipped']} deleted skipped). "
        f"Saved to {storage.CATALOG_PATH}"
    )


if __name__ == "__main__":
    main()

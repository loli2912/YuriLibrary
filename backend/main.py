"""FastAPI app serving the catalog and accepting rating updates."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend import storage

# Built frontend, produced by `npm run build` and copied into the image.
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

app = FastAPI(title="Yuri Maker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RatingUpdate(BaseModel):
    rating: int = Field(ge=0, le=10)


class BulkDelete(BaseModel):
    ids: list[str] = Field(min_length=1)


@app.get("/api/items")
def get_items() -> dict:
    catalog = storage.load()
    return {
        "items": catalog.get("items", []),
        "syncedAt": catalog.get("syncedAt"),
    }


@app.put("/api/items/{item_id}/rating")
def update_rating(item_id: str, body: RatingUpdate) -> dict:
    catalog = storage.load()
    for item in catalog.get("items", []):
        if item["id"] == item_id:
            item["rating"] = body.rating
            storage.save(catalog)
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.post("/api/items/delete")
def delete_items(body: BulkDelete) -> dict:
    catalog = storage.load()
    items = catalog.get("items", [])
    target = set(body.ids)

    remaining = [item for item in items if item["id"] not in target]
    removed = len(items) - len(remaining)
    catalog["items"] = remaining

    # Tombstone every requested id so a future sync never re-adds them.
    deleted = catalog.setdefault("deletedIds", [])
    existing = set(deleted)
    deleted.extend(i for i in body.ids if i not in existing)

    storage.save(catalog)
    return {"requested": len(target), "removed": removed}


# Serve the built frontend from the same origin (so the app keeps calling
# relative /api paths, no CORS needed). Mounted last so the /api routes above
# take precedence. Skipped in dev when the build hasn't been produced yet;
# `html=True` serves index.html for client-side routes.
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")

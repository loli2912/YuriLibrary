"""MangaDex API client.

Fetches the curated catalog: Japanese-origin manga tagged both Drama and
Girls' Love, with a completed publication status.
"""
from __future__ import annotations

import time
from typing import Iterator

import httpx

API_BASE = "https://api.mangadex.org"
UPLOADS_BASE = "https://uploads.mangadex.org"

# Tag UUIDs (verified against GET /manga/tag).
TAG_DRAMA = "b9af3a63-f058-46de-a9a0-e0c13906197a"
TAG_GIRLS_LOVE = "a3c67850-4684-404e-9b7f-c69850ee5da6"
TAG_DOUJINSHI = "b13b2a48-c720-44a9-9c77-39c9979373fb"  # format tag
TAG_ONESHOT = "0234a31e-a729-4e28-9d6a-3f87c4966b9e"  # format tag

PAGE_LIMIT = 100  # MangaDex max page size for /manga.
USER_AGENT = "yuri-maker/1.0 (personal catalog app)"
REQUEST_DELAY = 0.25  # seconds between pages; stay well under ~5 req/s cap.


def _search_params(offset: int) -> list[tuple[str, str]]:
    """Query params for one page of the filtered /manga search.

    Returned as a list of tuples so repeated keys (the `[]` array params) are
    sent correctly.
    """
    return [
        ("limit", str(PAGE_LIMIT)),
        ("offset", str(offset)),
        ("originalLanguage[]", "ja"),
        ("includedTags[]", TAG_DRAMA),
        ("includedTags[]", TAG_GIRLS_LOVE),
        ("includedTagsMode", "AND"),
        ("status[]", "completed"),
        # Default search omits erotica/pornographic, which would silently drop
        # many yuri titles. Include the ratings we want explicitly.
        ("contentRating[]", "safe"),
        ("contentRating[]", "suggestive"),
        ("contentRating[]", "erotica"),
        ("includes[]", "cover_art"),
        ("order[title]", "asc"),
    ]


def _pick_title(attributes: dict) -> str:
    """Best-effort human title: prefer English, then any main title, then alt."""
    titles = attributes.get("title") or {}
    if titles.get("en"):
        return titles["en"]
    if titles:
        return next(iter(titles.values()))
    for alt in attributes.get("altTitles") or []:
        if alt:
            return next(iter(alt.values()))
    return "(untitled)"


def _cover_url(manga_id: str, relationships: list[dict]) -> str | None:
    """Build a 512px cover URL from the cover_art relationship, if present."""
    for rel in relationships:
        if rel.get("type") == "cover_art":
            file_name = (rel.get("attributes") or {}).get("fileName")
            if file_name:
                return f"{UPLOADS_BASE}/covers/{manga_id}/{file_name}.512.jpg"
    return None


def _to_item(manga: dict) -> dict:
    manga_id = manga["id"]
    attributes = manga.get("attributes") or {}
    relationships = manga.get("relationships") or []
    tags = attributes.get("tags") or []
    return {
        "id": manga_id,
        "title": _pick_title(attributes),
        "coverUrl": _cover_url(manga_id, relationships),
        "rating": None,
        "year": attributes.get("year"),
        "isDoujinshi": any(t.get("id") == TAG_DOUJINSHI for t in tags),
        "isOneshot": any(t.get("id") == TAG_ONESHOT for t in tags),
    }


def iter_catalog() -> Iterator[dict]:
    """Yield every matching manga as a catalog item, paging through results."""
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(base_url=API_BASE, headers=headers, timeout=30.0) as client:
        offset = 0
        while True:
            resp = client.get("/manga", params=_search_params(offset))
            resp.raise_for_status()
            payload = resp.json()

            data = payload.get("data") or []
            for manga in data:
                yield _to_item(manga)

            total = payload.get("total", 0)
            offset += PAGE_LIMIT
            if offset >= total or not data:
                break
            time.sleep(REQUEST_DELAY)


def fetch_catalog() -> list[dict]:
    """Collect the full filtered catalog into a list."""
    return list(iter_catalog())

#!/usr/bin/env python3
"""Synchronise public LinkedIn posts into the static site's JSON feed.

The live mode uses LinkedIn's authorised Posts API. It intentionally does not
scrape an authenticated browser session or accept credentials from source.
Set LINKEDIN_ACCESS_TOKEN, LINKEDIN_MEMBER_URN, and optionally
LINKEDIN_API_URL in the environment for scheduled updates.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_SINCE = date(2025, 10, 1)
DEFAULT_API_URL = "https://api.linkedin.com/rest/posts"


def _epoch_to_date(value: object) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date().isoformat()


def _text(item: dict) -> str:
    for key in ("commentary", "text", "description"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    specific = item.get("specificContent")
    if isinstance(specific, dict):
        share = specific.get("com.linkedin.ugc.ShareContent", {})
        if isinstance(share, dict):
            commentary = share.get("shareCommentary", {})
            if isinstance(commentary, dict) and isinstance(commentary.get("text"), str):
                return commentary["text"].strip()
    return ""


def _created_date(item: dict) -> str | None:
    created = item.get("created")
    if isinstance(created, dict):
        value = created.get("time") or created.get("timestamp")
        result = _epoch_to_date(value)
        if result:
            return result
        if isinstance(created.get("date"), str):
            return created["date"][:10]
    for key in ("date", "publishedAt", "createdAt"):
        value = item.get(key)
        if isinstance(value, str) and len(value) >= 10:
            return value[:10]
    return None


def normalize_posts(payload: dict | list) -> list[dict]:
    elements = payload if isinstance(payload, list) else payload.get("elements", [])
    if not isinstance(elements, list):
        return []
    result: list[dict] = []
    seen: set[str] = set()
    for item in elements:
        if not isinstance(item, dict):
            continue
        post_id = str(item.get("id") or item.get("urn") or "").strip()
        visibility = item.get("visibility")
        if visibility is not None and visibility != "PUBLIC":
            continue
        post_date = _created_date(item)
        text = _text(item)
        if not post_id or not post_date or not text or post_id in seen:
            continue
        seen.add(post_id)
        result.append({
            "id": post_id,
            "date": post_date,
            "text": text,
            "url": item.get("url") or item.get("permalink") or "",
        })
    return sorted(result, key=lambda p: (p["date"], p["id"]), reverse=True)


def select_since(posts: list[dict], since: date = DEFAULT_SINCE) -> list[dict]:
    return [p for p in posts if p.get("date", "") >= since.isoformat()]


def fetch_posts() -> list[dict]:
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
    member_urn = os.environ.get("LINKEDIN_MEMBER_URN", "").strip()
    if not token or not member_urn:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN and LINKEDIN_MEMBER_URN are required for live sync")
    base = os.environ.get("LINKEDIN_API_URL", DEFAULT_API_URL)
    query = urlencode({"author": member_urn, "q": "author", "count": "100"})
    request = Request(
        f"{base}?{query}",
        headers={
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": os.environ.get("LINKEDIN_VERSION", "202601"),
            "X-Restli-Protocol-Version": "2.0.0",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=30) as response:
        return select_since(normalize_posts(json.load(response)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Read an API JSON response from a file")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        if args.input:
            posts = select_since(normalize_posts(json.loads(args.input.read_text())))
        else:
            posts = fetch_posts()
    except Exception as exc:
        print(f"linkedin sync failed: {exc}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(posts, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(posts)} posts to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

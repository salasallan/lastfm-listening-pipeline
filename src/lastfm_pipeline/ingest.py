"""Ingestion logic: incremental load with a lookback window."""
import time

from lastfm_pipeline.client import fetch_recent_tracks_page
from lastfm_pipeline.db import insert_plays, uts_bounds

PAGE_SIZE = 200
PAUSE_SECONDS = 0.25
DEFAULT_LOOKBACK_SECONDS = 2 * 24 * 60 * 60  # re-fetch the last 2 days


def incremental_load(con, user, api_key, lookback_seconds=DEFAULT_LOOKBACK_SECONDS):
    """Fetch plays newer than (latest stored uts - lookback).

    The lookback catches scrobbles submitted late with older timestamps.
    Overlapping rows are ignored by the primary key, so this is idempotent.
    Returns (rows_added, pages_fetched).
    """
    _, newest = uts_bounds(con, user)
    if newest is None:
        raise RuntimeError("No data stored yet: run scripts/load_history.py first.")

    from_ts = newest - lookback_seconds
    to_ts = int(time.time())  # frozen upper bound, same idea as the backfill

    page, total_pages, added = 1, None, 0
    while total_pages is None or page <= total_pages:
        plays, attr = fetch_recent_tracks_page(
            user, api_key, page=page, limit=PAGE_SIZE, from_ts=from_ts, to_ts=to_ts
        )
        total_pages = int(attr["totalPages"])
        added += insert_plays(con, user, plays)
        page += 1
        if page <= total_pages:
            time.sleep(PAUSE_SECONDS)
    return added, total_pages
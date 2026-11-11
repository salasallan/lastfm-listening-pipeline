"""Historical load: backfill all scrobbles into DuckDB (resumable, idempotent)."""
import os
import time

from dotenv import load_dotenv

from lastfm_pipeline.client import fetch_recent_tracks_page
from lastfm_pipeline.db import connect, count_rows, insert_plays, uts_bounds

PAGE_SIZE = 200
PAUSE_SECONDS = 0.25


def main():
    load_dotenv()
    user = os.getenv("LASTFM_USER")
    api_key = os.getenv("LASTFM_API_KEY")
    if not user or not api_key:
        raise SystemExit("Missing LASTFM_API_KEY or LASTFM_USER in .env")

    con = connect()
    try:
        oldest, _ = uts_bounds(con, user)
        # Fresh load: freeze "now". Resume: go backwards from the oldest stored play.
        # The +1 makes the boundary overlap on purpose; duplicates are ignored.
        to_ts = int(time.time()) if oldest is None else oldest + 1
        print(f"Loading plays up to uts={to_ts} (rows already stored: {count_rows(con)})")

        page, total_pages, added_total = 1, None, 0
        while total_pages is None or page <= total_pages:
            plays, attr = fetch_recent_tracks_page(
                user, api_key, page=page, limit=PAGE_SIZE, to_ts=to_ts
            )
            total_pages = int(attr["totalPages"])
            if page == 1:
                print(f"API reports {attr['total']} plays in this range ({total_pages} pages)")
            added_total += insert_plays(con, user, plays)
            if page % 10 == 0 or page == total_pages:
                print(f"page {page}/{total_pages} - added {added_total} new rows so far")
            page += 1
            time.sleep(PAUSE_SECONDS)

        print(f"Done. Rows in raw_scrobbles: {count_rows(con)}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
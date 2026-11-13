"""Enrichment: fetch Last.fm tags for artists that don't have them yet (resumable)."""
import os
import time

from dotenv import load_dotenv

from lastfm_pipeline.client import LastFmError, fetch_artist_top_tags
from lastfm_pipeline.db import artists_missing_tags, connect, insert_artist_tags

PAUSE_SECONDS = 0.25
MAX_CONSECUTIVE_ERRORS = 10


def main():
    load_dotenv()
    api_key = os.getenv("LASTFM_API_KEY")
    if not api_key:
        raise SystemExit("Missing LASTFM_API_KEY in .env")

    con = connect()
    try:
        pending = artists_missing_tags(con)
        print(f"Artists without tags yet: {len(pending)}")

        stored = errors = consecutive_errors = 0
        for i, artist in enumerate(pending, start=1):
            try:
                tags = fetch_artist_top_tags(artist, api_key)
            except LastFmError as e:
                errors += 1
                consecutive_errors += 1
                print(f"  skipped {artist!r}: {e}")
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    raise SystemExit("Too many consecutive errors; stopping. Re-run to resume.")
                continue

            consecutive_errors = 0
            insert_artist_tags(con, artist, tags)
            stored += 1
            if i % 100 == 0 or i == len(pending):
                print(f"{i}/{len(pending)} processed - stored {stored}, skipped {errors}")
            time.sleep(PAUSE_SECONDS)

        print(f"Done. Stored {stored}, skipped {errors} (skipped artists are retried next run).")
    finally:
        con.close()


if __name__ == "__main__":
    main()
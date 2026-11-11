"""Incremental load: fetch only new plays. Safe to run repeatedly."""
import os

from dotenv import load_dotenv

from lastfm_pipeline.db import connect, count_rows
from lastfm_pipeline.ingest import incremental_load


def main():
    load_dotenv()
    user = os.getenv("LASTFM_USER")
    api_key = os.getenv("LASTFM_API_KEY")
    if not user or not api_key:
        raise SystemExit("Missing LASTFM_API_KEY or LASTFM_USER in .env")

    con = connect()
    try:
        before = count_rows(con)
        added, pages = incremental_load(con, user, api_key)
        print(f"Fetched {pages} page(s), added {added} new rows. "
              f"Total rows: {count_rows(con)} (was {before}).")
    finally:
        con.close()


if __name__ == "__main__":
    main()
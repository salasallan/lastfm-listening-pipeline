"""Export the publishable tables into a small standalone DuckDB file for the dashboard."""
import os
from datetime import datetime, timezone
from pathlib import Path

import duckdb
from dotenv import load_dotenv

SOURCE = Path("data/lastfm.duckdb")
TARGET = Path("data/dashboard.duckdb")
TABLES = ["mart_artist_daily", "mart_album_daily", "mart_track_daily", "mart_recent_plays"]


def main():
    load_dotenv()
    tz = os.getenv("LASTFM_TIMEZONE", "UTC")
    if not SOURCE.exists():
        raise SystemExit(f"{SOURCE} not found: run the pipeline first.")

    tmp = TARGET.with_name(TARGET.name + ".tmp")
    tmp.unlink(missing_ok=True)
    Path(str(tmp) + ".wal").unlink(missing_ok=True)

    con = duckdb.connect(str(tmp))
    try:
        con.execute(f"ATTACH '{SOURCE.as_posix()}' AS src (READ_ONLY)")
        for table in TABLES:
            con.execute(f"CREATE TABLE {table} AS SELECT * FROM src.main.{table}")
        con.execute("DETACH src")

        con.execute(
            "CREATE TABLE meta (exported_at_utc TIMESTAMP, timezone VARCHAR, "
            "latest_play_date DATE, total_plays BIGINT)"
        )
        latest, total = con.execute(
            "SELECT max(play_date), sum(plays) FROM mart_artist_daily"
        ).fetchone()
        exported_at = datetime.now(timezone.utc).replace(tzinfo=None)
        con.execute("INSERT INTO meta VALUES (?, ?, ?, ?)", [exported_at, tz, latest, int(total)])

        counts = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in TABLES}
        con.execute("CHECKPOINT")
    finally:
        con.close()

    try:
        tmp.replace(TARGET)
    except PermissionError:
        raise SystemExit(f"Could not replace {TARGET}: close the dashboard (or any tool using it) and retry.")

    print(f"Exported to {TARGET} ({TARGET.stat().st_size / 1_000_000:.1f} MB)")
    for table, n in counts.items():
        print(f"  {table}: {n} rows")
    print(f"  meta: latest_play_date={latest}, total_plays={int(total)}, timezone={tz}")


if __name__ == "__main__":
    main()
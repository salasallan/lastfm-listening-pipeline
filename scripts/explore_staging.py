"""Create the stg_plays view from its SQL file and run sanity checks."""
from pathlib import Path

from lastfm_pipeline.db import connect

SQL_FILE = Path("sql/staging/stg_plays.sql")

con = connect()
con.execute(f"CREATE OR REPLACE VIEW stg_plays AS\n{SQL_FILE.read_text(encoding='utf-8')}")

raw_rows = con.execute("SELECT count(*) FROM raw_scrobbles").fetchone()[0]
stg_rows = con.execute("SELECT count(*) FROM stg_plays").fetchone()[0]
print(f"raw rows: {raw_rows}, staging rows: {stg_rows}")

null_time, null_album, empty_names, null_artist_mbid = con.execute("""
    SELECT
        count(*) FILTER (WHERE played_at_utc IS NULL),
        count(*) FILTER (WHERE album IS NULL),
        count(*) FILTER (WHERE artist = '' OR track = ''),
        count(*) FILTER (WHERE artist_mbid IS NULL)
    FROM stg_plays
""").fetchone()
print(f"null timestamps: {null_time}")
print(f"null album: {null_album}")
print(f"empty artist/track names: {empty_names}")
print(f"null artist mbid: {null_artist_mbid}")

print("plays per year:")
for year, plays in con.execute(
    "SELECT year(played_at_utc), count(*) FROM stg_plays GROUP BY 1 ORDER BY 1"
).fetchall():
    print(f"  {year}: {plays}")

print("latest 5 plays (UTC):")
for row in con.execute(
    "SELECT played_at_utc, artist, album, track FROM stg_plays "
    "ORDER BY played_at_utc DESC LIMIT 5"
).fetchall():
    print(" ", row)

con.close()
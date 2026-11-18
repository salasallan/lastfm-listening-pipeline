"""Experiment: how much smaller would raw plays and tags be as typed columns instead of JSON?

Writes a temporary file in data/ for each variant, measures it and deletes it.
Does not touch the real database.
"""
from pathlib import Path

import duckdb

SRC = "data/lastfm.duckdb"
TMP = Path("data/_experiment.duckdb")

BASE = "lastfm_user, uts, artist, track"
ALBUM = "nullif(json_extract_string(payload, '$.album.\"#text\"'), '') as album"
MBIDS = (
    "nullif(json_extract_string(payload, '$.artist.mbid'), '') as artist_mbid, "
    "nullif(json_extract_string(payload, '$.album.mbid'), '') as album_mbid, "
    "nullif(json_extract_string(payload, '$.mbid'), '') as track_mbid"
)
URL = "json_extract_string(payload, '$.url') as track_url"

PLAYS = {
    "plays: JSON payload (current)": f"{BASE}, payload, ingested_at",
    "plays: typed columns, all fields": f"{BASE}, {ALBUM}, {MBIDS}, {URL}, ingested_at",
    "plays: typed, without url": f"{BASE}, {ALBUM}, {MBIDS}, ingested_at",
    "plays: typed, without url and mbids": f"{BASE}, {ALBUM}, ingested_at",
}
TAGS = {
    "tags: JSON array (current)": "select artist, payload, fetched_at from src.main.raw_artist_tags",
    "tags: one row per tag": (
        "select artist, lower(json_extract_string(tag, '$.name')) as tag, "
        "cast(json_extract_string(tag, '$.count') as integer) as tag_count "
        "from (select artist, unnest(from_json(payload, '[\"JSON\"]')) as tag "
        "from src.main.raw_artist_tags)"
    ),
}


def cleanup():
    for p in (TMP, Path(str(TMP) + ".wal")):
        p.unlink(missing_ok=True)


def measure(label, create_sql):
    cleanup()
    con = duckdb.connect(str(TMP))
    try:
        con.execute(f"ATTACH '{SRC}' AS src (READ_ONLY)")
        con.execute(create_sql)
        con.execute("DETACH src")
        con.execute("CHECKPOINT")
    finally:
        con.close()
    print(f"  {label}: {TMP.stat().st_size / 1_000_000:.1f} MB")
    cleanup()


print(f"current database: {Path(SRC).stat().st_size / 1_000_000:.1f} MB (plays, tags and the dbt tables)\n")
for label, cols in PLAYS.items():
    measure(label, f"create table t as select {cols} from src.main.raw_scrobbles order by uts")
for label, select in TAGS.items():
    measure(label, f"create table t as {select}")
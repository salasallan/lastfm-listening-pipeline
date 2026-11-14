"""One-time migration: copy the raw tables into a new, smaller DuckDB file.

Keeps only the fields the pipeline uses and the top tags per artist. The old file is
left untouched; swap the files manually after the checks pass.
"""
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, "src")
from lastfm_pipeline.db import connect, slim_play, slim_tags  # noqa: E402

SOURCE = Path("data/lastfm.duckdb")
TARGET = Path("data/lastfm.compact.duckdb")

FIELDS_HASH = (
    "hash(json_extract_string(payload, '$.album.\"#text\"'), "
    "json_extract_string(payload, '$.artist.mbid'), "
    "json_extract_string(payload, '$.album.mbid'), "
    "json_extract_string(payload, '$.mbid'), "
    "json_extract_string(payload, '$.url'))"
)
CHECKS = {
    "play rows": "select count(*) from raw_scrobbles",
    "play keys": "select bit_xor(hash(lastfm_user, uts, artist, track)) from raw_scrobbles",
    "play fields used by staging": f"select bit_xor({FIELDS_HASH}) from raw_scrobbles",
    "artists with a tag record": "select count(*) from raw_artist_tags",
    "artists with at least one tag": "select count(*) filter (where json_array_length(payload) > 0) from raw_artist_tags",
    "top-1 tag per artist": "select bit_xor(hash(artist, lower(json_extract_string(payload, '$[0].name')))) from raw_artist_tags",
}


def main():
    if not SOURCE.exists():
        raise SystemExit(f"{SOURCE} not found.")
    TARGET.unlink(missing_ok=True)
    Path(str(TARGET) + ".wal").unlink(missing_ok=True)

    src = duckdb.connect(str(SOURCE), read_only=True)
    plays = src.execute(
        "select lastfm_user, uts, artist, track, payload::varchar as payload, ingested_at from raw_scrobbles"
    ).df()
    tags = src.execute(
        "select artist, payload::varchar as payload, fetched_at from raw_artist_tags"
    ).df()
    src.close()
    print(f"read {len(plays)} plays and {len(tags)} artist tag records")

    plays["payload"] = plays["payload"].map(
        lambda s: json.dumps(slim_play(json.loads(s)), ensure_ascii=False))
    tags["payload"] = tags["payload"].map(
        lambda s: json.dumps(slim_tags(json.loads(s)), ensure_ascii=False))

    dst = connect(TARGET)  # creates both raw tables with the current schema
    dst.register("plays_df", plays)
    dst.register("tags_df", tags)
    dst.execute(
        "insert into raw_scrobbles (lastfm_user, uts, artist, track, payload, ingested_at) "
        "select lastfm_user, uts, artist, track, payload, ingested_at from plays_df")
    dst.execute(
        "insert into raw_artist_tags (artist, payload, fetched_at) "
        "select artist, payload, fetched_at from tags_df")
    dst.execute("checkpoint")
    dst.close()

    old = duckdb.connect(str(SOURCE), read_only=True)
    new = duckdb.connect(str(TARGET), read_only=True)
    failures = 0
    print("\nchecks (old file vs new file):")
    for name, sql in CHECKS.items():
        a, b = old.execute(sql).fetchone()[0], new.execute(sql).fetchone()[0]
        ok = a == b
        failures += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {a} vs {b}")
    old.close()
    new.close()

    print(f"\nold file: {SOURCE.stat().st_size / 1_000_000:.1f} MB, "
          f"new file: {TARGET.stat().st_size / 1_000_000:.1f} MB")
    if failures:
        raise SystemExit(f"{failures} check(s) failed: do NOT swap the files.")
    print("All checks passed. Safe to swap (see the instructions).")


if __name__ == "__main__":
    main()
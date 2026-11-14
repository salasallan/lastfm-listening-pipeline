"""Snapshot checksums of the marts before a migration ('save'), and compare afterwards ('compare')."""
import json
import sys
from pathlib import Path

import duckdb

DB = Path("data/lastfm.duckdb")
SNAP = Path("data/marts_snapshot.json")

CHECKSUMS = {
    "mart_track_daily": "select count(*), sum(plays), bit_xor(hash(play_date, artist, track, plays)) from mart_track_daily",
    "mart_album_daily": "select count(*), sum(plays), bit_xor(hash(play_date, artist, album, plays)) from mart_album_daily",
    "mart_artist_daily": "select count(*), sum(plays), bit_xor(hash(play_date, artist, genre, genre_family, plays)) from mart_artist_daily",
    "mart_recent_plays": "select count(*), 0, bit_xor(hash(played_at_local, artist, track, album, genre)) from mart_recent_plays",
}


def take():
    con = duckdb.connect(str(DB), read_only=True)
    sums = {name: [int(v) for v in con.execute(sql).fetchone()] for name, sql in CHECKSUMS.items()}
    genres = dict(con.execute("select artist, genre from dim_artist_genre").fetchall())
    con.close()
    return {"checksums": sums, "genres": genres}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "save":
        SNAP.write_text(json.dumps(take()), encoding="utf-8")
        print(f"Snapshot saved to {SNAP}. Do not run the pipeline until you have compared.")
        return
    if mode != "compare":
        raise SystemExit("usage: snapshot_marts.py save|compare")

    old, new = json.loads(SNAP.read_text(encoding="utf-8")), take()
    failures = 0
    for name in CHECKSUMS:
        same = old["checksums"][name] == new["checksums"][name]
        failures += not same
        print(f"  {'PASS' if same else 'DIFF'}  {name}: {old['checksums'][name]} vs {new['checksums'][name]}")

    changed = [(a, old["genres"].get(a), g) for a, g in new["genres"].items() if old["genres"].get(a) != g]
    print(f"\nartists whose genre changed: {len(changed)} of {len(new['genres'])}")
    for artist, before, after in changed[:20]:
        print(f"  {artist}: {before} -> {after}")
    print("\nThe mart_artist_daily DIFF is expected only if some genres changed above."
          if changed else "\nNo genre changed.")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
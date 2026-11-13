"""List top-1 tags missing from the genre mapping seed, by plays (maintenance helper)."""
import csv
from pathlib import Path

import duckdb

SEED = Path("dbt/seeds/genre_mapping.csv")
LIMIT = 80

mapped = set()
with SEED.open(encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        mapped.add(row["tag"].strip().lower())

con = duckdb.connect("data/lastfm.duckdb", read_only=True)
total_plays = con.execute("select count(*) from raw_scrobbles").fetchone()[0]
rows = con.execute("""
    select lower(json_extract_string(r.payload, '$[0].name')) as tag,
           count(*) as plays,
           count(distinct s.artist) as artists
    from raw_scrobbles s
    join raw_artist_tags r on r.artist = s.artist
    where json_array_length(r.payload) > 0
    group by 1
    order by plays desc
""").fetchall()
con.close()

unmapped = [r for r in rows if r[0] not in mapped]
mapped_plays = sum(r[1] for r in rows if r[0] in mapped)
unmapped_plays = sum(r[1] for r in unmapped)
print(f"mapped top-1 tags cover {mapped_plays / total_plays:.1%} of all plays")
print(f"unmapped top-1 tags: {len(unmapped)} tags, {unmapped_plays / total_plays:.1%} of plays\n")
print(f"top {LIMIT} unmapped tags by plays:")
for tag, plays, artists in unmapped[:LIMIT]:
    print(f"  {tag}: {plays} plays, {artists} artists")
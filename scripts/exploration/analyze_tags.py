"""Analyze the top-1 tag distribution: coverage curve, sample of the tail, CSV export."""
import csv
import random
from pathlib import Path

import duckdb

con = duckdb.connect("data/lastfm.duckdb", read_only=True)
total_plays = con.execute("select count(*) from raw_scrobbles").fetchone()[0]
rows = con.execute("""
    select
        case when r.artist is null then '(not fetched)'
             else coalesce(lower(json_extract_string(r.payload, '$[0].name')), '(no tags)')
        end as tag,
        count(*) as plays,
        count(distinct s.artist) as artists
    from raw_scrobbles s
    left join raw_artist_tags r on r.artist = s.artist
    group by 1
    order by plays desc
""").fetchall()
con.close()

specials = [r for r in rows if r[0] in ("(no tags)", "(not fetched)")]
genre_rows = [r for r in rows if r[0] not in ("(no tags)", "(not fetched)")]

print(f"distinct top-1 tags: {len(genre_rows)}")
for tag, plays, artists in specials:
    print(f"{tag}: {plays} plays ({plays / total_plays:.2%}), {artists} artists")

cum = 0
export = []
for i, (tag, plays, artists) in enumerate(genre_rows, start=1):
    cum += plays
    export.append((i, tag, plays, artists, round(cum / total_plays, 4)))
    if i in (10, 25, 50, 100, 200, 400):
        print(f"top {i} tags cover {cum / total_plays:.1%} of all plays")

print("\ntags ranked 31-70:")
for rank, tag, plays, artists, _ in export[30:70]:
    print(f"  #{rank} {tag}: {plays} plays, {artists} artists")

tail = export[70:]
print("\nrandom sample of 25 tags from rank 71 onward:")
for rank, tag, plays, artists, _ in random.Random(7).sample(tail, min(25, len(tail))):
    print(f"  #{rank} {tag}: {plays} plays, {artists} artists")

out = Path("data/top1_tags_for_review.csv")
with out.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["rank", "tag", "plays", "artists", "cumulative_share"])
    writer.writerows(export)
print(f"\nSaved the full list to {out}")
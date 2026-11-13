"""Explore artist.getTopTags: tag coverage and the top-1 tag per artist (sample only)."""
import json
import os
import random
import time
from collections import Counter
from pathlib import Path

import duckdb
from dotenv import load_dotenv

from lastfm_pipeline.client import LastFmError, _request  # raw access, exploration only

TOP_N_ARTISTS = 25
RANDOM_N_ARTISTS = 15
PAUSE_SECONDS = 0.25

load_dotenv()
api_key = os.getenv("LASTFM_API_KEY")
if not api_key:
    raise SystemExit("Missing LASTFM_API_KEY in .env")

con = duckdb.connect("data/lastfm.duckdb", read_only=True)
rows = con.execute(
    "select artist, count(*) as plays from raw_scrobbles group by 1 order by plays desc"
).fetchall()
con.close()
print(f"distinct artists: {len(rows)}")

top = rows[:TOP_N_ARTISTS]
tail = random.Random(42).sample(rows[TOP_N_ARTISTS:], RANDOM_N_ARTISTS)
sample = [("top", a, p) for a, p in top] + [("tail", a, p) for a, p in tail]

raw_responses = {}
top1_counter = Counter()
with_tag = {"top": 0, "tail": 0}

for group, artist, plays in sample:
    try:
        data = _request({
            "method": "artist.gettoptags",
            "artist": artist,
            "api_key": api_key,
            "format": "json",
            "autocorrect": 1,
        })
    except LastFmError as e:
        print(f"[{group}] {artist} ({plays} plays) -> ERROR: {e}")
        raw_responses[artist] = {"error": str(e)}
        continue

    raw_responses[artist] = data
    tags = data.get("toptags", {}).get("tag", [])
    if isinstance(tags, dict):
        tags = [tags]

    if tags:
        first = max(tags, key=lambda t: int(t.get("count", 0)))
        with_tag[group] += 1
        top1_counter[first["name"].lower()] += 1
        print(f"[{group}] {artist} ({plays} plays) -> {first['name']} ({first['count']})")
    else:
        print(f"[{group}] {artist} ({plays} plays) -> (no tags)")
    time.sleep(PAUSE_SECONDS)

print(f"\nwith at least one tag: top {with_tag['top']}/{TOP_N_ARTISTS}, "
      f"tail {with_tag['tail']}/{RANDOM_N_ARTISTS}")
print("most common top-1 tags in this sample:")
for name, n in top1_counter.most_common(10):
    print(f"  {name}: {n}")

out = Path("data/sample_artist_tags.json")
out.write_text(json.dumps(raw_responses, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nSaved full responses to {out}")
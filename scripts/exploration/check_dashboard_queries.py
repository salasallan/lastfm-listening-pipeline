"""Cross-check the dashboard export and queries against an independent calculation from stg_plays."""
import sys
from datetime import date, timedelta
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, "dashboard")
import queries as q  # noqa: E402

DASH_DB = Path("data/dashboard.duckdb")
FULL_DB = Path("data/lastfm.duckdb")
N = 15

dash = q.connect_readonly(DASH_DB)
full = duckdb.connect(str(FULL_DB), read_only=True)
meta = q.get_meta(dash)
latest = meta["latest_play_date"]
first = full.execute("select min(cast(played_at_local as date)) from stg_plays").fetchone()[0]

failures = 0


def check(name, ok):
    global failures
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures += 1


def rows(df, cols):
    return list(df[cols].itertuples(index=False, name=None))


print(f"dashboard export: latest play date {latest}, timezone {meta['timezone']}, "
      f"exported at {meta['exported_at_utc']} UTC")
raw_total = full.execute("select count(*) from raw_scrobbles").fetchone()[0]
check("meta total_plays equals raw_scrobbles", meta["total_plays"] == raw_total)

ranges = {
    "latest day": (latest, latest),
    "last 7 days": (latest - timedelta(days=6), latest),
    "last 30 days": (latest - timedelta(days=29), latest),
    "all time": (first, latest),
    "custom 2021-03-01..2021-06-30": (date(2021, 3, 1), date(2021, 6, 30)),
}

for label, (start, end) in ranges.items():
    print(f"\n{label} ({start} .. {end})")
    in_range = "cast(played_at_local as date) between ? and ?"

    exp_plays, exp_artists = full.execute(
        f"select count(*), count(distinct artist) from stg_plays where {in_range}", [start, end]
    ).fetchone()
    exp_tracks = full.execute(
        f"select count(*) from (select distinct artist, track from stg_plays where {in_range})",
        [start, end],
    ).fetchone()[0]
    k = q.kpis(dash, start, end)
    check("kpis (plays, artists, tracks)",
          (k["plays"], k["artists"], k["tracks"]) == (exp_plays, exp_artists, exp_tracks))

    exp = full.execute(
        f"select artist, count(*) as plays from stg_plays where {in_range} "
        f"group by artist order by plays desc, artist limit {N}", [start, end]).fetchall()
    check("top artists", rows(q.top_artists(dash, start, end, N), ["artist", "plays"]) == exp)

    exp = full.execute(
        f"select artist, track, count(*) as plays from stg_plays where {in_range} "
        f"group by artist, track order by plays desc, artist, track limit {N}", [start, end]).fetchall()
    check("top tracks", rows(q.top_tracks(dash, start, end, N), ["artist", "track", "plays"]) == exp)

    exp = full.execute(
        f"select artist, album, count(*) as plays from stg_plays where {in_range} and album is not null "
        f"group by artist, album order by plays desc, artist, album limit {N}", [start, end]).fetchall()
    check("top albums", rows(q.top_albums(dash, start, end, N), ["artist", "album", "plays"]) == exp)

    exp = full.execute(
        f"select g.genre_family, count(*) as plays from stg_plays p "
        f"join dim_artist_genre g on g.artist = p.artist "
        f"where cast(p.played_at_local as date) between ? and ? "
        f"group by g.genre_family order by plays desc, g.genre_family", [start, end]).fetchall()
    check("genre families", rows(q.genre_family_breakdown(dash, start, end), ["genre_family", "plays"]) == exp)

    series = q.plays_over_time(dash, start, end, "day")
    check("plays over time sums to total and covers every day",
          int(series["plays"].sum()) == exp_plays and len(series) == (end - start).days + 1)

print("\nrecent plays")
recent = q.recent_plays(dash)
newest = full.execute("select max(played_at_local) from stg_plays").fetchone()[0]
check("recent plays: 100 rows", len(recent) == 100)
check("recent plays: newest play matches staging", pd.Timestamp(newest) == recent["played_at_local"].max())

print(f"\n{'ALL CHECKS PASSED' if failures == 0 else f'{failures} CHECK(S) FAILED'}")
sys.exit(1 if failures else 0)
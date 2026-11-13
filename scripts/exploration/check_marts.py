"""Sanity-check the daily marts with the kinds of date-range questions the dashboard will ask."""
from datetime import timedelta

import duckdb

con = duckdb.connect("data/lastfm.duckdb", read_only=True)
latest = con.execute("select max(play_date) from mart_artist_daily").fetchone()[0]
print(f"latest play date in the marts (local): {latest}")

mart_total = con.execute("select sum(plays) from mart_artist_daily").fetchone()[0]
raw_total = con.execute("select count(*) from raw_scrobbles").fetchone()[0]
print(f"plays in mart_artist_daily: {mart_total}, in raw_scrobbles: {raw_total}")


def show(title, sql, *params):
    print(f"\n{title}")
    for row in con.execute(sql, list(params)).fetchall():
        print(" ", row)


last7 = latest - timedelta(days=7)
last30 = latest - timedelta(days=30)

show("top 5 artists, last 7 days:",
     "select artist, sum(plays) p from mart_artist_daily where play_date > ? "
     "group by 1 order by p desc limit 5", last7)
show("top 5 genres, last 30 days:",
     "select genre, sum(plays) p from mart_artist_daily where play_date > ? "
     "group by 1 order by p desc limit 5", last30)
show("top 5 albums, last 30 days:",
     "select artist, album, sum(plays) p from mart_album_daily where play_date > ? "
     "group by 1, 2 order by p desc limit 5", last30)
show("top 5 tracks on the latest day:",
     "select artist, track, sum(plays) p from mart_track_daily where play_date = ? "
     "group by 1, 2 order by p desc limit 5", latest)
show("plays by genre family, 2025:",
     "select genre_family, sum(plays) p from mart_artist_daily "
     "where year(play_date) = 2025 group by 1 order by p desc", )
con.close()
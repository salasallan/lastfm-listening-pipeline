"""Read-only queries for the dashboard. Pure functions: connection + dates in, DataFrame out."""
from datetime import date

import duckdb
import pandas as pd

_GRAIN_SQL = {
    "day": "play_date",
    "week": "cast(date_trunc('week', play_date) as date)",
    "month": "cast(date_trunc('month', play_date) as date)",
}


def connect_readonly(path):
    return duckdb.connect(str(path), read_only=True)


def _df(con, sql, params=()):
    return con.execute(sql, list(params)).df()


def get_meta(con) -> dict:
    row = _df(con, "select * from meta").iloc[0]
    return {
        "exported_at_utc": pd.Timestamp(row["exported_at_utc"]).to_pydatetime(),
        "timezone": row["timezone"],
        "latest_play_date": pd.Timestamp(row["latest_play_date"]).date(),
        "total_plays": int(row["total_plays"]),
    }


def kpis(con, start: date, end: date) -> dict:
    plays, artists = con.execute(
        "select coalesce(sum(plays), 0), count(distinct artist) "
        "from mart_artist_daily where play_date between ? and ?",
        [start, end],
    ).fetchone()
    tracks = con.execute(
        "select count(*) from (select distinct artist, track from mart_track_daily "
        "where play_date between ? and ?)",
        [start, end],
    ).fetchone()[0]
    days = (end - start).days + 1
    return {
        "plays": int(plays),
        "artists": int(artists),
        "tracks": int(tracks),
        "days": days,
        "avg_per_day": float(plays) / days if days > 0 else 0.0,
    }


def top_artists(con, start: date, end: date, n: int = 10) -> pd.DataFrame:
    return _df(con, f"""
        select artist, genre, genre_family, cast(sum(plays) as bigint) as plays
        from mart_artist_daily
        where play_date between ? and ?
        group by artist, genre, genre_family
        order by plays desc, artist
        limit {int(n)}
    """, [start, end])


def top_albums(con, start: date, end: date, n: int = 10) -> pd.DataFrame:
    return _df(con, f"""
        select artist, album, cast(sum(plays) as bigint) as plays
        from mart_album_daily
        where play_date between ? and ?
        group by artist, album
        order by plays desc, artist, album
        limit {int(n)}
    """, [start, end])


def top_tracks(con, start: date, end: date, n: int = 10) -> pd.DataFrame:
    return _df(con, f"""
        select artist, track, cast(sum(plays) as bigint) as plays
        from mart_track_daily
        where play_date between ? and ?
        group by artist, track
        order by plays desc, artist, track
        limit {int(n)}
    """, [start, end])


def genre_family_breakdown(con, start: date, end: date) -> pd.DataFrame:
    return _df(con, """
        select genre_family, cast(sum(plays) as bigint) as plays
        from mart_artist_daily
        where play_date between ? and ?
        group by genre_family
        order by plays desc, genre_family
    """, [start, end])


def genre_breakdown(con, start: date, end: date, family: str | None = None, n: int = 15) -> pd.DataFrame:
    family_filter = "and genre_family = ?" if family else ""
    params = [start, end] + ([family] if family else [])
    return _df(con, f"""
        select genre, genre_family, cast(sum(plays) as bigint) as plays
        from mart_artist_daily
        where play_date between ? and ? {family_filter}
        group by genre, genre_family
        order by plays desc, genre
        limit {int(n)}
    """, params)


def plays_over_time(con, start: date, end: date, grain: str = "day") -> pd.DataFrame:
    if grain not in _GRAIN_SQL:
        raise ValueError(f"grain must be one of {sorted(_GRAIN_SQL)}")
    df = _df(con, f"""
        select {_GRAIN_SQL[grain]} as period, cast(sum(plays) as bigint) as plays
        from mart_artist_daily
        where play_date between ? and ?
        group by 1
        order by 1
    """, [start, end])
    df["period"] = pd.to_datetime(df["period"])
    if grain == "day":  # fill days without plays with zeros so charts show real gaps
        full = pd.DataFrame({"period": pd.date_range(start, end, freq="D")})
        df = full.merge(df, on="period", how="left")
        df["plays"] = df["plays"].fillna(0).astype("int64")
    return df


def recent_plays(con) -> pd.DataFrame:
    return _df(con, """
        select played_at_local, artist, track, album, genre, genre_family
        from mart_recent_plays
        order by played_at_local desc
    """)

_TABLES = ["mart_artist_daily", "mart_album_daily", "mart_track_daily", "mart_recent_plays", "meta"]


def load_dashboard_db(path):
    """Copy the exported tables into an in-memory DuckDB and release the file.

    The exported file is not held open, so the export script can replace it while the
    app runs; the app notices the new version through the file's modification time.
    """
    mem = duckdb.connect(":memory:")
    safe_path = str(path).replace("\\", "/").replace("'", "''")
    mem.execute(f"ATTACH '{safe_path}' AS src (READ_ONLY)")
    try:
        for table in _TABLES:
            mem.execute(f"CREATE TABLE {table} AS SELECT * FROM src.main.{table}")
    finally:
        mem.execute("DETACH src")
    return mem


def first_play_date(con) -> date:
    return pd.Timestamp(con.execute("select min(play_date) from mart_artist_daily").fetchone()[0]).date()


def all_families(con) -> list[str]:
    return [r[0] for r in con.execute(
        "select distinct genre_family from mart_artist_daily order by genre_family").fetchall()]
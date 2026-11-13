"""DuckDB access layer: schema and idempotent inserts for raw scrobbles."""
import json
from pathlib import Path

import duckdb

DEFAULT_DB_PATH = Path("data/lastfm.duckdb")

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_scrobbles (
    lastfm_user  VARCHAR   NOT NULL,
    uts          BIGINT    NOT NULL,
    artist       VARCHAR   NOT NULL,
    track        VARCHAR   NOT NULL,
    payload      JSON      NOT NULL,
    ingested_at  TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (lastfm_user, uts, artist, track)
);
"""

TAGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_artist_tags (
    artist      VARCHAR   PRIMARY KEY,
    payload     JSON      NOT NULL,
    fetched_at  TIMESTAMP NOT NULL DEFAULT current_timestamp
);
"""

def connect(db_path=DEFAULT_DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute(SCHEMA)
    con.execute(TAGS_SCHEMA)
    return con


def _text(value):
    """Artist and album arrive as {"#text": "..."} objects."""
    if isinstance(value, dict):
        return value.get("#text", "")
    return value or ""


def count_rows(con):
    return con.execute("SELECT count(*) FROM raw_scrobbles").fetchone()[0]


def uts_bounds(con, user):
    """Return (oldest_uts, newest_uts) for a user, or (None, None) if empty."""
    return con.execute(
        "SELECT min(uts), max(uts) FROM raw_scrobbles WHERE lastfm_user = ?", [user]
    ).fetchone()


def insert_plays(con, user, plays):
    """Insert plays, skipping rows that already exist. Returns rows added."""
    rows = [
        (
            user,
            int(t["date"]["uts"]),
            _text(t.get("artist")),
            t.get("name", ""),
            json.dumps(t, ensure_ascii=False),
        )
        for t in plays
    ]
    if not rows:
        return 0
    before = count_rows(con)
    #con.executemany(
    #    "INSERT INTO raw_scrobbles (lastfm_user, uts, artist, track, payload) "
    #    "VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
    #    rows,
    #)
    con.begin()
    try:
        con.executemany(
            "INSERT INTO raw_scrobbles (lastfm_user, uts, artist, track, payload) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
            rows,
        )
        con.commit()
    except Exception:
        con.rollback()
        raise

    return count_rows(con) - before

def artists_missing_tags(con):
    """Artists with plays but no stored tags yet, most-played first."""
    return [
        row[0]
        for row in con.execute(
            """
            SELECT artist FROM (
                SELECT artist, count(*) AS plays FROM raw_scrobbles GROUP BY artist
            )
            WHERE artist NOT IN (SELECT artist FROM raw_artist_tags)
            ORDER BY plays DESC
            """
        ).fetchall()
    ]

def insert_artist_tags(con, artist, tags):
    """Store an artist's tag list as JSON. An empty list means 'fetched, no tags'."""
    con.execute(
        "INSERT INTO raw_artist_tags (artist, payload) VALUES (?, ?) ON CONFLICT DO NOTHING",
        [artist, json.dumps(tags, ensure_ascii=False)],
    )
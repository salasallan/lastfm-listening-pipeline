from datetime import datetime, timezone

from lastfm_pipeline.db import connect

con = connect()
total, first, last = con.execute(
    "SELECT count(*), min(uts), max(uts) FROM raw_scrobbles"
).fetchone()


def fmt(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


print(f"rows: {total}, oldest: {fmt(first)}, newest: {fmt(last)}")
print("top artists:")
for artist, plays in con.execute(
    "SELECT artist, count(*) AS plays FROM raw_scrobbles "
    "GROUP BY artist ORDER BY plays DESC LIMIT 5"
).fetchall():
    print(f"  {artist}: {plays}")
con.close()
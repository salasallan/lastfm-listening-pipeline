import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

from lastfm_pipeline.client import fetch_recent_tracks_page

load_dotenv()
user = os.getenv("LASTFM_USER")
api_key = os.getenv("LASTFM_API_KEY")


def fmt(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


to_ts = int(time.time())  # frozen upper bound
for page in (1, 2):
    plays, attr = fetch_recent_tracks_page(user, api_key, page=page, limit=200, to_ts=to_ts)
    first, last = int(plays[0]["date"]["uts"]), int(plays[-1]["date"]["uts"])
    print(f"page {page}/{attr['totalPages']}: {len(plays)} plays, {fmt(first)} -> {fmt(last)}")
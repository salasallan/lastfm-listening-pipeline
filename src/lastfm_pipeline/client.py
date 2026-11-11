"""Last.fm API client: fetches pages of scrobbles with retries."""
import time

import requests

API_URL = "https://ws.audioscrobbler.com/2.0/"
RETRYABLE_HTTP = {429, 500, 502, 503, 504}
RETRYABLE_API_ERRORS = {11, 16, 29}  # service offline, temporary error, rate limit


class LastFmError(Exception):
    pass


def fetch_recent_tracks_page(user, api_key, page=1, limit=200,
                             to_ts=None, from_ts=None, max_retries=5):
    """Return (plays, pagination_attrs) for one page, keeping only items with a timestamp."""
    params = {
        "method": "user.getrecenttracks",
        "user": user,
        "api_key": api_key,
        "format": "json",
        "limit": limit,
        "page": page,
    }
    if to_ts is not None:
        params["to"] = to_ts
    if from_ts is not None:
        params["from"] = from_ts

    for attempt in range(max_retries):
        wait = 2 ** attempt
        try:
            response = requests.get(API_URL, params=params, timeout=30)
        except requests.RequestException:
            time.sleep(wait)
            continue
        if response.status_code in RETRYABLE_HTTP:
            time.sleep(wait)
            continue

        data = response.json()
        if "error" in data:
            if data["error"] in RETRYABLE_API_ERRORS:
                time.sleep(wait)
                continue
            raise LastFmError(f"API error {data['error']}: {data.get('message')}")
        response.raise_for_status()

        recent = data["recenttracks"]
        tracks = recent["track"]
        if isinstance(tracks, dict):
            tracks = [tracks]
        plays = [t for t in tracks if "date" in t]
        return plays, recent["@attr"]

    raise LastFmError(f"Failed after {max_retries} attempts (page {page})")
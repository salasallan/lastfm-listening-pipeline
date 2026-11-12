"""Explore the Last.fm user.getRecentTracks response (Phase 2)."""
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

API_URL = "https://ws.audioscrobbler.com/2.0/"


def main() -> None:
    load_dotenv()
    api_key = os.getenv("LASTFM_API_KEY")
    user = os.getenv("LASTFM_USER")
    if not api_key or not user:
        raise SystemExit("Missing LASTFM_API_KEY or LASTFM_USER in .env")

    params = {
        "method": "user.getrecenttracks",
        "user": user,
        "api_key": api_key,
        "format": "json",
        "limit": 5,
        "page": 1,
    }
    response = requests.get(API_URL, params=params, timeout=30)
    print("HTTP status:", response.status_code)

    data = response.json()
    if "error" in data:
        raise SystemExit(f"API error {data['error']}: {data.get('message')}")
    response.raise_for_status()

    recent = data["recenttracks"]
    print("\nPagination info:")
    print(json.dumps(recent["@attr"], indent=2, ensure_ascii=False))

    tracks = recent["track"]
    if isinstance(tracks, dict):  # defensive: a single item may not come as a list
        tracks = [tracks]
    print(f"\nTracks returned: {len(tracks)}")
    print("\nFirst track:")
    print(json.dumps(tracks[0], indent=2, ensure_ascii=False))

    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "sample_recent_tracks.json"
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved full sample to {out_file}")


if __name__ == "__main__":
    main()
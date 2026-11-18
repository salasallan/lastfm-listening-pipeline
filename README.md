# Last.fm Listening Pipeline

An end-to-end data pipeline and dashboard built on my own Last.fm listening history:
Python ingestion → DuckDB → dbt models and tests → Streamlit dashboard.

> Live dashboard: _coming soon_

## What it does

- Backfills the full scrobble history, then loads new plays incrementally (idempotent, with a lookback window for late scrobbles).
- Assigns every artist a single genre (from Last.fm tags, through a curated mapping) and a genre family.
- Builds daily marts with dbt (data tests included) and exports a small file for the dashboard.
- Streamlit dashboard: top artists, albums, tracks and genres for any date range, plus the latest plays.

## Architecture

Last.fm API → `src/lastfm_pipeline` (client, ingestion, database access) → DuckDB raw tables →
dbt (staging, genre dimension, daily marts) → `scripts/export_dashboard_data.py` →
a small standalone DuckDB file → `dashboard/app.py`

## Repository layout

```
src/lastfm_pipeline/   API client, ingestion and database access
scripts/               pipeline entry points (load_history, run_pipeline, ...)
scripts/exploration/   one-off exploration and review helpers
scripts/maintenance/   migration helpers
dbt/                   dbt project: models, tests, seeds (genre mapping)
dashboard/             Streamlit app and its queries
docs/                  project document and learning log
```

## Setup (PowerShell)

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env        # then fill in your values
$env:PYTHONPATH = "src"
python scripts/load_history.py     # one-time backfill (15-30 minutes)
python scripts/run_pipeline.py     # ingest, tags, dbt build, export
streamlit run dashboard/app.py
```

## Configuration (`.env`)

| Variable | Purpose |
|---|---|
| `LASTFM_API_KEY` | Your Last.fm API key (free at last.fm/api) |
| `LASTFM_USER` | Your Last.fm username |
| `LASTFM_TIMEZONE` | IANA timezone used for local dates and hours (default `UTC`) |
| `LASTFM_DB_PATH` | Optional: path of the DuckDB file used by dbt |
| `LASTFM_DASHBOARD_DB` | Optional: path of the exported file read by the dashboard |

## Data and privacy

The repository contains no listening data. The dashboard publishes daily aggregates and the
latest 100 plays only.

## Attribution and terms

Listening data comes from [Last.fm](https://www.last.fm). This is a personal, non-commercial
project, and the use of Last.fm data is subject to the Last.fm API Terms of Service.

## License

MIT
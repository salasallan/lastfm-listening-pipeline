"""Streamlit dashboard: top artists, albums, tracks and genres for a chosen date range."""
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import shutil
import tempfile
import urllib.request

import altair as alt
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import queries as q  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

PALETTE = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948",
           "#b07aa1", "#ff9da7", "#9c755f", "#86bc86", "#d37295", "#8cd17d"]
GREY = "#9aa0a6"

PRESETS = ["Yesterday", "Last 7 days", "Last 30 days", "This month", "Last month",
           "This year", "All time", "Custom range"]

GRAINS = ["day", "week", "month"]

DEFAULT_DATA_URL = (
    "https://github.com/salasallan/lastfm-listening-pipeline/"
    "releases/download/data/dashboard.duckdb"
)
CACHE_TTL_SECONDS = 15 * 60

st.set_page_config(page_title="My Music Wrapped", page_icon="🎧", layout="wide")

#def resolve_db_path() -> Path:
#    configured = os.getenv("LASTFM_DASHBOARD_DB")
#    if configured:
#        path = Path(configured)
#        return path if path.is_absolute() else ROOT / path
#    return ROOT / "data" / "dashboard.duckdb"

def local_db_path():
    configured = os.getenv("LASTFM_DASHBOARD_DB")
    if configured:
        path = Path(configured)
        return path if path.is_absolute() else ROOT / path
    default = ROOT / "data" / "dashboard.duckdb"
    return default if default.exists() else None

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner="Downloading the latest data...")
def download_db(url: str) -> str:
    """Download the exported file to a temp folder; keep the previous copy if the download fails."""
    target = Path(tempfile.gettempdir()) / "lastfm_dashboard" / "dashboard.duckdb"
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".part")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "lastfm-listening-pipeline-dashboard"})
        with urllib.request.urlopen(request, timeout=60) as response, open(part, "wb") as out:
            shutil.copyfileobj(response, out)
        part.replace(target)
    except Exception as exc:  # network error, missing asset, ...
        part.unlink(missing_ok=True)
        if not target.exists():
            raise RuntimeError(f"Could not download the data file: {exc}") from exc
    return str(target)

def resolve_db_path() -> Path:
    forced_url = os.getenv("LASTFM_DASHBOARD_URL")
    if not forced_url:
        local = local_db_path()
        if local is not None:
            return local
    return Path(download_db(forced_url or DEFAULT_DATA_URL))

@st.cache_resource(max_entries=2, show_spinner="Loading data...")
def get_connection(db_path: str, version: float):
    return q.load_dashboard_db(db_path)


def period_for(preset: str, today: date, first_day: date):
    if preset == "Yesterday":
        day = today - timedelta(days=1)
        return day, day
    if preset == "Last 7 days":
        return today - timedelta(days=6), today
    if preset == "Last 30 days":
        return today - timedelta(days=29), today
    if preset == "This month":
        return today.replace(day=1), today
    if preset == "Last month":
        end = today.replace(day=1) - timedelta(days=1)
        return end.replace(day=1), end
    if preset == "This year":
        return date(today.year, 1, 1), today
    return first_day, today  # All time


def fmt_day(day: date) -> str:
    return day.strftime("%b %d, %Y")


def family_scale(families):
    named = [f for f in families if f not in ("Other", "Unknown")]
    greys = [f for f in ("Other", "Unknown") if f in families]
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(named))] + [GREY] * len(greys)
    return alt.Scale(domain=named + greys, range=colors)


def bar_chart(df, label_col, tooltips, color=None):
    mark = alt.Chart(df).mark_bar() if color is not None else alt.Chart(df).mark_bar(color=PALETTE[0])
    encoding = dict(
        x=alt.X("plays:Q", title="Plays"),
        y=alt.Y(f"{label_col}:N", sort="-x", title=None, axis=alt.Axis(labelLimit=320)),
        tooltip=tooltips,
    )
    if color is not None:
        encoding["color"] = color
    return mark.encode(**encoding).properties(height=max(140, 26 * len(df)), width="container")


def show_table(df, rename):
    table = df.rename(columns=rename).copy()
    table.insert(0, "#", range(1, len(table) + 1))
    st.dataframe(table, hide_index=True)


#db_path = resolve_db_path()
#if not db_path.exists():
#    st.error(f"Data file not found: {db_path}. Run scripts/export_dashboard_data.py first.")
#    st.stop()

try:
    db_path = resolve_db_path()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()
if not db_path.exists():
    st.error(f"Data file not found: {db_path}. Run scripts/export_dashboard_data.py first.")
    st.stop()

con = get_connection(str(db_path), db_path.stat().st_mtime).cursor()
meta = q.get_meta(con)
tz = ZoneInfo(meta["timezone"])
today = datetime.now(tz).date()
first_day = q.first_play_date(con)
families = q.all_families(con)
scale = family_scale(families)

# ---- Sidebar filters ----
st.sidebar.header("Filters")
preset = st.sidebar.radio("Period", PRESETS, index=2)
if preset == "Custom range":
    picked = st.sidebar.date_input(
        "Dates", value=(today - timedelta(days=29), today), min_value=first_day, max_value=today
    )
    if not isinstance(picked, (tuple, list)) or len(picked) != 2:
        st.info("Pick a start and an end date in the sidebar.")
        st.stop()
    start, end = picked
else:
    start, end = period_for(preset, today, first_day)
top_n = st.sidebar.slider("Items shown", 5, 25, 10)

# ---- Header and KPIs ----
updated = meta["exported_at_utc"].replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
st.title("Music Scrobbles Dashboard")
st.caption(
    f"Source: Last.fm scrobbles · latest play: {fmt_day(meta['latest_play_date'])} · "
    f"data updated {updated:%b %d, %Y %H:%M} (local time)"
)
st.subheader(fmt_day(start) if start == end else f"{fmt_day(start)} – {fmt_day(end)}")

k = q.kpis(con, start, end)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Plays", f"{k['plays']:,}")
c2.metric("Artists", f"{k['artists']:,}")
c3.metric("Tracks", f"{k['tracks']:,}")
c4.metric("Avg plays / day", f"{k['avg_per_day']:.1f}")

if k["plays"] == 0:
    st.info("No plays in this period.")
    st.stop()

tab_artists, tab_albums, tab_tracks, tab_genres, tab_time, tab_recent = st.tabs(
    ["Artists", "Albums", "Tracks", "Genres", "Over time", "Recent plays"]
)

with tab_artists:
    df = q.top_artists(con, start, end, top_n)
    color = alt.Color("genre_family:N", scale=scale, legend=alt.Legend(title="Family"))
    st.altair_chart(bar_chart(df, "artist", ["artist:N", "genre:N", "genre_family:N", "plays:Q"], color))
    show_table(df, {"artist": "Artist", "genre": "Genre", "genre_family": "Family", "plays": "Plays"})

with tab_albums:
    df = q.top_albums(con, start, end, top_n)
    df["label"] = df["artist"] + " — " + df["album"]
    st.altair_chart(bar_chart(df, "label", ["artist:N", "album:N", "plays:Q"]))
    st.caption("Plays without album information are not included.")
    show_table(df[["artist", "album", "plays"]], {"artist": "Artist", "album": "Album", "plays": "Plays"})

with tab_tracks:
    df = q.top_tracks(con, start, end, top_n)
    df["label"] = df["artist"] + " — " + df["track"]
    st.altair_chart(bar_chart(df, "label", ["artist:N", "track:N", "plays:Q"]))
    show_table(df[["artist", "track", "plays"]], {"artist": "Artist", "track": "Track", "plays": "Plays"})

with tab_genres:
    fam_df = q.genre_family_breakdown(con, start, end)
    st.markdown("**By genre family**")
    st.altair_chart(bar_chart(
        fam_df, "genre_family", ["genre_family:N", "plays:Q"],
        alt.Color("genre_family:N", scale=scale, legend=None),
    ))
    fam_table = fam_df.copy()
    fam_table["share"] = (fam_table["plays"] / fam_table["plays"].sum() * 100).round(1).astype(str) + "%"
    show_table(fam_table, {"genre_family": "Family", "plays": "Plays", "share": "Share"})

    choice = st.selectbox("Genres within a family", ["All families"] + list(fam_df["genre_family"]))
    gen_df = q.genre_breakdown(con, start, end, None if choice == "All families" else choice, top_n)
    st.markdown("**By genre**")
    st.altair_chart(bar_chart(
        gen_df, "genre", ["genre:N", "genre_family:N", "plays:Q"],
        alt.Color("genre_family:N", scale=scale, legend=None),
    ))
    st.caption(
        "Each artist is assigned a single genre: the highest-weighted Last.fm tag that "
        "belongs to a recognized genre. 'Unknown' means no tags; 'Other' means no recognized genre."
    )

with tab_time:
    span = (end - start).days + 1
    default_grain = "day" if span <= 62 else ("week" if span <= 400 else "month")
    grain = st.radio("Group by", GRAINS, index=GRAINS.index(default_grain),
                     horizontal=True, key=f"grain-{default_grain}")
    series = q.plays_over_time(con, start, end, grain)
    chart = alt.Chart(series).mark_bar(color=PALETTE[0]).encode(
        x=alt.X("period:T", title=None),
        y=alt.Y("plays:Q", title="Plays"),
        tooltip=[alt.Tooltip("period:T", title="Period start"), alt.Tooltip("plays:Q", title="Plays")],
    ).properties(height=320, width="container")
    st.altair_chart(chart)
    st.caption("The first and last periods can be partial.")

with tab_recent:
    recent = q.recent_plays(con)
    st.caption(f"Latest {len(recent)} plays, in local time.")
    recent = recent.rename(columns={
        "played_at_local": "Played at", "artist": "Artist", "track": "Track",
        "album": "Album", "genre": "Genre", "genre_family": "Family",
    })
    st.dataframe(
        recent, hide_index=True,
        column_config={"Played at": st.column_config.DatetimeColumn("Played at", format="YYYY-MM-DD HH:mm")},
    )

st.divider()
st.caption("Listening data from [Last.fm](https://www.last.fm). Personal, non-commercial project.")
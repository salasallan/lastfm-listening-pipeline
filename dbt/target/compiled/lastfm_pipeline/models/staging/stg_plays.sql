-- Staging model: one row per play, typed and flattened from raw_scrobbles.
select
    lastfm_user,
    uts                                                          as played_at_uts,
    make_timestamp(uts * 1000000)                                as played_at_utc,
    timezone('America/Costa_Rica', to_timestamp(uts))   as played_at_local,
    artist,
    track,
    nullif(json_extract_string(payload, '$.album."#text"'), '')  as album,
    nullif(json_extract_string(payload, '$.artist.mbid'), '')    as artist_mbid,
    nullif(json_extract_string(payload, '$.album.mbid'), '')     as album_mbid,
    nullif(json_extract_string(payload, '$.mbid'), '')           as track_mbid,
    json_extract_string(payload, '$.url')                        as track_url,
    ingested_at
from "lastfm"."main"."raw_scrobbles"
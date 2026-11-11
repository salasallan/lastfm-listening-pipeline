-- Staging model: one row per play, typed and flattened from raw_scrobbles.
SELECT
    lastfm_user,
    uts                                                          AS played_at_uts,
    make_timestamp(uts * 1000000)                                AS played_at_utc,
    artist,
    track,
    NULLIF(json_extract_string(payload, '$.album."#text"'), '')  AS album,
    NULLIF(json_extract_string(payload, '$.artist.mbid'), '')    AS artist_mbid,
    NULLIF(json_extract_string(payload, '$.album.mbid'), '')     AS album_mbid,
    NULLIF(json_extract_string(payload, '$.mbid'), '')           AS track_mbid,
    json_extract_string(payload, '$.url')                        AS track_url,
    ingested_at
FROM raw_scrobbles
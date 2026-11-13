-- The most recent plays (local time), with genre. This is the only play-level table that is
-- published; the window size can be changed with the recent_plays_limit variable.
select
    p.played_at_local,
    p.artist,
    p.track,
    p.album,
    g.genre,
    g.genre_family
from {{ ref('stg_plays') }} p
join {{ ref('dim_artist_genre') }} g on g.artist = p.artist
order by p.played_at_utc desc
limit {{ var('recent_plays_limit', 100) }}
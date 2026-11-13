-- Plays per artist + album per day. Plays without an album are excluded.
-- The key is the artist/album pair because different artists can share album names.
select
    cast(played_at_local as date) as play_date,
    artist,
    album,
    count(*) as plays
from "lastfm"."main"."stg_plays"
where album is not null
group by 1, 2, 3
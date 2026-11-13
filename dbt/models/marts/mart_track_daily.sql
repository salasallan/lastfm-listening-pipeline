-- Plays per artist + track per day.
select
    cast(played_at_local as date) as play_date,
    artist,
    track,
    count(*) as plays
from {{ ref('stg_plays') }}
group by 1, 2, 3

    

    create  table
      "lastfm"."main"."mart_track_daily__dbt_tmp"
  
    
    as (
      -- Plays per artist + track per day.
select
    cast(played_at_local as date) as play_date,
    artist,
    track,
    count(*) as plays
from "lastfm"."main"."stg_plays"
group by 1, 2, 3
    );
    
  
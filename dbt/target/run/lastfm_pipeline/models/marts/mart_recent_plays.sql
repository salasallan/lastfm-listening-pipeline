
    

    create  table
      "lastfm"."main"."mart_recent_plays__dbt_tmp"
  
    
    as (
      -- The most recent plays (local time), with genre. This is the only play-level table that is
-- published; the window size can be changed with the recent_plays_limit variable.
select
    p.played_at_local,
    p.artist,
    p.track,
    p.album,
    g.genre,
    g.genre_family
from "lastfm"."main"."stg_plays" p
join "lastfm"."main"."dim_artist_genre" g on g.artist = p.artist
order by p.played_at_utc desc
limit 100
    );
    
  
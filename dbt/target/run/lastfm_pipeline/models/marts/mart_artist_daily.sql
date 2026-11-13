
    

    create  table
      "lastfm"."main"."mart_artist_daily__dbt_tmp"
  
    
    as (
      -- Plays per artist per day (local date), with the artist's single genre and genre family.
-- Genre totals come from summing this table, since each artist has exactly one genre.
select
    cast(p.played_at_local as date) as play_date,
    p.artist,
    g.genre,
    g.genre_family,
    count(*) as plays
from "lastfm"."main"."stg_plays" p
join "lastfm"."main"."dim_artist_genre" g on g.artist = p.artist
group by 1, 2, 3, 4
    );
    
  
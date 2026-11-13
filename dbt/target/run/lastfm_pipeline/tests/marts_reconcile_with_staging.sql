
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Fails if a mart's total plays differ from what staging says it should be.
with checks as (
    select 'artist_daily' as mart,
           (select sum(plays) from "lastfm"."main"."mart_artist_daily") as mart_plays,
           (select count(*) from "lastfm"."main"."stg_plays") as expected_plays
    union all
    select 'track_daily',
           (select sum(plays) from "lastfm"."main"."mart_track_daily"),
           (select count(*) from "lastfm"."main"."stg_plays")
    union all
    select 'album_daily',
           (select sum(plays) from "lastfm"."main"."mart_album_daily"),
           (select count(*) from "lastfm"."main"."stg_plays" where album is not null)
)
select * from checks where mart_plays != expected_plays
  
  
      
    ) dbt_internal_test
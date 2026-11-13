
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Fails if the dimension has a different number of artists than raw_scrobbles.
select raw_artists, dim_artists
from (
    select
        (select count(distinct artist) from "lastfm"."main"."raw_scrobbles") as raw_artists,
        (select count(*) from "lastfm"."main"."dim_artist_genre") as dim_artists
)
where raw_artists != dim_artists
  
  
      
    ) dbt_internal_test

    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select artist
from "lastfm"."main"."dim_artist_genre"
where artist is null



  
  
      
    ) dbt_internal_test
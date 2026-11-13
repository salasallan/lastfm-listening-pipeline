
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select artist
from "lastfm"."main"."mart_track_daily"
where artist is null



  
  
      
    ) dbt_internal_test
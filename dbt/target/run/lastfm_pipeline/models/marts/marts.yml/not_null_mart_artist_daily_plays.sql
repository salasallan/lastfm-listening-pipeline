
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select plays
from "lastfm"."main"."mart_artist_daily"
where plays is null



  
  
      
    ) dbt_internal_test
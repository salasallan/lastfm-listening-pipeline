
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select play_date
from "lastfm"."main"."mart_artist_daily"
where play_date is null



  
  
      
    ) dbt_internal_test
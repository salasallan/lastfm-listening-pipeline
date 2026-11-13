
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select genre
from "lastfm"."main"."mart_recent_plays"
where genre is null



  
  
      
    ) dbt_internal_test
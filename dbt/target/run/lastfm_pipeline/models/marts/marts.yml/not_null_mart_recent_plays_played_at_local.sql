
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select played_at_local
from "lastfm"."main"."mart_recent_plays"
where played_at_local is null



  
  
      
    ) dbt_internal_test
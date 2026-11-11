
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select played_at_utc
from "lastfm"."main"."stg_plays"
where played_at_utc is null



  
  
      
    ) dbt_internal_test
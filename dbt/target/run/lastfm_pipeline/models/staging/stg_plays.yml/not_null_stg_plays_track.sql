
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select track
from "lastfm"."main"."stg_plays"
where track is null



  
  
      
    ) dbt_internal_test
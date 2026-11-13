
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select tag
from "lastfm"."main"."genre_mapping"
where tag is null



  
  
      
    ) dbt_internal_test
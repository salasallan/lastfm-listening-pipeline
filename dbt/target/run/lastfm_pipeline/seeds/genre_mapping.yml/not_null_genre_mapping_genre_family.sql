
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select genre_family
from "lastfm"."main"."genre_mapping"
where genre_family is null



  
  
      
    ) dbt_internal_test
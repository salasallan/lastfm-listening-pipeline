
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select artist
from "lastfm"."main"."stg_artist_tags"
where artist is null



  
  
      
    ) dbt_internal_test
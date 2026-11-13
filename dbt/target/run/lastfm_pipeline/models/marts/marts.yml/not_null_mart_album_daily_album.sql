
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select album
from "lastfm"."main"."mart_album_daily"
where album is null



  
  
      
    ) dbt_internal_test
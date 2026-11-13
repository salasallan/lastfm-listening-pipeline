
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select genre_family
from "lastfm"."main"."dim_artist_genre"
where genre_family is null



  
  
      
    ) dbt_internal_test
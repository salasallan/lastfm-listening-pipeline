
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    tag as unique_field,
    count(*) as n_records

from "lastfm"."main"."genre_mapping"
where tag is not null
group by tag
having count(*) > 1



  
  
      
    ) dbt_internal_test
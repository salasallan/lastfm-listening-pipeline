
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Fails if mart_recent_plays is not exactly the newest N plays of staging.
-- (Two plays at the exact same second on the window boundary could trigger a false alarm.)
with bounds as (
    select min(played_at_local) as oldest, count(*) as n
    from "lastfm"."main"."mart_recent_plays"
)
select b.n, count(*) as plays_in_staging_since_oldest
from "lastfm"."main"."stg_plays" p, bounds b
where p.played_at_local >= b.oldest
group by b.n
having count(*) != b.n
  
  
      
    ) dbt_internal_test
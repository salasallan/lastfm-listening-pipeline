
    
    

select
    tag as unique_field,
    count(*) as n_records

from "lastfm"."main"."genre_mapping"
where tag is not null
group by tag
having count(*) > 1




    
    

select
    artist as unique_field,
    count(*) as n_records

from "lastfm"."main"."dim_artist_genre"
where artist is not null
group by artist
having count(*) > 1



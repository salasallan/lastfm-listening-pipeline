
    

    create  table
      "lastfm"."main"."dim_artist_genre__dbt_tmp"
  
    
    as (
      -- One row per artist with a single genre: the highest-weighted tag that appears in genre_mapping.
-- 'unknown' = no tags at all; 'other' = has tags, but none is in the mapping.
with artists as (
    select distinct artist
    from "lastfm"."main"."raw_scrobbles"
),

artists_with_tags as (
    select distinct artist
    from "lastfm"."main"."stg_artist_tags"
),

mapped_tags as (
    select
        t.artist,
        m.genre,
        m.genre_family,
        row_number() over (
            partition by t.artist
            order by t.tag_count desc, m.genre
        ) as rn
    from "lastfm"."main"."stg_artist_tags" t
    join "lastfm"."main"."genre_mapping" m
        on t.tag = lower(m.tag)
)

select
    a.artist,
    case
        when b.genre is not null then b.genre
        when w.artist is not null then 'other'
        else 'unknown'
    end as genre,
    case
        when b.genre_family is not null then b.genre_family
        when w.artist is not null then 'Other'
        else 'Unknown'
    end as genre_family
from artists a
left join (select * from mapped_tags where rn = 1) b on b.artist = a.artist
left join artists_with_tags w on w.artist = a.artist
    );
    
  
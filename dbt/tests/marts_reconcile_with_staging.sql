-- Fails if a mart's total plays differ from what staging says it should be.
with checks as (
    select 'artist_daily' as mart,
           (select sum(plays) from {{ ref('mart_artist_daily') }}) as mart_plays,
           (select count(*) from {{ ref('stg_plays') }}) as expected_plays
    union all
    select 'track_daily',
           (select sum(plays) from {{ ref('mart_track_daily') }}),
           (select count(*) from {{ ref('stg_plays') }})
    union all
    select 'album_daily',
           (select sum(plays) from {{ ref('mart_album_daily') }}),
           (select count(*) from {{ ref('stg_plays') }} where album is not null)
)
select * from checks where mart_plays != expected_plays
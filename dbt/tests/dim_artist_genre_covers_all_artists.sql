-- Fails if the dimension has a different number of artists than raw_scrobbles.
select raw_artists, dim_artists
from (
    select
        (select count(distinct artist) from {{ source('lastfm', 'raw_scrobbles') }}) as raw_artists,
        (select count(*) from {{ ref('dim_artist_genre') }}) as dim_artists
)
where raw_artists != dim_artists
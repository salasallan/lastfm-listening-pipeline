-- One row per artist tag, flattened from the JSON array in raw_artist_tags.
-- Artists whose tag list is empty produce no rows.
select
    artist,
    lower(json_extract_string(tag, '$.name'))                as tag,
    cast(json_extract_string(tag, '$.count') as integer)     as tag_count
from (
    select artist, unnest(from_json(payload, '["JSON"]')) as tag
    from {{ source('lastfm', 'raw_artist_tags') }}
)
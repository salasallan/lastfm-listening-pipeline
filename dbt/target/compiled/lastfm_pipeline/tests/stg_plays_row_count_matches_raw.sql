-- Returns a row (and fails) when staging and raw row counts differ.
select raw_count, stg_count
from (
    select
        (select count(*) from "lastfm"."main"."raw_scrobbles") as raw_count,
        (select count(*) from "lastfm"."main"."stg_plays")                  as stg_count
)
where raw_count != stg_count
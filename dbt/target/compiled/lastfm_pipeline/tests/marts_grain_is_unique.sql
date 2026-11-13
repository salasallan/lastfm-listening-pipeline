-- Fails if any mart has duplicate rows at its declared grain.
select 'artist_daily' as mart, play_date::varchar as k1, artist as k2, '' as k3
from "lastfm"."main"."mart_artist_daily"
group by play_date, artist
having count(*) > 1

union all

select 'album_daily', play_date::varchar, artist, album
from "lastfm"."main"."mart_album_daily"
group by play_date, artist, album
having count(*) > 1

union all

select 'track_daily', play_date::varchar, artist, track
from "lastfm"."main"."mart_track_daily"
group by play_date, artist, track
having count(*) > 1
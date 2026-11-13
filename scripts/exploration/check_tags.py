"""Check the real distribution of top-1 tags once the enrichment has finished."""
import duckdb

con = duckdb.connect("data/lastfm.duckdb", read_only=True)

total, empty = con.execute(
    "select count(*), count(*) filter (where json_array_length(payload) = 0) "
    "from raw_artist_tags"
).fetchone()
print(f"artists with stored tags: {total}, with an empty tag list: {empty}")

total_plays = con.execute("select count(*) from raw_scrobbles").fetchone()[0]
print("\ntop 30 top-1 tags by plays:")
for genre, plays, artists in con.execute("""
    with top1 as (
        select artist, lower(json_extract_string(payload, '$[0].name')) as genre
        from raw_artist_tags
    )
    select coalesce(t.genre, '(no tags)') as genre,
           count(*) as plays,
           count(distinct s.artist) as artists
    from raw_scrobbles s
    left join top1 t using (artist)
    group by 1
    order by plays desc
    limit 30
""").fetchall():
    print(f"  {genre}: {plays} plays ({plays / total_plays:.1%}), {artists} artists")

con.close()
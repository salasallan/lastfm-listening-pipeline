"""Review the genre assignment: shares by family and genre, and artists left in 'other'."""
import duckdb

con = duckdb.connect("data/lastfm.duckdb", read_only=True)
total = con.execute("select count(*) from raw_scrobbles").fetchone()[0]

print("plays by genre family:")
for fam, plays in con.execute("""
    select d.genre_family, count(*) as plays
    from raw_scrobbles s join dim_artist_genre d using (artist)
    group by 1 order by plays desc
""").fetchall():
    print(f"  {fam}: {plays} ({plays / total:.1%})")

print("\ntop 25 genres:")
for genre, plays, artists in con.execute("""
    select d.genre, count(*) as plays, count(distinct s.artist) as artists
    from raw_scrobbles s join dim_artist_genre d using (artist)
    group by 1 order by plays desc limit 25
""").fetchall():
    print(f"  {genre}: {plays} ({plays / total:.1%}), {artists} artists")

print("\ntop 20 artists left in 'other' (first three tags):")
for artist, plays, t1, t2, t3 in con.execute("""
    select d.artist, count(*) as plays,
           json_extract_string(r.payload, '$[0].name'),
           json_extract_string(r.payload, '$[1].name'),
           json_extract_string(r.payload, '$[2].name')
    from raw_scrobbles s
    join dim_artist_genre d using (artist)
    join raw_artist_tags r using (artist)
    where d.genre = 'other'
    group by d.artist, r.payload
    order by plays desc limit 20
""").fetchall():
    print(f"  {artist} ({plays} plays): {t1} | {t2} | {t3}")

con.close()
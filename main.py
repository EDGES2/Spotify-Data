import json
import glob
import os
import pandas as pd

# Форматуємо секунди в HHh MMm SSs
def format_hms(total_seconds: float) -> str:
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

# Перетворюємо список років у компактний рядок, наприклад: [2021,2023,2024,2025] → "2021, 2023-2025"
def format_years(years: list[int]) -> str:
    if not years:
        return ""
    years = sorted(set(years))
    ranges = []
    start = prev = years[0]
    for y in years[1:]:
        if y == prev + 1:
            prev = y
        else:
            ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
            start = prev = y
    ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ", ".join(ranges)

# Обробка даних у Spotify Streaming History
def process_spotify_data(file_pattern: str):
    files = glob.glob(file_pattern)
    if not files:
        raise FileNotFoundError(f"Жоден файл за шаблоном '{file_pattern}' не знайдено")

    data = []
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            content = json.load(f)
            if isinstance(content, dict):
                data.append(content)
            else:
                data.extend(content)

    df = pd.DataFrame(data)
    df['ts'] = pd.to_datetime(df['ts'])
    df['year'] = df['ts'].dt.year
    df['seconds_played'] = df.get('ms_played', 0) / 1000.0

    # Загальні обчислення
    total_seconds = df['seconds_played'].sum()
    sec_per_year = df.groupby('year')['seconds_played'].sum().reset_index()

    # Роки прослуховувань для треків та авторів
    years_per_track = (
        df.groupby(['master_metadata_track_name', 'spotify_track_uri'])['year']
          .apply(lambda yrs: sorted(set(yrs)))
          .reset_index(name='years_list')
    )
    years_per_author = (
        df.groupby('master_metadata_album_artist_name')['year']
          .apply(lambda yrs: sorted(set(yrs)))
          .to_dict()
    )

    # Топ-5 треків за рік
    track_year = (
        df.groupby(['year', 'master_metadata_track_name', 'spotify_track_uri'])
          .agg(seconds_played=('seconds_played', 'sum'), plays=('master_metadata_track_name', 'count'))
          .reset_index()
    )
    top5_per_year = (
        track_year
        .sort_values(['year', 'seconds_played'], ascending=[True, False])
        .groupby('year').head(5)
        .merge(years_per_track, on=['master_metadata_track_name', 'spotify_track_uri'], how='left')
    )

    # Топ-5 авторів за рік
    author_year = (
        df.groupby(['year', 'master_metadata_album_artist_name'])
          .agg(seconds_played=('seconds_played', 'sum'), plays=('master_metadata_track_name', 'count'))
          .reset_index()
    )
    top5_authors_per_year = (
        author_year
        .sort_values(['year', 'seconds_played'], ascending=[True, False])
        .groupby('year').head(5)
        .assign(years_list=lambda d: d['master_metadata_album_artist_name'].map(years_per_author))
    )

    # Топ-10 треків за весь час
    track_overall = (
        df.groupby(['master_metadata_track_name', 'spotify_track_uri'])
          .agg(seconds_played=('seconds_played', 'sum'), plays=('master_metadata_track_name', 'count'))
          .reset_index()
    )
    top10_overall = (
        track_overall
        .merge(years_per_track, on=['master_metadata_track_name', 'spotify_track_uri'], how='left')
        .sort_values('seconds_played', ascending=False)
        .head(10)
    )

    # Топ-15 авторів за весь час
    author_stats = (
        df.groupby('master_metadata_album_artist_name')
          .agg(total_seconds=('seconds_played', 'sum'), plays=('master_metadata_track_name', 'count'))
          .reset_index()
          .sort_values('total_seconds', ascending=False)
          .head(15)
    )

    # Топ-5 треків авторів
    author_top_tracks = (
        df.groupby(['master_metadata_album_artist_name', 'master_metadata_track_name', 'spotify_track_uri'])
          .agg(seconds_played=('seconds_played', 'sum'), plays=('master_metadata_track_name', 'count'))
          .reset_index()
    )
    author_top5 = (
        author_top_tracks[author_top_tracks['plays'] > 5]
        .sort_values(['master_metadata_album_artist_name', 'seconds_played'], ascending=[True, False])
        .groupby('master_metadata_album_artist_name').head(5)
        .merge(years_per_track, on=['master_metadata_track_name', 'spotify_track_uri'], how='left')
    )

    return total_seconds, sec_per_year, top5_per_year, top5_authors_per_year, top10_overall, author_stats, author_top5, years_per_author

if __name__ == "__main__":
    (total_seconds, sec_per_year, top5_per_year, top5_authors_per_year,
     top10_overall, author_stats, author_top5, years_per_author) = \
        process_spotify_data('data/Streaming_History_Audio_*.json')

    stats_dir = 'stats'
    os.makedirs(stats_dir, exist_ok=True)
    # Очищуємо теку
    for fn in os.listdir(stats_dir):
        path = os.path.join(stats_dir, fn)
        if os.path.isfile(path):
            os.remove(path)

    # years.txt
    with open(os.path.join(stats_dir, 'years.txt'), 'w', encoding='utf-8') as f:
        f.write(f"✅ Успішно оброблено! Загальний час прослуховування: {format_hms(total_seconds)}\n\n")
        for year in sorted(sec_per_year['year']):
            total_y = sec_per_year.loc[sec_per_year['year'] == year, 'seconds_played'].iloc[0]
            f.write(f"{int(year)}: {format_hms(total_y)}\n")
            # Топ-5 треків
            for _, r in top5_per_year[top5_per_year['year'] == year].iterrows():
                f.write(f" {r['master_metadata_track_name']}: {format_hms(r['seconds_played'])} "
                        f"({r['plays']} plays) {format_years(r['years_list'])}\n")
            f.write("\n")
            # Топ-5 авторів
            for _, a in top5_authors_per_year[top5_authors_per_year['year'] == year].iterrows():
                f.write(f" {a['master_metadata_album_artist_name']}: {format_hms(a['seconds_played'])} "
                        f"({a['plays']} plays) {format_years(a['years_list'])}\n")
            f.write("\n")
        # Топ-10 треків загалом
        f.write("🌍 Топ-10 треків за весь час:\n")
        for _, r in top10_overall.iterrows():
            f.write(f" {r['master_metadata_track_name']}: {format_hms(r['seconds_played'])} "
                    f"({r['plays']} plays) {format_years(r['years_list'])}\n")
        f.write("\n")
        # Топ-15 авторів загалом
        f.write("🌍 Топ-15 авторів за весь час:\n")
        for _, a in author_stats.iterrows():
            author = a['master_metadata_album_artist_name']
            f.write(f" {author}: {format_hms(a['total_seconds'])} ({a['plays']} plays) "
                    f"{format_years(years_per_author.get(author, []))}\n")

    # authors.txt
    with open(os.path.join(stats_dir, 'authors.txt'), 'w', encoding='utf-8') as f:
        for _, a in author_stats.iterrows():
            author = a['master_metadata_album_artist_name']
            f.write(f"{author}: {format_hms(a['total_seconds'])} ({a['plays']} plays)\n")
            for _, t in author_top5[author_top5['master_metadata_album_artist_name'] == author].iterrows():
                f.write(f" {t['master_metadata_track_name']}: {format_hms(t['seconds_played'])} "
                        f"({t['plays']} plays) {format_years(t['years_list'])}\n")
            f.write("\n")
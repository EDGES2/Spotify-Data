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

# Перетворюємо URI у відкритий URL
def make_spotify_url(uri: str) -> str:
    if isinstance(uri, str) and uri.startswith("spotify:track:"):
        track_id = uri.split(':')[-1]
        return f"https://open.spotify.com/track/{track_id}"
    return ""

# ANSI OSC 8 hyperlink
def ansi_hyperlink(text: str, url: str) -> str:
    if not url:
        return text
    return f"\x1b]8;;{url}\x1b\\{text}\x1b]8;;\x1b\\"

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
            elif isinstance(content, list):
                data.extend(content)

    df = pd.DataFrame(data)
    if 'ts' not in df.columns:
        raise KeyError("У даних немає поля 'ts'")

    df['ts'] = pd.to_datetime(df['ts'])
    df['year'] = df['ts'].dt.year
    df['ms_played'] = df.get('ms_played', 0)
    df['seconds_played'] = df['ms_played'] / 1000.0

    total_seconds = df['seconds_played'].sum()
    sec_per_year = df.groupby('year')['seconds_played'].sum().reset_index()

    # Підрахунок років прослуховування для кожного треку та автора
    years_per_track = (
        df.groupby(['master_metadata_track_name','spotify_track_uri'])['year']
          .apply(lambda yrs: sorted(set(yrs)))
          .reset_index(name='years_list')
    )
    years_per_author = (
        df.groupby('master_metadata_album_artist_name')['year']
          .apply(lambda yrs: sorted(set(yrs)))
          .to_dict()
    )

    # Топ-5 треків по кожному року
    track_year = (
        df.groupby(['year', 'master_metadata_track_name', 'spotify_track_uri'])
          .agg(seconds_played=('seconds_played','sum'),
               plays=('master_metadata_track_name','count'))
          .reset_index()
    )
    top5_per_year = (
        track_year
        .sort_values(['year','seconds_played'], ascending=[True,False])
        .groupby('year').head(5)
        .merge(years_per_track,
               on=['master_metadata_track_name','spotify_track_uri'],
               how='left')
    )

    # Топ-10 треків загалом з роками
    track_overall = (
        df.groupby(['master_metadata_track_name','spotify_track_uri'])
          .agg(seconds_played=('seconds_played','sum'),
               plays=('master_metadata_track_name','count'))
          .reset_index()
    )
    top10_overall = (
        track_overall
        .merge(years_per_track,
               on=['master_metadata_track_name','spotify_track_uri'],
               how='left')
        .sort_values('seconds_played', ascending=False)
        .head(10)
    )

    # Статистика по авторам
    author_stats = (
        df.groupby('master_metadata_album_artist_name')
          .agg(total_seconds=('seconds_played','sum'),
               plays=('master_metadata_track_name','count'))
          .reset_index()
          .sort_values('total_seconds', ascending=False)
          .head(15)
    )

    # Топ-5 треків авторів з роками
    author_top_tracks = (
        df.groupby(['master_metadata_album_artist_name',
                    'master_metadata_track_name',
                    'spotify_track_uri'])
          .agg(seconds_played=('seconds_played','sum'),
               plays=('master_metadata_track_name','count'))
          .reset_index()
    )
    author_top5 = (
        author_top_tracks[author_top_tracks['plays'] > 5]
        .sort_values(['master_metadata_album_artist_name','seconds_played'],
                     ascending=[True,False])
        .groupby('master_metadata_album_artist_name').head(5)
        .merge(years_per_track,
               on=['master_metadata_track_name','spotify_track_uri'],
               how='left')
    )

    return (total_seconds, sec_per_year,
            top5_per_year, top10_overall,
            author_stats, author_top5,
            years_per_author)

if __name__ == "__main__":
    (total_seconds, sec_per_year,
     top5_per_year, top10_overall,
     author_stats, author_top5,
     years_per_author) = process_spotify_data('*.json')

    stats_dir = 'stats'
    os.makedirs(stats_dir, exist_ok=True)
    # Очищуємо теку (видаляємо лише файли)
    for fn in os.listdir(stats_dir):
        path = os.path.join(stats_dir, fn)
        if os.path.isfile(path):
            os.remove(path)

    # Запис years.txt
    years_path = os.path.join(stats_dir, 'years.txt')
    with open(years_path, 'w', encoding='utf-8') as f:
        # Загальний час
        header = f"✅ Успішно оброблено! Загальний час прослуховування: {format_hms(total_seconds)}\n\n"
        f.write(header)

        # Топ-5 треків за роками
        section = "🏆 Топ-5 треків за роками:\n"
        f.write(section)
        for year in sorted(sec_per_year['year']):
            total_y = sec_per_year.loc[sec_per_year['year']==year, 'seconds_played'].iloc[0]
            year_header = f"\n{int(year)}: {format_hms(total_y)}\n"
            f.write(year_header)
            for _, r in top5_per_year[top5_per_year['year']==year].iterrows():
                line = (f" {r['master_metadata_track_name']}: {format_hms(r['seconds_played'])} "
                        f"({r['plays']} plays) {format_years(r['years_list'])}\n")
                f.write(line)

        # Топ-10 треків за весь час
        section2 = "\n🌍 Топ-10 треків за весь час:\n"
        f.write(section2)
        for _, r in top10_overall.iterrows():
            line = (f" {r['master_metadata_track_name']}: {format_hms(r['seconds_played'])} "
                    f"({r['plays']} plays) {format_years(r['years_list'])}\n")
            f.write(line)

        # Топ-15 авторів за весь час з роками
        section3 = "\n🌍 Топ-15 авторів за весь час:\n"
        f.write(section3)
        for _, a in author_stats.iterrows():
            author = a['master_metadata_album_artist_name']
            years_str = format_years(years_per_author.get(author, []))
            line = (f" {author}: {format_hms(a['total_seconds'])} "
                    f"({a['plays']} plays) {years_str}\n")
            f.write(line)

    # Запис authors.txt
    authors_path = os.path.join(stats_dir, 'authors.txt')
    with open(authors_path, 'w', encoding='utf-8') as f:
        for _, a in author_stats.iterrows():
            author = a['master_metadata_album_artist_name']
            secs = a['total_seconds']
            plays = a['plays']
            f.write(f"{author}: {format_hms(secs)} ({plays} plays)\n")
            top5 = author_top5[author_top5['master_metadata_album_artist_name'] == author]
            for _, t in top5.iterrows():
                f.write(
                    f" {t['master_metadata_track_name']}: {format_hms(t['seconds_played'])} "
                    f"({t['plays']} plays) {format_years(t['years_list'])}\n"
                )
            f.write("\n")
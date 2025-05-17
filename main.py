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
            if start == prev:
                ranges.append(f"{start}")
            else:
                ranges.append(f"{start}-{prev}")
            start = prev = y
    # додати останній
    if start == prev:
        ranges.append(f"{start}")
    else:
        ranges.append(f"{start}-{prev}")
    return ", ".join(ranges)

# Перетворюємо URI у відкритий URL
def make_spotify_url(uri: str) -> str:
    if isinstance(uri, str) and uri.startswith("spotify:track:"):
        track_id = uri.split(":")[-1]
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
        print("🔍 Файли не знайдено. Вміст теки:", os.listdir('.'))
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
        print("❌ Колонки у DataFrame:", df.columns.tolist())
        raise KeyError("У даних немає поля 'ts'")

    df['ts'] = pd.to_datetime(df['ts'])
    df['year'] = df['ts'].dt.year
    df['ms_played'] = df.get('ms_played', 0)
    df['seconds_played'] = df['ms_played'] / 1000.0

    total_seconds = df['seconds_played'].sum()
    sec_per_year = df.groupby('year')['seconds_played'].sum().reset_index()

    # Топ-5 треків по кожному року
    track_year = (
        df.groupby(['year', 'master_metadata_track_name', 'spotify_track_uri'])
          .agg(seconds_played=('seconds_played','sum'), plays=('master_metadata_track_name','count'))
          .reset_index()
    )
    top5_per_year = (
        track_year.sort_values(['year','seconds_played'], ascending=[True,False])
                   .groupby('year').head(5)
    )

    # Топ-10 треків загалом з підрахунком років прослуховування
    # Спочатку базова агрегація
    track_overall = (
        df.groupby(['master_metadata_track_name','spotify_track_uri'])
          .agg(seconds_played=('seconds_played','sum'),
               plays=('master_metadata_track_name','count'),
               years_list=('year', lambda yrs: sorted(set(yrs))))
          .reset_index()
    )
    top10_overall = track_overall.sort_values('seconds_played', ascending=False).head(10)

    # Статистика по авторам
    author_stats = (
        df.groupby('master_metadata_album_artist_name')
          .agg(total_seconds=('seconds_played','sum'),
               plays=('master_metadata_track_name','count'))
          .reset_index()
    ).sort_values('total_seconds', ascending=False).head(15)

    # Топ-5 треків кожного автора (мінімум 5 прослуховувань), з роками
    author_top_tracks = (
        df.groupby(['master_metadata_album_artist_name', 'master_metadata_track_name', 'spotify_track_uri'])
          .agg(seconds_played=('seconds_played','sum'),
               plays=('master_metadata_track_name','count'),
               years_list=('year', lambda yrs: sorted(set(yrs))))
          .reset_index()
    )
    author_top5 = (
        author_top_tracks[author_top_tracks['plays'] > 5]
          .sort_values(['master_metadata_album_artist_name','seconds_played'], ascending=[True,False])
          .groupby('master_metadata_album_artist_name').head(5)
    )

    return total_seconds, sec_per_year, top5_per_year, top10_overall, author_stats, author_top5

if __name__ == "__main__":
    total_seconds, sec_per_year, top5_per_year, top10_overall, author_stats, author_top5 = \
        process_spotify_data('*.json')

    stats_dir = 'stats'
    # Створюємо або очищаємо папку stats
    if not os.path.exists(stats_dir):
        os.makedirs(stats_dir)
    else:
        for fn in os.listdir(stats_dir):
            path = os.path.join(stats_dir, fn)
            if os.path.isfile(path):
                os.remove(path)

    # ===================== Запис month.txt =====================
    month_path = os.path.join(stats_dir, 'month.txt')
    with open(month_path, 'w', encoding='utf-8') as f:
        # Загальний час
        header = f"✅ Успішно оброблено! Загальний час прослуховування: {format_hms(total_seconds)}\n\n"
        print(header, end='')
        f.write(header)

        # По роках
        section = "📆 Час прослуховування по роках:\n"
        print(section, end='')
        f.write(section)
        for _, row in sec_per_year.iterrows():
            line = f"- {int(row['year'])}: {format_hms(row['seconds_played'])}\n"
            print(line, end='')
            f.write(line)
        print(); f.write("\n")

        # Топ-5 по роках
        section = "🏆 Топ-5 треків за роками:\n"
        print(section, end='')
        f.write(section)
        for year in sorted(top5_per_year['year'].unique()):
            year_header = f"\n{int(year)}\n"
            print(year_header, end='')
            f.write(year_header)
            subset = top5_per_year[top5_per_year['year'] == year]
            for _, r in subset.iterrows():
                name = r['master_metadata_track_name']
                url = make_spotify_url(r['spotify_track_uri'])
                plays = r['plays']
                secs = r['seconds_played']
                console_title = ansi_hyperlink(name, url)
                line_console = f" {console_title}: {format_hms(secs)} ({plays} plays)\n"
                print(line_console, end='')
                line_file = f" {name}: {format_hms(secs)} ({plays} plays)\n"
                f.write(line_file)

        # Топ-10 за весь час із роками
        section = "\n🌍 Топ-10 треків за весь час:\n"
        print(section, end='')
        f.write(section)
        for _, r in top10_overall.iterrows():
            name = r['master_metadata_track_name']
            url = make_spotify_url(r['spotify_track_uri'])
            plays = r['plays']
            secs = r['seconds_played']
            years_str = format_years(r['years_list'])
            console_title = ansi_hyperlink(name, url)
            line_console = f" {console_title}: {format_hms(secs)} ({plays} plays) {years_str}\n"
            print(line_console, end='')
            line_file = f" {name}: {format_hms(secs)} ({plays} plays) {years_str}\n"
            f.write(line_file)

    # ===================== Запис authors.txt =====================
    authors_path = os.path.join(stats_dir, 'authors.txt')
    with open(authors_path, 'w', encoding='utf-8') as f:
        for _, a in author_stats.iterrows():
            author = a['master_metadata_album_artist_name']
            secs = a['total_seconds']
            plays = a['plays']
            f.write(f"{author}: {format_hms(secs)} ({plays} plays)\n")
            # f.write("Топ 5 треків по цьому автору:\n")
            top5 = author_top5[author_top5['master_metadata_album_artist_name'] == author]
            for _, t in top5.iterrows():
                track = t['master_metadata_track_name']
                secs_t = t['seconds_played']
                plays_t = t['plays']
                years_str = format_years(t['years_list'])
                f.write(f" {track}: {format_hms(secs_t)} ({plays_t} plays) {years_str}\n")
            f.write("\n")

    print(f"✅ Дані авторів (топ-15) записані до {authors_path}")

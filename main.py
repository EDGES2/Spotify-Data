import json
import glob
import os
import pandas as pd
import calendar

mefilepass = 'data/Me/Streaming_History_Audio_*.json'

# Форматування часу в HHh MMm SSs
def format_hms(total_seconds: float) -> str:
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

# Компактний рядок для списку років (напр., [2021,2022,2023] → "2021-2023")
def format_years(years: list[int]) -> str:
    if not years:
        return ""
    years = sorted(set(years))
    ranges = []
    start = prev = years[0]
    for year in years[1:]:
        if year == prev + 1:
            prev = year
        else:
            ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
            start = prev = year
    ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ", ".join(ranges)

# Основна обробка даних
def process_spotify_data(file_pattern: str):
    files = glob.glob(file_pattern)
    if not files:
        raise FileNotFoundError(f"No files matching '{file_pattern}'")

    data = []
    for path in files:
        with open(path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            data.extend(content if isinstance(content, list) else [content])

    df = pd.DataFrame(data)
    df['ts'] = pd.to_datetime(df['ts'])
    df['year'] = df['ts'].dt.year
    df['month'] = df['ts'].dt.month
    df['seconds_played'] = df.get('ms_played', 0) / 1000.0

    # Загальний час
    total_seconds = df['seconds_played'].sum()
    sec_per_year = df.groupby('year')['seconds_played'].sum().reset_index()
    sec_per_month = df.groupby(['year', 'month'])['seconds_played'].sum().reset_index()

    # Роки для треків та авторів
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

    # Топ-5 треків за місяць
    top5_per_month = (
        df.groupby(['year', 'month', 'master_metadata_track_name', 'spotify_track_uri'])
          .agg(seconds_played=('seconds_played', 'sum'), plays=('master_metadata_track_name', 'count'))
          .reset_index()
          .sort_values(['year', 'month', 'seconds_played'], ascending=[True, True, False])
          .groupby(['year', 'month']).head(5)
          .merge(years_per_track, on=['master_metadata_track_name', 'spotify_track_uri'], how='left')
    )

    # Топ-5 авторів за місяць
    top5_auth_month = (
        df.groupby(['year', 'month', 'master_metadata_album_artist_name'])
          .agg(seconds_played=('seconds_played', 'sum'), plays=('master_metadata_track_name', 'count'))
          .reset_index()
          .sort_values(['year', 'month', 'seconds_played'], ascending=[True, True, False])
          .groupby(['year', 'month']).head(5)
          .assign(years_list=lambda d: d['master_metadata_album_artist_name'].map(years_per_author))
    )

    # Топ-5 треків за рік
    track_year = (
        df.groupby(['year', 'master_metadata_track_name', 'spotify_track_uri'])
          .agg(seconds_played=('seconds_played','sum'), plays=('master_metadata_track_name','count'))
          .reset_index()
    )
    top5_per_year = (
        track_year.sort_values(['year', 'seconds_played'], ascending=[True, False])
                  .groupby('year').head(5)
                  .merge(years_per_track, on=['master_metadata_track_name', 'spotify_track_uri'], how='left')
    )

    # Топ-5 авторів за рік
    author_year = (
        df.groupby(['year', 'master_metadata_album_artist_name'])
          .agg(seconds_played=('seconds_played','sum'), plays=('master_metadata_track_name','count'))
          .reset_index()
    )
    top5_auth_year = (
        author_year.sort_values(['year', 'seconds_played'], ascending=[True, False])
                   .groupby('year').head(5)
                   .assign(years_list=lambda d: d['master_metadata_album_artist_name'].map(years_per_author))
    )

    # Топ-10 треків за весь час
    track_overall = (
        df.groupby(['master_metadata_track_name', 'spotify_track_uri'])
          .agg(seconds_played=('seconds_played','sum'), plays=('master_metadata_track_name','count'))
          .reset_index()
    )
    top10_overall = (
        track_overall.sort_values('seconds_played', ascending=False)
                     .head(10)
                     .merge(years_per_track, on=['master_metadata_track_name', 'spotify_track_uri'], how='left')
    )

    # Топ-15 авторів за весь час
    author_stats = (
        df.groupby('master_metadata_album_artist_name')
          .agg(total_seconds=('seconds_played','sum'), plays=('master_metadata_track_name','count'))
          .reset_index()
          .sort_values('total_seconds', ascending=False)
          .head(15)
    )

    # Топ-5 треків авторів за весь час
    author_tracks = (
        df.groupby(['master_metadata_album_artist_name', 'master_metadata_track_name', 'spotify_track_uri'])
          .agg(seconds_played=('seconds_played','sum'), plays=('master_metadata_track_name','count'))
          .reset_index()
    )
    top5_authors_tracks = (
        author_tracks[author_tracks['plays']>5]
                    .sort_values(['master_metadata_album_artist_name','seconds_played'], ascending=[True,False])
                    .groupby('master_metadata_album_artist_name').head(5)
                    .merge(years_per_track, on=['master_metadata_track_name','spotify_track_uri'], how='left')
    )

    return {
        'total_seconds': total_seconds,
        'sec_year': sec_per_year,
        'sec_month': sec_per_month,
        'top5_month': top5_per_month,
        'top5_auth_month': top5_auth_month,
        'top5_year': top5_per_year,
        'top5_auth_year': top5_auth_year,
        'top10_all': top10_overall,
        'top15_auth_all': author_stats,
        'top5_authors_tracks': top5_authors_tracks,
        'years_per_author': years_per_author
    }

if __name__ == "__main__":
    stats = process_spotify_data(mefilepass)

    # Створюємо директорію для результатів перед записом файлів
    stats_dir = 'stats'
    os.makedirs(stats_dir, exist_ok=True)

    # Створити папку month всередині stats
    month_dir = os.path.join(stats_dir, 'month')
    os.makedirs(month_dir, exist_ok=True)

    # Для кожного року створюємо файл YYYY.txt і записуємо місячні дані
    for year in stats['sec_year']['year'].sort_values():
        year_file = os.path.join(month_dir, f"{year}.txt")
        with open(year_file, 'w', encoding='utf-8') as f:
            # Пишемо заголовок з роком
            f.write(f"{year}\n")
            monthly = stats['sec_month'][stats['sec_month']['year'] == year]
            for _, row in monthly.sort_values('month').iterrows():
                month_name = calendar.month_name[int(row['month'])]
                secs = row['seconds_played']
                f.write(f"{month_name}: {format_hms(secs)}\n")

                # Топ-5 пісень за місяць
                f.write("Топ-5 пісень:\n")
                df_t = stats['top5_month']
                mask_t = (df_t['year'] == year) & (df_t['month'] == row['month'])
                for _, tr in df_t[mask_t].iterrows():
                    f.write(f" {tr['master_metadata_track_name']}: {format_hms(tr['seconds_played'])} "
                            f"({tr['plays']} plays) {format_years(tr['years_list'])}\n")

                # Топ-5 авторів за місяць
                f.write("\nТоп-5 авторів:\n")
                df_a = stats['top5_auth_month']
                mask_a = (df_a['year'] == year) & (df_a['month'] == row['month'])
                for _, au in df_a[mask_a].iterrows():
                    f.write(f" {au['master_metadata_album_artist_name']}: {format_hms(au['seconds_played'])} "
                            f"({au['plays']} plays) {format_years(au['years_list'])}\n")

                f.write("\n")

    # Запис years.txt
    with open(os.path.join(stats_dir, 'years.txt'), 'w', encoding='utf-8') as f:
        f.write(f"✅ Успішно оброблено! Загальний час прослуховування: {format_hms(stats['total_seconds'])}\n\n")
        for year in stats['sec_year']['year'].sort_values():
            total_year = stats['sec_year'].loc[stats['sec_year']['year']==year, 'seconds_played'].iloc[0]
            f.write(f"{year}: {format_hms(total_year)}\n")
            for _, tr in stats['top5_year'][stats['top5_year']['year']==year].iterrows():
                f.write(f" {tr['master_metadata_track_name']}: {format_hms(tr['seconds_played'])} "
                        f"({tr['plays']} plays) {format_years(tr['years_list'])}\n")
            f.write("\n")
            for _, au in stats['top5_auth_year'][stats['top5_auth_year']['year']==year].iterrows():
                f.write(f" {au['master_metadata_album_artist_name']}: {format_hms(au['seconds_played'])} "
                        f"({au['plays']} plays) {format_years(au['years_list'])}\n")
            f.write("\n")

        f.write("🌍 Топ-10 треків за весь час:\n")
        for _, tr in stats['top10_all'].iterrows():
            f.write(f" {tr['master_metadata_track_name']}: {format_hms(tr['seconds_played'])} "
                    f"({tr['plays']} plays) {format_years(tr['years_list'])}\n")

        f.write("\n🌍 Топ-15 авторів за весь час:\n")
        for _, au in stats['top15_auth_all'].iterrows():
            name = au['master_metadata_album_artist_name']
            years_str = format_years(stats['years_per_author'].get(name, []))
            f.write(f" {name}: {format_hms(au['total_seconds'])} ({au['plays']} plays) {years_str}\n")

    # Запис authors.txt
    with open(os.path.join(stats_dir, 'authors.txt'), 'w', encoding='utf-8') as f:
        for _, au in stats['top15_auth_all'].iterrows():
            name = au['master_metadata_album_artist_name']
            f.write(f"{name}: {format_hms(au['total_seconds'])} ({au['plays']} plays)\n")
            for _, tr in stats['top5_authors_tracks'][stats['top5_authors_tracks']['master_metadata_album_artist_name']==name].iterrows():
                f.write(f" {tr['master_metadata_track_name']}: {format_hms(tr['seconds_played'])} "
                        f"({tr['plays']} plays) {format_years(tr['years_list'])}\n")
            f.write("\n")

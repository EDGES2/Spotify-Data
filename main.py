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
    # \x1b]8;;url\x1b\text\x1b]8;;\x1b\
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
    
    # Підготовка даних
    df['ts'] = pd.to_datetime(df['ts'])
    df['year'] = df['ts'].dt.year
    df['ms_played'] = df.get('ms_played', 0)
    df['seconds_played'] = df['ms_played'] / 1000.0
    
    total_seconds = df['seconds_played'].sum()
    sec_per_year = df.groupby('year')['seconds_played'].sum().reset_index()
    
    # Топ‑5 по роках
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
    )
    
    # Топ‑10 за весь час
    track_overall = (
        df.groupby(['master_metadata_track_name','spotify_track_uri'])
          .agg(seconds_played=('seconds_played','sum'),
               plays=('master_metadata_track_name','count'))
          .reset_index()
    )
    top10_overall = track_overall.sort_values('seconds_played', ascending=False).head(10)
    
    return total_seconds, sec_per_year, top5_per_year, top10_overall

if __name__ == "__main__":
    total_seconds, sec_per_year, top5_per_year, top10_overall = process_spotify_data('*.json')
    
    # Загальний час
    print(f"✅ Успішно оброблено! Загальний час прослуховування: {format_hms(total_seconds)}\n")
    
    # По роках
    print("📆 Час прослуховування по роках:")
    for _, row in sec_per_year.iterrows():
        print(f"- {int(row['year'])}: {format_hms(row['seconds_played'])}")
    
    # Топ‑5 треків по роках
    print("\n🏆 Топ‑5 треків за роками:")
    for year in sorted(top5_per_year['year'].unique()):
        print(f"\n{int(year)}")
        subset = top5_per_year[top5_per_year['year'] == year]
        for _, r in subset.iterrows():
            name = r['master_metadata_track_name']
            url = make_spotify_url(r['spotify_track_uri'])
            plays = r['plays']
            secs = r['seconds_played']
            # Робимо Warriors (або іншу назву) клікабельним
            title = ansi_hyperlink(name, url)
            print(f" {title}: {format_hms(secs)} ({plays} plays)")
    
    # Топ‑10 за весь час
    print("\n🌍 Топ‑10 треків за весь час:")
    for _, r in top10_overall.iterrows():
        name = r['master_metadata_track_name']
        url = make_spotify_url(r['spotify_track_uri'])
        plays = r['plays']
        secs = r['seconds_played']
        title = ansi_hyperlink(name, url)
        print(f" {title}: {format_hms(secs)} ({plays} plays)")

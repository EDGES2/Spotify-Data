import json
import glob
import os
import pandas as pd

def format_hms(total_seconds: float) -> str:
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

def make_spotify_url(uri: str) -> str:
    if isinstance(uri, str) and uri.startswith("spotify:track:"):
        track_id = uri.split(":")[-1]
        return f"https://open.spotify.com/track/{track_id}"
    return ""

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

    # Підготуємо директорію та файл
    os.makedirs('stats', exist_ok=True)
    out_path = os.path.join('stats', 'month.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        # Загальний час
        header = f"✅ Успішно оброблено! Загальний час прослуховування: {format_hms(total_seconds)}\n\n"
        print(header, end='')
        f.write(header)

        # По роках
        section = "📆 Час прослуховування по роках:\n"
        print(section, end=''); f.write(section)
        for _, row in sec_per_year.iterrows():
            line = f"- {int(row['year'])}: {format_hms(row['seconds_played'])}\n"
            print(line, end=''); f.write(line)
        print(); f.write("\n")

        # Топ‑5 по роках
        section = "🏆 Топ‑5 треків за роками:\n"
        print(section, end=''); f.write(section)
        for year in sorted(top5_per_year['year'].unique()):
            year_header = f"\n{int(year)}\n"
            print(year_header, end=''); f.write(year_header)
            subset = top5_per_year[top5_per_year['year'] == year]
            for _, r in subset.iterrows():
                name = r['master_metadata_track_name']
                url = make_spotify_url(r['spotify_track_uri'])
                plays = r['plays']
                secs = r['seconds_played']
                # в консолі — ANSI‑лінк
                console_title = ansi_hyperlink(name, url)
                line_console = f" {console_title}: {format_hms(secs)} ({plays} plays)\n"
                print(line_console, end='')

                # у файлі — просто назва
                line_file = f" {name}: {format_hms(secs)} ({plays} plays)\n"
                f.write(line_file)

        # Топ‑10 за весь час
        section = "\n🌍 Топ‑10 треків за весь час:\n"
        print(section, end=''); f.write(section)
        for _, r in top10_overall.iterrows():
            name = r['master_metadata_track_name']
            url = make_spotify_url(r['spotify_track_uri'])
            plays = r['plays']
            secs = r['seconds_played']
            console_title = ansi_hyperlink(name, url)
            line_console = f" {console_title}: {format_hms(secs)} ({plays} plays)\n"
            print(line_console, end='')

            line_file = f" {name}: {format_hms(secs)} ({plays} plays)\n"
            f.write(line_file)

    print(f"\nВсі дані записані до {out_path}")

import json
import glob
import os
import pandas as pd

def format_hms(total_seconds: float) -> str:
    """Повертає рядок у форматі HHh MMm SSs."""
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

def process_spotify_data(file_pattern: str):
    # 1) Показати, які файли знайдено
    files = glob.glob(file_pattern)
    print("🔍 Знайдено файли:", files)
    if not files:
        print("📂 Вміст поточної теки:", os.listdir('.'))
        raise FileNotFoundError(f"Жоден файл за шаблоном '{file_pattern}' не знайдено")
    
    data = []
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            content = json.load(f)
            sample = content[0] if isinstance(content, list) else content
            print(f"🗒️ Ключі в '{file}':", list(sample.keys()))
            if isinstance(content, dict):
                data.append(content)
            elif isinstance(content, list):
                data.extend(content)
    
    df = pd.DataFrame(data)
    
    # Перевірка наявності ts
    if 'ts' not in df.columns:
        print("❌ Усі колонки у DataFrame:", df.columns.tolist())
        raise KeyError("У даних немає поля 'ts'")
    
    # Основна обробка
    df['ts'] = pd.to_datetime(df['ts'])
    df['year'] = df['ts'].dt.year
    
    # Додаємо seconds_played (ms_played може бути відсутнім)
    df['ms_played'] = df.get('ms_played', 0)
    df['seconds_played'] = df['ms_played'] / 1000.0
    
    # Загальний час прослуховування
    total_seconds = df['seconds_played'].sum()
    
    # Час прослуховування по роках
    sec_per_year = df.groupby('year')['seconds_played'].sum().reset_index()
    
    # Топ 5 треків за секундами по року
    top5_per_year = (
        df.groupby(['year', 'master_metadata_track_name'])['seconds_played']
          .sum().reset_index()
          .sort_values(['year', 'seconds_played'], ascending=[True, False])
          .groupby('year').head(5)
    )
    
    # Топ 10 треків за весь час
    top10_overall = (
        df.groupby('master_metadata_track_name')['seconds_played']
          .sum().reset_index()
          .sort_values('seconds_played', ascending=False)
          .head(10)
    )
    
    return total_seconds, sec_per_year, top5_per_year, top10_overall

if __name__ == "__main__":
    # Використовуємо шаблон *.json
    total_seconds, sec_per_year, top5_per_year, top10_overall = process_spotify_data('*.json')
    
    # Вивід загального часу
    print(f"\n✅ Успішно оброблено! Загальний час прослуховування: {format_hms(total_seconds)}\n")
    
    # Вивід по роках
    print("Час прослуховування по роках:")
    for _, row in sec_per_year.iterrows():
        print(f"{int(row['year'])}: {format_hms(row['seconds_played'])}")
    
    # Топ‑5 треків за рік
    print("\nТоп‑5 треків за часом прослуховування у кожному році:")
    for year in sorted(sec_per_year['year']):
        print(f"\n{int(year)}:")
        subset = top5_per_year[top5_per_year['year'] == year]
        for _, r in subset.iterrows():
            name = r['master_metadata_track_name']
            secs = r['seconds_played']
            print(f"  {name}: {format_hms(secs)}")
    
    # Топ‑10 треків за весь час
    print("\nТоп‑10 треків за весь час:")
    for _, r in top10_overall.iterrows():
        name = r['master_metadata_track_name']
        secs = r['seconds_played']
        print(f"  {name}: {format_hms(secs)}")

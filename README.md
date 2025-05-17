# 🎧 Spotify Listening History Analyzer

This Python script analyzes and summarizes your Spotify listening history from exported JSON files. It generates monthly and yearly statistics of your most played tracks and artists, including top lists and total listening time.

---

## 📦 Required Packages

Ensure you have the following Python package installed:

```bash
pip install pandas
```

The script uses built-in modules and `pandas`:

* `json` — for reading JSON data
* `glob` — for file pattern matching
* `os` — for directory and file operations
* `pandas` — for data manipulation and grouping
* `calendar` — for converting month numbers to month names

---

## 📂 Input Files

Place your Spotify streaming history JSON files in a directory, for example:

```bash
data/Me/Streaming_History_Audio_*.json
```

Each file must be a valid JSON exported by Spotify, typically containing a list of listening sessions.

---

## 🚀 Usage

Run the script with:

```bash
python your_script_name.py
```

The script processes all matching files and creates the following output structure:

```text
stats/
├── month/
│   ├── 2021.txt
│   ├── 2022.txt
│   └── ...
├── years.txt
└── authors.txt
```

* **stats/month/YYYY.txt** — monthly listening stats for each year:

  * Total listening time
  * Top 5 tracks for each month
  * Top 5 artists for each month

* **stats/years.txt** — yearly summaries, yearly top tracks and artists, plus overall top tracks and artists.

* **stats/authors.txt** — top 15 artists of all time and their top 5 tracks (with more than 5 plays).

---

## 🧠 Features

* **Total Listening Time:** Calculates total time listened across all files.
* **Yearly and Monthly Summaries:** Organizes your listening time by year and month.
* **Top Tracks and Artists:**

  * Monthly top 5 tracks and artists
  * Yearly top 5 tracks and artists
  * All-time top 10 tracks and top 15 artists
* **Track and Artist Lifespan:** Shows years when a track or artist appeared in your history.
* **Formatted Output:** Displays durations in `HHh MMm SSs` format and year ranges like `2019–2021`.

---

## 📌 Notes

* Ensure your streaming history JSON files are encoded in UTF-8.
* The script skips files automatically if none match the given path.
* Monthly stats labels are written in Ukrainian (e.g., "Топ-5 пісень").

---

## 🧩 Customization

You can change the `mefilepass` variable to point to a different folder or filename pattern:

```python
mefilepass = 'data/Me/Streaming_History_Audio_*.json'
```

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

## ⬇️ Downloading Your Data

Before running the script, you need to download your extended streaming history from Spotify:

1. Open your browser and navigate to Spotify’s Privacy page:

   ```
   https://www.spotify.com/account/privacy/
   ```
2. Under **Download your data**, select **Account data**
<img width="750" alt="Screenshot 2025-05-17 at 17 29 49" src="https://github.com/user-attachments/assets/9452eb10-09ff-4a3a-aec3-c63adee10cb4" />

3. Click **Request data** and wait for the email link (valid for 14 days).

4. Confirm request to download data
<img width="481" alt="Screenshot 2025-05-17 at 17 32 07" src="https://github.com/user-attachments/assets/ce745581-abf0-44fa-b434-95d4baa03292" />

5. After confirming, you’ll be redirected back to the Spotify website, where you’ll see a confirmation of your request
<img width="807" alt="Screenshot 2025-05-17 at 17 32 22" src="https://github.com/user-attachments/assets/b378648d-6456-4ab6-a93e-213720663075" />

6. You will receive this message by email (preparation of your data may take 1–2 days)
<img width="469" alt="Screenshot 2025-05-17 at 17 32 37" src="https://github.com/user-attachments/assets/9971b808-2275-4da6-a00f-cc7ba9211f83" />

7. In the email, click **Download your data** to get a ZIP archive
<img width="464" alt="Screenshot 2025-05-17 at 17 32 55" src="https://github.com/user-attachments/assets/9a1e0719-76e7-4250-b777-eb7f946fa62b" />

8. Extract the archive and locate files named `Streaming_History_Audio_*.json`.

## 📂 Input Files

Place your Spotify streaming history JSON files in a directory, for example:

```bash
Spotify-Data/data/Me/
```

Each file must be a valid JSON exported by Spotify, typically containing a list of listening sessions.

---

Your project will look like:
```bash
Spotify-Data
├── README.md
├── data
│   └── Me
│       ├── ReadMeFirst_ExtendedStreamingHistory.pdf
│       ├── Streaming_History_Audio_2021-2024_0.json
│       ├── Streaming_History_Audio_2024-2025_1.json
│       ├── Streaming_History_Audio_2025_2.json
│       └── Streaming_History_Video_2024.json
├── main.py
└── stats
    ├── authors.txt
    ├── month
    │   ├── 2021.txt
    │   ├── 2022.txt
    │   ├── 2023.txt
    │   ├── 2024.txt
    │   └── 2025.txt
    └── years.txt
```

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

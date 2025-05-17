🎧 Spotify Listening History Analyzer
This Python script analyzes and summarizes your Spotify listening history from exported JSON files. It generates monthly and yearly statistics about your most played tracks and artists, including top lists and total listening time.

📦 Required Packages
Make sure the following Python packages are installed:

bash
Copy
Edit
pip install pandas
The script uses only built-in and pandas packages:

json — for reading JSON data

glob — for file pattern matching

os — for directory and file operations

pandas — for data manipulation and grouping

calendar — for converting month numbers to month names

📂 Input
Place your Spotify streaming history files in a directory such as:

kotlin
Copy
Edit
data/Me/Streaming_History_Audio_*.json
Each file must be a valid JSON file exported by Spotify, typically containing a list of listening sessions.

🚀 Usage
Run the script with:

bash
Copy
Edit
python your_script_name.py
The script processes all matching history files and creates the following output structure:

yaml
Copy
Edit
stats/
├── month/
│   ├── 2021.txt
│   ├── 2022.txt
│   └── ...
├── years.txt
└── authors.txt
Output Files
stats/month/YYYY.txt — per-month listening stats for each year, including:

Total listening time

Top 5 tracks for each month

Top 5 artists for each month

stats/years.txt — yearly totals and top tracks/artists by year, plus overall top tracks and artists.

stats/authors.txt — top 15 artists of all time and their top 5 tracks (with more than 5 plays).

🧠 Features
Total Listening Time: Calculates total time listened across all files.

Per-Year and Per-Month Summaries: Organizes your listening time by year and month.

Top Tracks and Artists:

Monthly top 5 tracks and artists

Yearly top 5 tracks and artists

All-time top 10 tracks and top 15 artists

Track and Artist Lifespan: Shows years when a track or artist appeared in your history.

Formatted Output: Time durations are shown in HHh MMm SSs format, and year ranges like 2019-2021.

📌 Notes
Ensure your streaming history JSON files are properly encoded in UTF-8.

The script automatically skips files if no matches are found for the given path.

Monthly stats are written in Ukrainian (e.g., labels like "Топ-5 пісень").

🧩 Customization
You can change the mefilepass variable to point to a different folder or filename pattern:

python
Copy
Edit
mefilepass = 'data/Me/Streaming_History_Audio_*.json'

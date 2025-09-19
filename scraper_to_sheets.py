# scraper_to_sheets.py
"""
Scraper for HELB mentions in Kenyan news starting from Jan 1 of the current year.
Appends only NEW mentions to Google Sheet (deduplicated by link/title+date).
"""

from gnews import GNews
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import sys
import time
from datetime import datetime

nltk.download("vader_lexicon", quiet=True)

# ---------------- CONFIG ----------------
SHEET_NAME = "HELB_Mentions"     # Google Sheet name
SPREADSHEET_ID = None            # if you prefer ID, put it here

HEADERS = ["title", "published", "source", "summary", "link", "tonality"]

QUERY = "HELB Kenya"

# ---- Dynamic start date: Jan 1 this year → today
START_DATE = (datetime.now().year, 1, 1)
END_DATE = datetime.now().timetuple()[:3]  # (YYYY, M, D)

# ---------------- AUTH ----------------
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

if not os.path.exists("service_account.json"):
    print("❌ service_account.json missing.")
    sys.exit(1)

creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", SCOPES)
gc = gspread.authorize(creds)

try:
    if SPREADSHEET_ID:
        sh = gc.open_by_key(SPREADSHEET_ID)
    else:
        sh = gc.open(SHEET_NAME)
    worksheet = sh.get_worksheet(0)
except Exception as e:
    print(f"❌ Failed to open sheet: {e}")
    sys.exit(1)

# ---------------- Existing Records ----------------
existing_records = worksheet.get_all_records()
existing_links = {str(r.get("link", "")).strip() for r in existing_records if r.get("link")}
existing_sigs = {(str(r.get("title", "")).strip(), str(r.get("published", "")).strip()) for r in existing_records}

print(f"✅ Existing rows: {len(existing_records)}")

# ---------------- Scrape News ----------------
sia = SentimentIntensityAnalyzer()
g = GNews(language="en", country="KE", start_date=START_DATE, end_date=END_DATE)

articles = g.get_news(QUERY) or []
print(f"📰 Articles fetched: {len(articles)}")

def extract_field(article, keys):
    for k in keys:
        if article.get(k):
            return article.get(k)
    return ""

new_rows = []
for a in articles:
    title = str(extract_field(a, ["title"])).strip()
    summary = str(extract_field(a, ["description", "summary", "snippet"])).strip()
    link = str(extract_field(a, ["url", "link"])).strip()
    published_raw = str(extract_field(a, ["published date", "published", "publishedAt"])).strip()
    source = ""
    pub = a.get("publisher")
    if isinstance(pub, dict):
        source = pub.get("title", "")
    if not source:
        source = str(extract_field(a, ["source", "site", "domain"])).strip()

    published_parsed = pd.to_datetime(published_raw, errors="coerce")
    published = published_parsed.isoformat() if not pd.isna(published_parsed) else published_raw

    text_for_sent = summary if summary else title
    score = sia.polarity_scores(text_for_sent)["compound"]
    tonality = "Positive" if score >= 0.05 else "Negative" if score <= -0.05 else "Neutral"

    sig = (title, published)
    if (link and link in existing_links) or (sig in existing_sigs):
        continue

    row = [title, published, source, summary, link, tonality]
    new_rows.append(row)

# ---------------- Append to Sheet ----------------
if not new_rows:
    print("ℹ️ No new mentions to append.")
else:
    if len(worksheet.get_all_values()) == 0:
        worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")
        time.sleep(1)

    try:
        worksheet.append_rows(new_rows, value_input_option="USER_ENTERED")
        print(f"✅ Appended {len(new_rows)} new mentions.")
    except Exception as e:
        print(f"⚠️ Batch append failed: {e}. Trying row-by-row...")
        for r in new_rows:
            worksheet.append_row(r, value_input_option="USER_ENTERED")
        print(f"✅ Appended {len(new_rows)} mentions (row-by-row).")

print("🎉 Done.")

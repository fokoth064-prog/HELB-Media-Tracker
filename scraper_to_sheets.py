# scraper_to_sheets.py
"""
Scraper for HELB mentions in Kenyan news starting from Jan 1, 2025.
Appends only NEW mentions to Google Sheet (deduplicated by link/title+date).
Cleans historical rows so all published dates are normalized.
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

nltk.download("vader_lexicon", quiet=True)

# ---------------- CONFIG ----------------
SHEET_NAME = "HELB_Mentions"     # Google Sheet name
SPREADSHEET_ID = None            # if you prefer ID, put it here

HEADERS = ["title", "published", "source", "summary", "link", "tonality"]

QUERY = "HELB Kenya"
START_DATE = (2025, 1, 1)  # YYYY, MM, DD → fetch from Jan 1, 2025 onwards

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

# ---------------- LOAD EXISTING ----------------
existing_records = worksheet.get_all_records()
df = pd.DataFrame(existing_records)

print(f"✅ Existing rows before cleaning: {len(df)}")

# ---------------- CLEAN PUBLISHED DATES ----------------
def clean_date(val):
    if not val or pd.isna(val):
        return ""
    try:
        dt = pd.to_datetime(val, errors="coerce", utc=True)
        if pd.isna(dt):
            return ""
        return dt.tz_convert("Africa/Nairobi").strftime("%Y-%m-%d")
    except Exception:
        try:
            dt = pd.to_datetime(val, errors="coerce")
            if pd.isna(dt):
                return ""
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return ""

if not df.empty and "published" in df.columns:
    df["published"] = df["published"].apply(clean_date)

    # Push cleaned data back to Google Sheet
    values = [df.columns.tolist()] + df.values.tolist()
    worksheet.clear()
    worksheet.update(values)
    print("🧹 Cleaned historical 'published' dates in sheet")

# ---------------- Refresh Records After Cleaning ----------------
existing_records = worksheet.get_all_records()
existing_links = {str(r.get("link", "")).strip() for r in existing_records if r.get("link")}
existing_sigs = {(str(r.get("title", "")).strip(), str(r.get("published", "")).strip()) for r in existing_records}

print(f"✅ Existing rows after cleaning: {len(existing_records)}")

# ---------------- Scrape New Articles ----------------
sia = SentimentIntensityAnalyzer()
g = GNews(language="en", country="KE", start_date=START_DATE)

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

    # Normalize new published dates
    published_parsed = pd.to_datetime(published_raw, errors="coerce", utc=True)
    if pd.isna(published_parsed):
        published = ""
    else:
        try:
            published = published_parsed.tz_convert("Africa/Nairobi").strftime("%Y-%m-%d")
        except Exception:
            published = published_parsed.strftime("%Y-%m-%d")

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

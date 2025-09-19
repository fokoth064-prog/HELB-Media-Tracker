from gnews import GNews
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe

# Download the sentiment lexicon
nltk.download('vader_lexicon', quiet=True)

# ---- Authenticate with Google Service Account ----
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
gc = gspread.authorize(creds)

# ---- Open Google Sheet ----
SHEET_NAME = "HELB_Mentions"
try:
    sh = gc.open(SHEET_NAME)
    worksheet = sh.sheet1
except gspread.SpreadsheetNotFound:
    sh = gc.create(SHEET_NAME)
    worksheet = sh.get_worksheet(0)

# ---- Scraper + sentiment ----
sia = SentimentIntensityAnalyzer()
g = GNews(language='en', country='KE', period='3000d')
articles = g.get_news("HELB Kenya")

rows = []
for a in articles:
    title = a.get('title')
    summary = a.get('description') or ""
    link = a.get('url')
    published = a.get('published date')
    source = a.get('publisher', {}).get('title', 'Unknown')

    score = sia.polarity_scores(summary)["compound"]
    if score >= 0.05:
        tonality = "Positive"
    elif score <= -0.05:
        tonality = "Negative"
    else:
        tonality = "Neutral"

    rows.append({
        "title": title,
        "published": published,
        "source": source,
        "summary": summary,
        "link": link,
        "tonality": tonality
    })

df = pd.DataFrame(rows)

# ---- Upload to Google Sheets ----
worksheet.clear()
set_with_dataframe(worksheet, df)

print(f"✅ Uploaded {len(df)} articles to Google Sheets")

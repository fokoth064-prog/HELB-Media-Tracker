# pages/3_Keyword_Trends.py
import streamlit as st
import pandas as pd
from collections import Counter
import re

st.title("🔑 Keyword Trends")

# -------------------------------
# Load dataset from Google Sheets
# -------------------------------
CSV_URL = "https://docs.google.com/spreadsheets/d/10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ/export?format=csv"

try:
    df = pd.read_csv(CSV_URL)
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()

# -------------------------------
# Rename columns to standard names
# -------------------------------
col_map = {
    "published": "date",
    "tonality": "sentiment",
    "title": "title",
    "source": "source"
}
df = df.rename(columns=col_map)

# Keep only the needed columns
df = df[["date", "source", "title", "sentiment"]]

# Convert date column to datetime
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# -------------------------------
# Filters
# -------------------------------
st.sidebar.header("Filters")

# Date filter
min_date, max_date = df["date"].min(), df["date"].max()
date_range = st.sidebar.date_input("Date Range", [min_date, max_date])
if len(date_range) == 2:
    df = df[(df["date"] >= pd.to_datetime(date_range[0])) & (df["date"] <= pd.to_datetime(date_range[1]))]

# Sentiment filter
sentiment_options = ["All"] + sorted(df["sentiment"].dropna().unique())
sentiment_filter = st.sidebar.selectbox("Sentiment", sentiment_options)
if sentiment_filter != "All":
    df = df[df["sentiment"] == sentiment_filter]

# Source filter
source_options = ["All"] + sorted(df["source"].dropna().unique())
source_filter = st.sidebar.selectbox("Source", source_options)
if source_filter != "All":
    df = df[df["source"] == source_filter]

# -------------------------------
# Keyword Extraction
# -------------------------------
all_text = " ".join(df["title"].dropna().astype(str).tolist()).lower()
tokens = re.findall(r"\b\w+\b", all_text)

# Keyword frequency
word_counts = Counter(tokens)
df_keywords = pd.DataFrame(word_counts.items(), columns=["keyword", "count"]).sort_values(
    by="count", ascending=False
)

st.subheader("Top Keywords")
top_n = st.slider("Select number of top keywords", 5, 20, 10)
st.dataframe(df_keywords.head(top_n), use_container_width=True)

# -------------------------------
# N-grams (bigrams & trigrams)
# -------------------------------
def get_ngrams(tokens, n):
    return zip(*[tokens[i:] for i in range(n)])

bigrams = Counter(get_ngrams(tokens, 2))
trigrams = Counter(get_ngrams(tokens, 3))

df_bigrams = pd.DataFrame(
    [(" ".join(k), v) for k, v in bigrams.items()],
    columns=["bigram", "count"]
).sort_values(by="count", ascending=False)

df_trigrams = pd.DataFrame(
    [(" ".join(k), v) for k, v in trigrams.items()],
    columns=["trigram", "count"]
).sort_values(by="count", ascending=False)

st.subheader("Top Bigrams")
st.dataframe(df_bigrams.head(10), use_container_width=True)

st.subheader("Top Trigrams")
st.dataframe(df_trigrams.head(10), use_container_width=True)

# -------------------------------
# Export option
# -------------------------------
st.subheader("Export Data")
csv = df_keywords.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download keyword frequencies as CSV",
    csv,
    "keyword_frequencies.csv",
    "text/csv",
    key="download-csv",
)

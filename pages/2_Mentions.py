# pages/2_Mentions.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from wordcloud import WordCloud, STOPWORDS
from sklearn.feature_extraction.text import CountVectorizer
import nltk

# Make sure NLTK stopwords are available
nltk.download("stopwords", quiet=True)
from nltk.corpus import stopwords as nltk_stopwords


# ---------- CONFIG ----------
CSV_URL = "https://docs.google.com/spreadsheets/d/10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ/export?format=csv"


# ---------- LOAD DATA ----------
@st.cache_data
def load_data(csv_url):
    try:
        df = pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"❌ Failed to load CSV: {e}")
        return pd.DataFrame()

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Parse and localize dates
    if "published" in df.columns:
        df["published_parsed"] = pd.to_datetime(df["published"], errors="coerce", utc=True)
        try:
            df["published_parsed"] = df["published_parsed"].dt.tz_convert("Africa/Nairobi")
        except Exception:
            pass
        df["DATE"] = df["published_parsed"].dt.strftime("%d-%b-%Y")
        df["TIME"] = df["published_parsed"].dt.strftime("%H:%M")
    else:
        df["published_parsed"] = pd.NaT
        df["DATE"] = ""
        df["TIME"] = ""

    # Ensure text columns exist
    for col in ["title", "summary", "source", "tonality", "link"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")

    # Rename to uppercase for display consistency
    rename_map = {
        "title": "TITLE",
        "summary": "SUMMARY",
        "source": "SOURCE",
        "tonality": "TONALITY",
        "link": "LINK",
    }
    df = df.rename(columns=rename_map)

    return df


# ---------- UTILITIES ----------
def make_html_table(df, cols, max_rows=200):
    """HTML table with conditional row colors."""
    COLORS = {
        "Positive": "#b6e0b6",  # darker green
        "Neutral": "#f3f3f3",   # grey
        "Negative": "#ffb3b3",  # darker red
    }

    html = """
    <div style="overflow:auto; max-height:650px;">
    <table style="border-collapse:collapse; width:100%; font-family:Arial, sans-serif; color:#000;">
      <thead>
        <tr>
    """
    for c in cols:
        html += f'<th style="text-align:left; padding:8px; border-bottom:1px solid #ddd; background:#f8f8f8;">{c}</th>'
    html += "</tr></thead><tbody>"

    n = min(len(df), max_rows)
    for i in range(n):
        row = df.iloc[i]
        ton = str(row.get("TONALITY", "")).strip()
        bg = COLORS.get(ton, "#ffffff")
        html += f'<tr style="background:{bg};">'
        for c in cols:
            v = row.get(c, "")
            if c == "LINK" and isinstance(v, str) and v.startswith("http"):
                cell = f'<a href="{v}" target="_blank" rel="noopener noreferrer">Open Article</a>'
            else:
                cell = str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html += f'<td style="padding:8px; vertical-align:top; border-bottom:1px solid #eee;">{cell}</td>'
        html += "</tr>"
    html += "</tbody></table></div>"
    return html


def top_ngrams(texts, ngram=(1, 1), top_n=20, extra_stopwords=None):
    stop_words = set(nltk_stopwords.words("english")) | set(STOPWORDS)
    if extra_stopwords:
        stop_words |= set(extra_stopwords)
    vectorizer = CountVectorizer(ngram_range=ngram, stop_words=stop_words)
    X = vectorizer.fit_transform(texts)
    counts = np.asarray(X.sum(axis=0)).ravel()
    vocab = np.array(vectorizer.get_feature_names_out())
    top_idx = counts.argsort()[::-1][:top_n]
    return list(zip(vocab[top_idx], counts[top_idx]))


def make_wordcloud_image(text_blob, width=800, height=400):
    if not text_blob.strip():
        return None
    wc = WordCloud(
        width=width,
        height=height,
        background_color="white",
        stopwords=set(nltk_stopwords.words("english")) | set(STOPWORDS),
    )
    wc.generate(text_blob)
    fig = plt.figure(figsize=(12, 6))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    buf = BytesIO()
    fig.tight_layout(pad=0)
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# ---------- MAIN ----------
st.title("📋 Mentions")

df = load_data(CSV_URL)
if df.empty:
    st.info("No data available. Check the CSV URL and sharing settings.")
    st.stop()

# Sidebar filter
st.sidebar.header("Filters")
search = st.sidebar.text_input("Search (TITLE / SUMMARY)")

if search:
    mask = df["TITLE"].str.contains(search, case=False, na=False) | df["SUMMARY"].str.contains(search, case=False, na=False)
    filtered = df[mask].copy()
else:
    filtered = df.copy()

# Results count
st.markdown(f"**Results:** {len(filtered):,} articles (showing latest first)")

# Sort by date
if "published_parsed" in filtered.columns:
    filtered = filtered.sort_values(by="published_parsed", ascending=False).reset_index(drop=True)

# Table
cols_to_show = ["DATE", "TIME", "SOURCE", "TONALITY", "TITLE", "SUMMARY", "LINK"]
cols_to_show = [c for c in cols_to_show if c in filtered.columns]
html_table = make_html_table(filtered, cols_to_show, max_rows=500)
st.markdown(html_table, unsafe_allow_html=True)

# CSV download
csv_bytes = filtered[cols_to_show].to_csv(index=False).encode("utf-8")
st.download_button("📥 Download Filtered Mentions (CSV)", data=csv_bytes, file_name="mentions_filtered.csv", mime="text/csv")

# Keyword trends
st.markdown("---")
st.header("🔎 Keyword Trends")

texts = (filtered["TITLE"].astype(str) + " " + filtered["SUMMARY"].astype(str)).tolist()
big_text = " ".join(texts)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Unigrams")
    top_uni = top_ngrams(texts, ngram=(1, 1), top_n=20)
    if top_uni:
        st.table(pd.DataFrame(top_uni, columns=["term", "count"]))
    else:
        st.info("Not enough text for unigrams.")

    st.subheader("Top Bigrams")
    top_bi = top_ngrams(texts, ngram=(2, 2), top_n=15)
    if top_bi:
        st.table(pd.DataFrame(top_bi, columns=["bigram", "count"]))
    else:
        st.info("Not enough text for bigrams.")

with col2:
    st.subheader("Word Cloud")
    wc_buf = make_wordcloud_image(big_text)
    if wc_buf:
        st.image(wc_buf, use_column_width=True)
    else:
        st.info("No text for word cloud.")

st.subheader("Top Trigrams")
top_tri = top_ngrams(texts, ngram=(3, 3), top_n=12)
if top_tri:
    st.table(pd.DataFrame(top_tri, columns=["trigram", "count"]))
else:
    st.info("No trigrams available.")

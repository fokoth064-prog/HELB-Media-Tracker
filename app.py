# app.py
import streamlit as st
import pandas as pd

# -------------------------------
# Page configuration
# -------------------------------
st.set_page_config(
    page_title="HELB Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 HELB Media Monitoring Dashboard")
st.write("Welcome! Use the sidebar to navigate to different pages.")

# -------------------------------
# Load dataset once
# -------------------------------
CSV_URL = "https://docs.google.com/spreadsheets/d/10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ/export?format=csv"

@st.cache_data(ttl=3600)  # cache for 1 hour
def load_data():
    df = pd.read_csv(CSV_URL)

    # Rename columns
    col_map = {
        "published": "date",
        "tonality": "sentiment",
        "title": "title",
        "source": "source"
    }
    df = df.rename(columns=col_map)

    # Keep only relevant columns
    df = df[["date", "source", "title", "sentiment"]]

    # Convert date column
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ✅ Keep only last 5 years
    cutoff_date = pd.Timestamp.today() - pd.DateOffset(years=5)
    df = df[df["date"] >= cutoff_date]

    return df

if "mentions_df" not in st.session_state:
    st.session_state["mentions_df"] = load_data()

df = st.session_state["mentions_df"]

# -------------------------------
# Quick Summary Stats
# -------------------------------
st.subheader("📌 Quick Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Mentions (5 yrs)", len(df))

with col2:
    date_range = f"{df['date'].min().date()} → {df['date'].max().date()}"
    st.metric("Date Range", date_range)

with col3:
    sentiment_counts = df["sentiment"].value_counts(normalize=True) * 100
    sentiment_str = " | ".join([f"{s}: {p:.1f}%" for s, p in sentiment_counts.items()])
    st.metric("Sentiment Split", sentiment_str)

# -------------------------------
# Extra info for user
# -------------------------------
st.info("✅ Data is automatically limited to the last 5 years and cached for faster loading.")

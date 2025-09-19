import streamlit as st
import pandas as pd

CSV_URL = "https://docs.google.com/spreadsheets/d/10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ/export?format=csv"

if "mentions_df" not in st.session_state:
    df = pd.read_csv(CSV_URL)

    # Rename columns
    col_map = {
        "published": "date",
        "tonality": "sentiment",
        "title": "title",
        "source": "source"
    }
    df = df.rename(columns=col_map)
    df = df[["date", "source", "title", "sentiment"]]

    # Convert date column
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ✅ Apply 5-year cutoff
    cutoff_date = pd.Timestamp.today() - pd.DateOffset(years=5)
    df = df[df["date"] >= cutoff_date]

    # Save in session_state
    st.session_state["mentions_df"] = df

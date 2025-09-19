# mentions.py
import streamlit as st
import pandas as pd

# ---------- CONFIG ----------
CSV_URL = "https://docs.google.com/spreadsheets/d/10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ/export?format=csv"

# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    df['published_parsed'] = pd.to_datetime(df['published'], errors='coerce')
    return df

df = load_data()

st.title("💬 Mentions")

# ---------- FILTERS ----------
st.sidebar.header("Filters")
sources = sorted(df['source'].dropna().unique())
source_filter = st.sidebar.multiselect("Source", options=sources, default=sources)

tonalities = df['tonality'].dropna().unique()
tonality_filter = st.sidebar.multiselect("Tonality", options=tonalities, default=tonalities)

filtered = df[
    df['source'].isin(source_filter) &
    df['tonality'].isin(tonality_filter)
]

# ---------- DISPLAY ----------
if not filtered.empty:
    st.write("### Mentions")
    st.dataframe(
        filtered[['published', 'source', 'title', 'summary', 'tonality']],
        use_container_width=True,  # ✅ auto-fit to screen
        hide_index=True
    )
else:
    st.warning("No mentions available for selected filters.")


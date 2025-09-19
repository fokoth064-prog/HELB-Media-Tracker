# pages/1_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- CONFIG ----------------
CSV_URL = "https://docs.google.com/spreadsheets/d/10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ/export?format=csv"

# HELB Brand Colors
HELB_GREEN = "#008000"   # main
HELB_GOLD = "#FFD700"
HELB_BLUE = "#1E90FF"
HELB_RED = "#B22222"

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data(csv_url):
    df = pd.read_csv(csv_url)
    df['published_parsed'] = pd.to_datetime(df['published'], errors='coerce')
    df['YEAR'] = df['published_parsed'].dt.year
    df['MONTH'] = df['published_parsed'].dt.month
    return df

df = load_data(CSV_URL)

st.markdown(
    f"""
    <style>
        .tile {{
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .tile h3 {{
            margin: 0;
            font-size: 20px;
            color: {HELB_GREEN};
        }}
        .tile p {{
            font-size: 28px;
            font-weight: bold;
            margin: 5px 0 0;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 HELB Dashboard")
st.write("An overview of HELB mentions, sentiment, and trends.")

# --- KPI Tiles ---
col1, col2, col3, col4 = st.columns(4)

total_mentions = len(df)
positive = df[df['tonality'] == "Positive"]
negative = df[df['tonality'] == "Negative"]
neutral = df[df['tonality'] == "Neutral"]

with col1:
    st.markdown(f"<div class='tile'><h3>Total Mentions</h3><p style='color:{HELB_BLUE};'>{total_mentions}</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='tile'><h3>Positive</h3><p style='color:{HELB_GREEN};'>{len(positive)}</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='tile'><h3>Negative</h3><p style='color:{HELB_RED};'>{len(negative)}</p></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='tile'><h3>Neutral</h3><p style='color:{HELB_GOLD};'>{len(neutral)}</p></div>", unsafe_allow_html=True)

st.markdown("---")

# --- Charts Row ---
col5, col6 = st.columns(2)

with col5:
    st.subheader("Tonality Distribution")
    tonality_counts = df['tonality'].value_counts().reset_index()
    tonality_counts.columns = ["Tonality", "Count"]
    fig_pie = px.pie(
        tonality_counts,
        names="Tonality",
        values="Count",
        color="Tonality",
        color_discrete_map={
            "Positive": HELB_GREEN,
            "Negative": HELB_RED,
            "Neutral": HELB_GOLD
        }
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col6:
    st.subheader("Mentions Over Time")
    timeline = df.groupby(df['published_parsed'].dt.date).size().reset_index(name="Count")
    fig_line = px.line(timeline, x="published_parsed", y="Count", markers=True)
    fig_line.update_traces(line_color=HELB_BLUE)
    st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

st.subheader("📅 Filter by Year / Financial Year / Quarter")
# TODO: Add Year, FY, Quarter filters and visuals

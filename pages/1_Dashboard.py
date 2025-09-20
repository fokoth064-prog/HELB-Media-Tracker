# app_streamlit.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import altair as alt

# ----------------- CONFIG -----------------
st.set_page_config(page_title="HELB Media Monitoring Dashboard", layout="wide")

# ----------------- CUSTOM HEADER -----------------
st.markdown(
    """
    <style>
    .header-container {
        background-color: #006400; /* HELB green */
        padding: 15px;
        text-align: center;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        z-index: 100;
    }
    .header-container h1 {
        color: white;
        font-size: 28px;
        margin: 0;
        font-weight: bold;
    }
    .reportview-container {
        margin-top: 90px;
    }
    </style>
    <div class="header-container">
        <h1>HELB MEDIA MONITORING DASHBOARD</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------- LOAD DATA -----------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/your_sheet_id_here/export?format=csv"
df = pd.read_csv(SHEET_URL)

# Clean & process
df["published"] = pd.to_datetime(df["published"], errors="coerce")
df = df.dropna(subset=["published"])

# ----------------- SIDEBAR FILTERS -----------------
st.sidebar.header("Filters")
start_date = st.sidebar.date_input("Start Date", df["published"].min().date())
end_date = st.sidebar.date_input("End Date", df["published"].max().date())
sentiments = st.sidebar.multiselect("Sentiment", options=df["tonality"].unique(), default=list(df["tonality"].unique()))

mask = (df["published"].dt.date >= start_date) & (df["published"].dt.date <= end_date) & (df["tonality"].isin(sentiments))
filtered_df = df.loc[mask]

# ----------------- KPIs -----------------
col1, col2, col3 = st.columns(3)
col1.metric("Total Mentions", len(filtered_df))
col2.metric("Unique Sources", filtered_df["source"].nunique())
col3.metric("Sentiment Split", f"{filtered_df['tonality'].value_counts(normalize=True).mul(100).round(1).to_dict()}")

# ----------------- TREND CHART -----------------
st.subheader("📈 Mentions Over Time")
trend = filtered_df.groupby(filtered_df["published"].dt.to_period("M")).size().reset_index(name="counts")
trend["published"] = trend["published"].dt.to_timestamp()

line_chart = alt.Chart(trend).mark_line(point=True).encode(
    x="published:T",
    y="counts:Q",
    tooltip=["published:T", "counts:Q"]
).properties(width=800, height=400)

st.altair_chart(line_chart, use_container_width=True)

# ----------------- TOP SOURCES -----------------
st.subheader("🏆 Top Sources")
top_sources = filtered_df["source"].value_counts().head(10).reset_index()
top_sources.columns = ["source", "mentions"]

bar_chart = alt.Chart(top_sources).mark_bar().encode(
    x="mentions:Q",
    y=alt.Y("source:N", sort="-x"),
    tooltip=["source", "mentions"]
).properties(width=800, height=400)

st.altair_chart(bar_chart, use_container_width=True)

# ----------------- WORD CLOUD -----------------
st.subheader("☁ Word Cloud of Mentions")
text = " ".join(filtered_df["summary"].dropna().astype(str).tolist())
if text.strip():
    wc = WordCloud(width=800, height=400, background_color="white", colormap="Greens").generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)
else:
    st.info("No text available to generate Word Cloud.")

# ----------------- FOOTER -----------------
st.markdown(
    """
    <hr>
    <div style='text-align: center; color: gray;'>
        Developed by Fred Okoth
    </div>
    """,
    unsafe_allow_html=True
)

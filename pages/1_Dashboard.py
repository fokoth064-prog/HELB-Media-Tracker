import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials

# ---------------- GOOGLE SHEETS LOADER ----------------
@st.cache_data(ttl=600)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]

    # Load credentials from Streamlit secrets
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(creds)

    # Open sheet by ID (replace with your sheet ID)
    SHEET_ID = "10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ"
    sh = client.open_by_key(SHEET_ID)
    worksheet = sh.sheet1

    records = worksheet.get_all_records()
    df = pd.DataFrame(records)

    # Ensure datetime
    if "published" in df.columns:
        df["published_parsed"] = pd.to_datetime(df["published"], errors="coerce")

    return df

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="HELB Dashboard", layout="wide")
st.title("📊 HELB Kenya News Sentiment Monitor")

# ---------------- LOAD DATA ----------------
df = load_data()

if df.empty:
    st.warning("No data found in Google Sheet.")
    st.stop()

# ---------------- FILTERS ----------------
st.sidebar.header("Filters")

# Year filter
df["Year"] = df["published_parsed"].dt.year
years = df["Year"].dropna().unique().tolist()
selected_years = st.sidebar.multiselect("Select Year(s)", years, default=years)

# Financial Year filter
def get_financial_year(date):
    if pd.isna(date):
        return None
    year = date.year
    return f"{year}/{year+1}" if date.month >= 7 else f"{year-1}/{year}"

df["FinancialYear"] = df["published_parsed"].apply(get_financial_year)
financial_years = df["FinancialYear"].dropna().unique().tolist()
selected_fy = st.sidebar.multiselect("Select Financial Year(s)", financial_years, default=financial_years)

# Quarter filter
def get_quarter(date):
    if pd.isna(date):
        return None
    if date.month in [7, 8, 9]:
        return "Q1"
    elif date.month in [10, 11, 12]:
        return "Q2"
    elif date.month in [1, 2, 3]:
        return "Q3"
    elif date.month in [4, 5, 6]:
        return "Q4"

df["Quarter"] = df["published_parsed"].apply(get_quarter)
quarters = df["Quarter"].dropna().unique().tolist()
selected_quarters = st.sidebar.multiselect("Select Quarter(s)", quarters, default=quarters)

# Month filter
df["Month"] = df["published_parsed"].dt.strftime("%B")
months = df["Month"].dropna().unique().tolist()
selected_months = st.sidebar.multiselect("Select Month(s)", months, default=months)

# Date range filter
min_date, max_date = df["published_parsed"].min(), df["published_parsed"].max()
start_date = st.sidebar.date_input("Start Date", min_date.date() if pd.notna(min_date) else None)
end_date = st.sidebar.date_input("End Date", max_date.date() if pd.notna(max_date) else None)

# Apply filters
filtered_df = df.copy()
if selected_years:
    filtered_df = filtered_df[filtered_df["Year"].isin(selected_years)]
if selected_fy:
    filtered_df = filtered_df[filtered_df["FinancialYear"].isin(selected_fy)]
if selected_quarters:
    filtered_df = filtered_df[filtered_df["Quarter"].isin(selected_quarters)]
if selected_months:
    filtered_df = filtered_df[filtered_df["Month"].isin(selected_months)]
if start_date and end_date:
    filtered_df = filtered_df[
        (filtered_df["published_parsed"] >= pd.to_datetime(start_date)) &
        (filtered_df["published_parsed"] <= pd.to_datetime(end_date))
    ]

# ---------------- KPI TILES ----------------
st.subheader("Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Mentions", len(filtered_df))

with col2:
    st.metric("Positive Mentions", (filtered_df["tonality"] == "Positive").sum())

with col3:
    st.metric("Negative Mentions", (filtered_df["tonality"] == "Negative").sum())

with col4:
    st.metric("Neutral Mentions", (filtered_df["tonality"] == "Neutral").sum())

# ---------------- CHARTS ----------------
st.subheader("Visual Analysis")

col_left, col_right = st.columns(2)

# Doughnut chart for tonality
with col_left:
    tonality_counts = filtered_df["tonality"].value_counts()
    fig_donut = go.Figure(data=[go.Pie(
        labels=tonality_counts.index,
        values=tonality_counts.values,
        hole=0.5,
        marker=dict(colors=["green", "red", "grey"]),
        textfont=dict(color="white")
    )])
    fig_donut.update_layout(
        title="Tonality Distribution",
        height=300,
        margin=dict(t=30, b=30, l=10, r=10)
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# Mentions over time
with col_right:
    mentions_ts = filtered_df.groupby(filtered_df["published_parsed"].dt.date).size().reset_index(name="count")
    fig_line = px.line(mentions_ts, x="published_parsed", y="count", title="Mentions Over Time")
    fig_line.update_layout(height=300, margin=dict(t=30, b=30, l=10, r=10))
    st.plotly_chart(fig_line, use_container_width=True)

# Row 2 charts
col3, col4 = st.columns(2)

# Top Sources
with col3:
    top_sources = filtered_df["source"].value_counts().head(5)
    fig_bar = px.bar(top_sources, x=top_sources.index, y=top_sources.values,
                     title="Top 5 News Sources", labels={"x": "Source", "y": "Mentions"})
    fig_bar.update_layout(height=300, margin=dict(t=30, b=30, l=10, r=10))
    st.plotly_chart(fig_bar, use_container_width=True)

# Tonality Trend Over Time
with col4:
    trend = filtered_df.groupby([filtered_df["published_parsed"].dt.date, "tonality"]).size().reset_index(name="count")
    fig_area = px.area(trend, x="published_parsed", y="count", color="tonality", title="Tonality Trend Over Time",
                       color_discrete_map={"Positive": "green", "Negative": "red", "Neutral": "grey"})
    fig_area.update_layout(height=300, margin=dict(t=30, b=30, l=10, r=10))
    st.plotly_chart(fig_area, use_container_width=True)

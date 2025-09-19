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

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(creds)

    SHEET_ID = "10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ"
    sh = client.open_by_key(SHEET_ID)
    worksheet = sh.sheet1

    records = worksheet.get_all_records()
    df = pd.DataFrame(records)

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

df["Year"] = df["published_parsed"].dt.year
df["Month"] = df["published_parsed"].dt.strftime("%B")

def get_financial_year(date):
    if pd.isna(date): return None
    year = date.year
    return f"{year}/{year+1}" if date.month >= 7 else f"{year-1}/{year}"
df["FinancialYear"] = df["published_parsed"].apply(get_financial_year)

def get_quarter(date):
    if pd.isna(date): return None
    if date.month in [7,8,9]: return "Q1"
    if date.month in [10,11,12]: return "Q2"
    if date.month in [1,2,3]: return "Q3"
    if date.month in [4,5,6]: return "Q4"
df["Quarter"] = df["published_parsed"].apply(get_quarter)

years = df["Year"].dropna().unique().tolist()
fy = df["FinancialYear"].dropna().unique().tolist()
quarters = df["Quarter"].dropna().unique().tolist()
months = df["Month"].dropna().unique().tolist()

selected_years = st.sidebar.multiselect("Select Year(s)", years, default=years)
selected_fy = st.sidebar.multiselect("Select Financial Year(s)", fy, default=fy)
selected_quarters = st.sidebar.multiselect("Select Quarter(s)", quarters, default=quarters)
selected_months = st.sidebar.multiselect("Select Month(s)", months, default=months)

min_date, max_date = df["published_parsed"].min(), df["published_parsed"].max()
start_date = st.sidebar.date_input("Start Date", min_date.date() if pd.notna(min_date) else None)
end_date = st.sidebar.date_input("End Date", max_date.date() if pd.notna(max_date) else None)

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
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

def kpi_tile(metric, value, color):
    st.markdown(
        f"""
        <div style="background-color:{color}; padding:15px; border-radius:10px; text-align:center; color:white;">
            <h4>{metric}</h4>
            <h2>{value}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

with kpi1: kpi_tile("Total Mentions", len(filtered_df), "#2E7D32")  # green
with kpi2: kpi_tile("Positive", (filtered_df["tonality"]=="Positive").sum(), "#388E3C")
with kpi3: kpi_tile("Negative", (filtered_df["tonality"]=="Negative").sum(), "#C62828")
with kpi4: kpi_tile("Neutral", (filtered_df["tonality"]=="Neutral").sum(), "#757575")

# ---------------- CHART TILES ----------------
st.subheader("Visual Analysis")
row1 = st.columns(2)
row2 = st.columns(2)

# helper for bordered container
def chart_tile(fig, title):
    st.markdown(
        f"""
        <div style="border:1px solid #ddd; border-radius:10px; padding:10px; margin-bottom:15px; background-color:white;">
            <h4 style="text-align:center;">{title}</h4>
        </div>
        """, unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)

# Doughnut chart
with row1[0]:
    tonality_counts = filtered_df["tonality"].value_counts()
    fig_donut = go.Figure(data=[go.Pie(
        labels=tonality_counts.index,
        values=tonality_counts.values,
        hole=0.5,
        marker=dict(colors=["green","red","grey"]),
        textfont=dict(color="white")
    )])
    fig_donut.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=280)
    chart_tile(fig_donut, "Tonality Distribution")

# Mentions over time
with row1[1]:
    ts = filtered_df.groupby(filtered_df["published_parsed"].dt.date).size().reset_index(name="count")
    fig_line = px.line(ts, x="published_parsed", y="count")
    fig_line.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=280)
    chart_tile(fig_line, "Mentions Over Time")

# Top sources
with row2[0]:
    top_sources = filtered_df["source"].value_counts().head(5)
    fig_bar = px.bar(top_sources, x=top_sources.index, y=top_sources.values,
                     labels={"x":"Source","y":"Mentions"})
    fig_bar.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=280)
    chart_tile(fig_bar, "Top 5 News Sources")

# Tonality trend
with row2[1]:
    trend = filtered_df.groupby([filtered_df["published_parsed"].dt.date,"tonality"]).size().reset_index(name="count")
    fig_area = px.area(trend, x="published_parsed", y="count", color="tonality",
                       color_discrete_map={"Positive":"green","Negative":"red","Neutral":"grey"})
    fig_area.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=280)
    chart_tile(fig_area, "Tonality Trend Over Time")

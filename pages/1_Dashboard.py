# pages/1_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import nltk
import gspread
from google.oauth2.service_account import Credentials

# Ensure nltk stopwords are available
nltk.download("stopwords", quiet=True)
from nltk.corpus import stopwords as nltk_stopwords

# ---------------- CONFIG ----------------
HELB_GREEN = "#008000"
HELB_GOLD = "#FFD700"
HELB_BLUE = "#1E90FF"
HELB_RED = "#B22222"
HELB_GREY = "#808080"
HELB_COLORS = [HELB_GREEN, HELB_GOLD, HELB_BLUE, HELB_RED]

# ---------------- LOAD DATA ----------------
@st.cache_data(ttl=600)
def load_data():
    try:
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
    except Exception as e:
        st.error(f"Failed to load Google Sheet: {e}")
        return pd.DataFrame()

    # --- clean columns
    df.columns = [c.strip().lower() for c in df.columns]
    for c in ["title", "summary", "source", "tonality", "link", "published"]:
        if c not in df.columns:
            df[c] = ""

    df["published_parsed"] = pd.to_datetime(df["published"], errors="coerce")
    df["tonality_norm"] = df["tonality"].astype(str).str.strip().str.capitalize()

    # --- extra fields
    df["YEAR"] = df["published_parsed"].dt.year
    df["MONTH_NUM"] = df["published_parsed"].dt.month
    df["MONTH"] = df["published_parsed"].dt.strftime("%b")

    fy = []
    for d in df["published_parsed"]:
        if pd.isnull(d):
            fy.append(None)
        else:
            if d.month >= 7:
                fy.append(f"{d.year}/{d.year+1}")
            else:
                fy.append(f"{d.year-1}/{d.year}")
    df["FINANCIAL_YEAR"] = fy

    def fy_quarter(date):
        if pd.isnull(date):
            return None
        m = date.month
        if m in (7, 8, 9): return "Q1 (Jul–Sep)"
        if m in (10, 11, 12): return "Q2 (Oct–Dec)"
        if m in (1, 2, 3): return "Q3 (Jan–Mar)"
        return "Q4 (Apr–Jun)"
    df["QUARTER"] = df["published_parsed"].apply(fy_quarter)

    return df


df = load_data()
if df.empty:
    st.error("❌ No data loaded. Please check Google Sheet & secrets setup.")
    st.stop()

# ---------------- STYLE ----------------
st.set_page_config(layout="wide", page_title="HELB Dashboard")
st.markdown(
    f"""
    <style>
        .tile {{
            background-color: white;
            padding: 18px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            text-align: center;
            margin-bottom: 10px;
        }}
        .tile h3 {{
            margin: 0;
            font-size: 16px;
            color: {HELB_GREEN};
        }}
        .tile p {{
            font-size: 26px;
            font-weight: 600;
            margin: 6px 0 0;
        }}
        .chart-tile {{
            background-color: white;
            padding: 14px;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            margin-bottom: 18px;
        }}
        .stMultiSelect [data-baseweb="select"] > div {{
            background-color: {HELB_GREEN} !important;
            color: white !important;
            border-radius: 8px;
        }}
        .stMultiSelect span, .stMultiSelect div[aria-label="Main select"] span {{
            color: white !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 HELB Mentions Monitor")
st.write("Overview — use the slicers to filter by Year, Financial Year, Quarter or Month.")

# ---------------- SIDEBAR SLICERS ----------------
st.sidebar.header("🔎 Filters (Slicers)")

years_all = sorted([int(y) for y in df["YEAR"].dropna().unique()])
fys_all = sorted([fy for fy in df["FINANCIAL_YEAR"].dropna().unique()])
quarters_all = ["Q1 (Jul–Sep)", "Q2 (Oct–Dec)", "Q3 (Jan–Mar)", "Q4 (Apr–Jun)"]
months_all = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

selected_years = st.sidebar.multiselect("Select Year(s)", years_all, default=[])
selected_fys = st.sidebar.multiselect("Select Financial Year(s)", fys_all, default=[])
selected_quarters = st.sidebar.multiselect("Select Quarter(s)", quarters_all, default=[])
selected_months = st.sidebar.multiselect("Select Month(s)", months_all, default=[])

filtered = df.copy()
if selected_years:
    filtered = filtered[filtered["YEAR"].isin(selected_years)]
if selected_fys:
    filtered = filtered[filtered["FINANCIAL_YEAR"].isin(selected_fys)]
if selected_quarters:
    filtered = filtered[filtered["QUARTER"].isin(selected_quarters)]
if selected_months:
    filtered = filtered[filtered["MONTH"].isin(selected_months)]

if st.sidebar.button("Clear All Filters"):
    filtered = df.copy()

# ---------------- KPI TILES ----------------
col1, col2, col3, col4 = st.columns(4)

total_mentions = len(filtered)
pos_count = int(filtered["tonality_norm"].str.lower().eq("positive").sum())
neg_count = int(filtered["tonality_norm"].str.lower().eq("negative").sum())
neu_count = int(filtered["tonality_norm"].str.lower().eq("neutral").sum())

with col1:
    st.markdown(f"<div class='tile'><h3>Total Mentions</h3><p style='color:{HELB_BLUE};'>{total_mentions}</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='tile'><h3>Positive</h3><p style='color:{HELB_GREEN};'>{pos_count}</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='tile'><h3>Negative</h3><p style='color:{HELB_RED};'>{neg_count}</p></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='tile'><h3>Neutral</h3><p style='color:{HELB_GREY};'>{neu_count}</p></div>", unsafe_allow_html=True)

st.markdown("---")

# ---------------- (Charts + Wordcloud remain unchanged) ----------------
# your existing Chart A–D and Wordcloud code goes here

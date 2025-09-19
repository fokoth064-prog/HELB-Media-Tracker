# pages/1_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- CONFIG ----------------
CSV_URL = "https://docs.google.com/spreadsheets/d/10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ/export?format=csv"

# HELB Brand Colors
HELB_GREEN = "#008000"
HELB_GOLD = "#FFD700"
HELB_BLUE = "#1E90FF"
HELB_RED = "#B22222"

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data(csv_url):
    df = pd.read_csv(csv_url)

    # Parse date safely
    if "published" in df.columns:
        df["published_parsed"] = pd.to_datetime(df["published"], errors="coerce")
    else:
        df["published_parsed"] = pd.NaT

    # Calendar Year
    df["YEAR"] = df["published_parsed"].dt.year

    # Financial Year (July–June)
    fy = []
    for date in df["published_parsed"]:
        if pd.isnull(date):
            fy.append(None)
        else:
            if date.month >= 7:  # July–Dec → FY start = current year
                fy.append(f"{date.year}/{date.year+1}")
            else:               # Jan–Jun → FY start = prev year
                fy.append(f"{date.year-1}/{date.year}")
    df["FINANCIAL_YEAR"] = fy

    # Quarters (FY-based)
    def fy_quarter(date):
        if pd.isnull(date):
            return None
        m = date.month
        if m in [7, 8, 9]:
            return "Q1 (Jul–Sep)"
        elif m in [10, 11, 12]:
            return "Q2 (Oct–Dec)"
        elif m in [1, 2, 3]:
            return "Q3 (Jan–Mar)"
        else:
            return "Q4 (Apr–Jun)"

    df["QUARTER"] = df["published_parsed"].apply(fy_quarter)

    return df

df = load_data(CSV_URL)

if df.empty:
    st.error("❌ No data loaded. Please check the CSV link.")
    st.stop()

# ---------------- STYLE ----------------
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
        .stMultiSelect [data-baseweb="select"] > div {{
            background-color: {HELB_GREEN} !important;
            color: white !important;
            border-radius: 8px;
        }}
        .stMultiSelect span {{
            color: white !important;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 HELB Dashboard")
st.write("An overview of HELB mentions, sentiment, and trends.")

# ---------------- FILTERS (SLICERS) ----------------
st.sidebar.header("🔎 Filters (Slicers)")

# Available options from data
years_all = sorted([int(y) for y in df["YEAR"].dropna().unique()])
fys_all = sorted([fy for fy in df["FINANCIAL_YEAR"].dropna().unique()])
quarters_all = ["Q1 (Jul–Sep)", "Q2 (Oct–Dec)", "Q3 (Jan–Mar)", "Q4 (Apr–Jun)"]

# User selections
selected_years = st.sidebar.multiselect("Select Year(s)", years_all, default=[])
selected_fys = st.sidebar.multiselect("Select Financial Year(s)", fys_all, default=[])
selected_quarters = st.sidebar.multiselect("Select Quarter(s)", quarters_all, default=[])

# Apply filters
filtered = df.copy()

if selected_years:
    filtered = filtered[filtered["YEAR"].isin(selected_years)]

if selected_fys:
    filtered = filtered[filtered["FINANCIAL_YEAR"].isin(selected_fys)]

# Sync quarters with available data after year/FY filters
quarters_available = sorted(filtered["QUARTER"].dropna().unique())
if selected_quarters:
    filtered = filtered[filtered["QUARTER"].isin(selected_quarters)]

# Reset option
if st.sidebar.button("Clear All Filters"):
    filtered = df.copy()
    selected_years, selected_fys, selected_quarters = [], [], []

# ---------------- KPI TILES ----------------
col1, col2, col3, col4 = st.columns(4)

total_mentions = len(filtered)
positive = filtered[filtered["tonality"] == "Positive"]
negative = filtered[filtered["tonality"] == "Negative"]
neutral = filtered[filtered["tonality"] == "Neutral"]

with col1:
    st.markdown(f"<div class='tile'><h3>Total Mentions</h3><p style='color:{HELB_BLUE};'>{total_mentions}</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='tile'><h3>Positive</h3><p style='color:{HELB_GREEN};'>{len(positive)}</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='tile'><h3>Negative</h3><p style='color:{HELB_RED};'>{len(negative)}</p></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='tile'><h3>Neutral</h3><p style='color:{HELB_GOLD};'>{len(neutral)}</p></div>", unsafe_allow_html=True)

st.markdown("---")

# ---------------- CHARTS ----------------
col5, col6 = st.columns(2)

with col5:
    st.subheader("Tonality Distribution")
    tonality_counts = filtered["tonality"].value_counts().reset_index()
    tonality_counts.columns = ["Tonality", "Count"]
    if not tonality_counts.empty:
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
    else:
        st.info("No data for selected filters.")

with col6:
    st.subheader("Mentions Over Time")
    timeline = filtered.groupby(filtered["published_parsed"].dt.date).size().reset_index(name="Count")
    if not timeline.empty:
        fig_line = px.line(timeline, x="published_parsed", y="Count", markers=True)
        fig_line.update_traces(line_color=HELB_BLUE)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No data for selected filters.")

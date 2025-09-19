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

st.set_page_config(layout="wide", page_title="HELB Media Monitoring Dashboard")

# ---------------- HEADER (Pinned with Logo) ----------------
st.markdown("""
    <style>
    .header-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: linear-gradient(90deg, #006400, #228B22);
        color: white;
        padding: 15px 20px;
        z-index: 100;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.2);
    }
    .header-container img {
        height: 50px;
        margin-right: 20px;
    }
    .header-title {
        font-size: 24px;
        font-weight: bold;
        color: white;
    }
    .main > div {
        padding-top: 100px; /* pushes dashboard down so it’s not hidden */
    }
    </style>
    <div class="header-container">
        <img src="https://www.helb.co.ke/wp-content/uploads/2020/09/cropped-helb-logo.png" alt="HELB Logo">
        <div class="header-title">HELB MEDIA MONITORING DASHBOARD</div>
    </div>
""", unsafe_allow_html=True)

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

# ---------------- CHARTS (2x2 grid) ----------------
colA, colB = st.columns(2)

# --- Chart A: Tonality Doughnut
with colA:
    st.markdown("<div class='chart-tile'>", unsafe_allow_html=True)
    st.subheader("Tonality Distribution")
    ton_order = ["Positive", "Negative", "Neutral"]
    counts = filtered["tonality_norm"].value_counts().reindex(ton_order).fillna(0).astype(int)
    donut_df = pd.DataFrame({"Tonality": counts.index, "Count": counts.values})

    if donut_df["Count"].sum() > 0:
        fig_donut = px.pie(
            donut_df,
            names="Tonality",
            values="Count",
            hole=0.54,
            color="Tonality",
            color_discrete_map={"Positive": HELB_GREEN, "Negative": HELB_RED, "Neutral": HELB_GREY},
        )
        fig_donut.update_traces(textposition="inside", textinfo="percent+label", insidetextfont=dict(color="white"))
        fig_donut.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("No tonality data for selected filters.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Chart B: Mentions Over Time
with colB:
    st.markdown("<div class='chart-tile'>", unsafe_allow_html=True)
    st.subheader("Mentions Over Time")
    if filtered["published_parsed"].notna().any():
        times = filtered.copy()
        times["date_only"] = times["published_parsed"].dt.date
        timeline = times.groupby("date_only").size().reset_index(name="count")
        timeline["date"] = pd.to_datetime(timeline["date_only"])
        fig_line = px.line(timeline.sort_values("date"), x="date", y="count", markers=True)
        fig_line.update_traces(line_color=HELB_BLUE)
        fig_line.update_layout(margin=dict(t=10, b=20, l=20, r=10), height=300)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No date information available for selected filters.")
    st.markdown("</div>", unsafe_allow_html=True)

colC, colD = st.columns(2)

# --- Chart C: Top Sources
with colC:
    st.markdown("<div class='chart-tile'>", unsafe_allow_html=True)
    st.subheader("Top News Sources")
    src_counts = filtered["source"].fillna("Unknown").value_counts().head(7).reset_index()
    if not src_counts.empty:
        src_counts.columns = ["Source", "Count"]
        fig_bar = px.bar(
            src_counts.sort_values("Count"),
            x="Count",
            y="Source",
            orientation="h",
            text="Count",
        )
        fig_bar.update_traces(marker_color=HELB_GREEN)
        fig_bar.update_layout(margin=dict(t=6, b=6, l=6, r=6), yaxis=dict(dtick=1), height=300)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No source data for selected filters.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Chart D: Tonality Trend
with colD:
    st.markdown("<div class='chart-tile'>", unsafe_allow_html=True)
    st.subheader("Tonality Trend Over Time (Monthly)")
    if filtered["published_parsed"].notna().any():
        trend = (
            filtered.assign(month=filtered["published_parsed"].dt.to_period("M").astype(str))
            .groupby(["month", "tonality_norm"])
            .size()
            .reset_index(name="count")
        )
        if not trend.empty:
            trend["month_dt"] = pd.to_datetime(trend["month"].astype(str) + "-01", errors="coerce")
            trend = trend.sort_values("month_dt")
            fig_area = px.area(
                trend,
                x="month",
                y="count",
                color="tonality_norm",
                color_discrete_map={"Positive": HELB_GREEN, "Negative": HELB_RED, "Neutral": HELB_GREY},
            )
            fig_area.update_layout(margin=dict(t=6, b=6, l=6, r=6), legend_title_text="Tonality", height=300)
            st.plotly_chart(fig_area, use_container_width=True)
        else:
            st.info("No tonality trend data for selected filters.")
    else:
        st.info("No date information for trend chart.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ---------------- WORD CLOUD ----------------
st.markdown("<div class='chart-tile'>", unsafe_allow_html=True)
if st.button("☁️ View Word Cloud"):
    st.subheader("Keyword Word Cloud")
    title_col = "title" if "title" in filtered.columns else "TITLE"
    summary_col = "summary" if "summary" in filtered.columns else "SUMMARY"
    texts = (filtered[title_col].astype(str) + " " + filtered[summary_col].astype(str)).tolist()
    big_text = " ".join(texts).strip()
    if big_text:
        stop_words = set(nltk_stopwords.words("english")) | set(STOPWORDS)

        def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
            idx = abs(hash(word)) % len(HELB_COLORS)
            return HELB_COLORS[idx]

        wc = WordCloud(
            width=900,
            height=400,
            background_color="white",
            stopwords=stop_words,
            color_func=color_func,
        ).generate(big_text)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
    else:
        st.info("No text available to generate word cloud.")
st.markdown("</div>", unsafe_allow_html=True)

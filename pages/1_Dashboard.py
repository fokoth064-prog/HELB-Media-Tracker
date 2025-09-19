import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="HELB Media Monitoring Dashboard", layout="wide")

# --- Custom CSS for Header ---
st.markdown(
    """
    <style>
        .main-header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 9999;
            background: linear-gradient(135deg, #006400, #228B22); /* Dark to lighter green */
            color: white;
            display: flex;
            align-items: center;
            padding: 15px 25px;
            font-size: 28px;
            font-weight: bold;
            box-shadow: 0px 4px 6px rgba(0,0,0,0.2);
        }
        .main-header img {
            height: 50px;
            margin-right: 15px;
        }
        .main-header h1 {
            margin: 0;
            font-size: 26px;
            color: white;
        }
        /* Add space below header so content isn’t hidden */
        .main-content {
            margin-top: 110px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header with Logo + Title ---
st.markdown(
    """
    <div class="main-header">
        <img src="https://www.helb.co.ke/wp-content/uploads/2022/03/helb-logo.png" alt="HELB Logo">
        <h1>HELB MEDIA MONITORING DASHBOARD</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Main Content Area ---
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# --- Load Data from Google Sheets ---
sheet_url = "https://docs.google.com/spreadsheets/d/your_google_sheet_id_here/export?format=csv"
try:
    df = pd.read_csv(sheet_url)

    # Ensure date column is datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # --- Sidebar Filters ---
    st.sidebar.header("🔎 Filter Options")

    # Date Range Filter
    if "date" in df.columns:
        min_date = df["date"].min()
        max_date = df["date"].max()
        start_date, end_date = st.sidebar.date_input(
            "Select Date Range",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        df = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]

    # Keyword Search
    keyword = st.sidebar.text_input("Search by Keyword")
    if keyword:
        df = df[df.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]

    # Sentiment Filter (if column exists)
    if "sentiment" in df.columns:
        sentiment_options = st.sidebar.multiselect("Filter by Sentiment", df["sentiment"].unique())
        if sentiment_options:
            df = df[df["sentiment"].isin(sentiment_options)]

    # --- KPIs (Summary Cards) ---
    st.subheader("📌 Key Metrics")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Mentions", len(df))

    if "sentiment" in df.columns:
        with col2:
            positive = (df["sentiment"] == "positive").sum()
            st.metric("Positive Mentions", positive)

        with col3:
            negative = (df["sentiment"] == "negative").sum()
            st.metric("Negative Mentions", negative)

    # --- Data Table ---
    st.subheader("📊 Filtered Media Mentions")
    st.dataframe(df)

    # --- Charts ---
    if "date" in df.columns and not df.empty:
        mentions_by_date = df.groupby(df["date"].dt.date).size().reset_index(name="mentions")
        fig = px.line(mentions_by_date, x="date", y="mentions", title="Mentions Over Time")
        st.plotly_chart(fig, use_container_width=True)

    if "sentiment" in df.columns and not df.empty:
        sentiment_count = df["sentiment"].value_counts().reset_index()
        sentiment_count.columns = ["sentiment", "count"]
        fig2 = px.pie(sentiment_count, names="sentiment", values="count", title="Sentiment Distribution")
        st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.error(f"❌ Could not load data. Error: {e}")

st.markdown('</div>', unsafe_allow_html=True)

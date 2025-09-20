import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import gspread
from google.oauth2.service_account import Credentials
import time

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="HELB Media Monitoring Dashboard",
    layout="wide"
)

# ---------------------------
# Load Data with Retry
# ---------------------------
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

        # retry wrapper
        def safe_get_records(ws, retries=3, delay=5):
            for i in range(retries):
                try:
                    return ws.get_all_records()
                except Exception as e:
                    if i < retries - 1:
                        time.sleep(delay)
                    else:
                        raise e

        records = safe_get_records(worksheet)
        df = pd.DataFrame(records)

        # ensure correct datetime
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        return df

    except Exception as e:
        st.error(f"❌ Failed to load Google Sheet: {e}")
        return pd.DataFrame()

df = load_data()

# ---------------------------
# Dashboard Title
# ---------------------------
st.markdown(
    """
    <div style="background-color:#006400;padding:15px;border-radius:10px;">
        <h1 style="color:white;text-align:center;">HELB MEDIA MONITORING DASHBOARD</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Filters
# ---------------------------
if not df.empty:
    st.sidebar.header("Filter Data")

    # Date filter
    min_date, max_date = df["Date"].min(), df["Date"].max()
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Platform filter
    platforms = st.sidebar.multiselect(
        "Select Platforms",
        options=df["Platform"].unique(),
        default=df["Platform"].unique()
    )

    # Apply filters
    filtered_df = df[
        (df["Date"].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) &
        (df["Platform"].isin(platforms))
    ]

    # ---------------------------
    # KPIs
    # ---------------------------
    total_mentions = len(filtered_df)
    positive_mentions = len(filtered_df[filtered_df["Sentiment"] == "Positive"])
    negative_mentions = len(filtered_df[filtered_df["Sentiment"] == "Negative"])
    neutral_mentions = len(filtered_df[filtered_df["Sentiment"] == "Neutral"])

    st.markdown("### 📊 Key Metrics")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Mentions", total_mentions)
    kpi2.metric("Positive Mentions", positive_mentions)
    kpi3.metric("Negative Mentions", negative_mentions)
    kpi4.metric("Neutral Mentions", neutral_mentions)

    # ---------------------------
    # Charts
    # ---------------------------
    st.markdown("### 📈 Trends and Visualizations")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Mentions Over Time**")
        mentions_over_time = filtered_df.groupby("Date").size()
        fig, ax = plt.subplots(figsize=(6, 4))
        mentions_over_time.plot(ax=ax, marker="o")
        ax.set_ylabel("Number of Mentions")
        ax.set_xlabel("Date")
        st.pyplot(fig)

    with col2:
        st.markdown("**Sentiment Distribution**")
        sentiment_counts = filtered_df["Sentiment"].value_counts()
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(x=sentiment_counts.index, y=sentiment_counts.values, palette="Set2", ax=ax)
        ax.set_ylabel("Count")
        ax.set_xlabel("Sentiment")
        st.pyplot(fig)

    # ---------------------------
    # Word Cloud
    # ---------------------------
    st.markdown("### ☁️ Word Cloud")
    all_text = " ".join(filtered_df["Content"].dropna().astype(str))
    if all_text.strip():
        wordcloud = WordCloud(width=800, height=400, background_color="white").generate(all_text)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
    else:
        st.info("No content available to generate word cloud.")

else:
    st.warning("No data available. Please check your Google Sheet.")

# ---------------------------
# Footer
# ---------------------------
st.markdown(
    """
    <hr>
    <div style="text-align:center; padding:10px; color:gray;">
        Developed by <b>Fred Okoth</b>
    </div>
    """,
    unsafe_allow_html=True
)

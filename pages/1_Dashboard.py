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
    df["published_parsed"] = pd.to_datetime(df["published"], errors="coerce")

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
            re

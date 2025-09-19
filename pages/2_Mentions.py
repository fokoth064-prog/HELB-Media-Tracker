# pages/2_Mentions.py
import streamlit as st
import pandas as pd

# ---------- CONFIG ----------
CSV_URL = "https://docs.google.com/spreadsheets/d/10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ/export?format=csv"

# ---------- HARD-CODED PASSWORD ----------
EDITOR_PASSWORD = "MyHardSecret123"  # change this string anytime
password = st.sidebar.text_input("Enter edit password", type="password")
is_editor = password == EDITOR_PASSWORD

if is_editor:
    st.sidebar.success("Editor mode ✅")
else:
    st.sidebar.info("Read-only mode 🔒")

# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Parse dates
    if "published" in df.columns:
        df["published_parsed"] = pd.to_datetime(df["published"], errors="coerce", utc=True)
        try:
            df["published_parsed"] = df["published_parsed"].dt.tz_convert("Africa/Nairobi")
        except Exception:
            pass
        df["DATE"] = df["published_parsed"].dt.strftime("%d-%b-%Y")
        df["TIME"] = df["published_parsed"].dt.strftime("%H:%M")
    else:
        df["published_parsed"] = pd.NaT
        df["DATE"] = ""
        df["TIME"] = ""

    # Ensure required columns exist
    for col in ["title", "summary", "source", "tonality", "link"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")

    # Rename to uppercase
    rename_map = {
        "title": "TITLE",
        "summary": "SUMMARY",
        "source": "SOURCE",
        "tonality": "TONALITY",
        "link": "LINK",
    }
    df = df.rename(columns=rename_map)
    return df

# ---------- INITIALIZE SESSION STATE ----------
if "mentions_df" not in st.session_state:
    st.session_state["mentions_df"] = load_data()

df = st.session_state["mentions_df"]

if df.empty:
    st.info("No data available. Check the CSV URL.")
    st.stop()

# Sort newest first
df = df.sort_values(by="published_parsed", ascending=False).reset_index(drop=True)

# ---------- COLOR MAP (original) ----------
COLORS = {
    "Positive": "#dff7df",  # light green
    "Neutral": "#f3f3f3",   # light grey
    "Negative": "#ffd6d6"   # light red
}

# ---------- DISPLAY MENTIONS ----------
st.title("📰 Mentions — Media Coverage")

for i, row in df.iterrows():
    with st.container():
        # Always show colored div with tonality
        bg_color = COLORS.get(row["TONALITY"], "#ffffff")
        st.markdown(
            f"""
            <div style="background-color:{bg_color}; padding:15px; border-radius:8px; margin-bottom:10px;">
                <b>{i+1}. {row['DATE']} {row['TIME']}</b><br>
                <b>Source:</b> {row['SOURCE']}<br>
                <b>Title:</b> {row['TITLE']}<br>
                <b>Summary:</b> {row['SUMMARY']}<br>
                <b>Tonality:</b> {row['TONALITY']}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Editable tonality only for editor, below the div
        if is_editor:
            new_tonality = st.selectbox(
                f"Update Tonality for mention #{i+1}",
                options=["Positive", "Neutral", "Negative"],
                index=["Positive","Neutral","Negative"].index(row["TONALITY"]) if row["TONALITY"] in ["Positive","Neutral","Negative"] else 1,
                key=f"tonality_{i}"
            )
            if new_tonality != row["TONALITY"]:
                st.session_state["mentions_df"].at[i, "TONALITY"] = new_tonality

        # Read full story link
        if row["LINK"].startswith("http"):
            st.markdown(f"[🔗 Read Full Story]({row['LINK']})")

        st.markdown("---")


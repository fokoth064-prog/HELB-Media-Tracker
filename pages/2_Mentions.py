# pages/2_Mentions.py
import streamlit as st
import pandas as pd

# ---------- CONFIG ----------
CSV_URL = "https://docs.google.com/spreadsheets/d/10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ/export?format=csv"
EDITOR_PASSWORD = "MyHardSecret123"

# ---------- PASSWORD ----------
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
    df.columns = [c.strip().lower() for c in df.columns]
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
    for col in ["title", "summary", "source", "tonality", "link"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")
    rename_map = {
        "title": "TITLE",
        "summary": "SUMMARY",
        "source": "SOURCE",
        "tonality": "TONALITY",
        "link": "LINK",
    }
    df = df.rename(columns=rename_map)
    return df

# ---------- SESSION STATE ----------
if "mentions_df" not in st.session_state:
    st.session_state["mentions_df"] = load_data()
df = st.session_state["mentions_df"]

if df.empty:
    st.info("No data available.")
    st.stop()

df = df.sort_values(by="published_parsed", ascending=False).reset_index(drop=True)

# Tonality mapping
if "tonality_map" not in st.session_state:
    st.session_state["tonality_map"] = {i: df.at[i, "TONALITY"] for i in df.index}

COLORS = {
    "Positive": "#3b8132",
    "Neutral": "#f3f3f3",
    "Negative": "#ff9999"
}

st.title("📰 Mentions — Media Coverage")

# ---------- EDITOR DROPDOWNS ----------
if is_editor:
    st.subheader("Edit Tonality")
    for i in df.index:
        row = df.loc[i]
        current = st.session_state["tonality_map"][i]
        new_val = st.selectbox(
            f"{i+1}. {row['TITLE'][:50]}...",
            options=["Positive", "Neutral", "Negative"],
            index=["Positive","Neutral","Negative"].index(current) if current in ["Positive","Neutral","Negative"] else 1,
            key=f"tonality_{i}"
        )
        if new_val != current:
            st.session_state["tonality_map"][i] = new_val

st.subheader("Mentions List")
# ---------- DISPLAY MENTIONS ----------
for i in df.index:
    row = df.loc[i]
    tonality = st.session_state["tonality_map"][i]
    bg = COLORS.get(tonality, "#ffffff")
    st.markdown(
        f"""
        <div style="background-color:{bg}; padding:15px; border-radius:8px; margin-bottom:10px;">
            <b>{i+1}. {row['DATE']} {row['TIME']}</b><br>
            <b>Source:</b> {row['SOURCE']}<br>
            <b>Title:</b> {row['TITLE']}<br>
            <b>Summary:</b> {row['SUMMARY']}<br>
            <b>Tonality:</b> {tonality}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if row["LINK"].startswith("http"):
        st.markdown(f"[🔗 Read Full Story]({row['LINK']})")
    st.markdown("---")

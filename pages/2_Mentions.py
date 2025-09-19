# pages/2_Mentions.py
import streamlit as st
import pandas as pd

# ---------- CONFIG ----------
CSV_URL = "https://docs.google.com/spreadsheets/d/10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ/export?format=csv"

# ---------- PASSWORD ----------
EDITOR_PASSWORD = "MyHardSecret123"
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
    st.info("No data available. Check the CSV URL.")
    st.stop()

df = df.sort_values(by="published_parsed", ascending=False).reset_index(drop=True)

# ---------- COLOR MAP ----------
COLORS = {
    "Positive": "#a3d9a5",  # darker green
    "Neutral": "#f3f3f3",
    "Negative": "#ff9999"   # darker red
}

# ---------- DISPLAY ----------
st.title("📰 Mentions — Media Coverage")

for i in df.index:
    row = df.loc[i]

    # Editor mode with form
    if is_editor:
        with st.form(key=f"form_{i}"):
            current_tonality = st.session_state["mentions_df"].at[i, "TONALITY"]
            new_tonality = st.selectbox(
                f"Update Tonality for mention #{i+1}",
                options=["Positive", "Neutral", "Negative"],
                index=["Positive","Neutral","Negative"].index(current_tonality) if current_tonality in ["Positive","Neutral","Negative"] else 1
            )
            submitted = st.form_submit_button("Update")
            if submitted and new_tonality != current_tonality:
                st.session_state["mentions_df"].at[i, "TONALITY"] = new_tonality

    # Always read the current tonality from session_state
    display_tonality = st.session_state["mentions_df"].at[i, "TONALITY"]
    bg_color = COLORS.get(display_tonality, "#ffffff")

    st.markdown(
        f"""
        <div style="background-color:{bg_color}; padding:15px; border-radius:8px; margin-bottom:10px;">
            <b>{i+1}. {row['DATE']} {row['TIME']}</b><br>
            <b>Source:</b> {row['SOURCE']}<br>
            <b>Title:</b> {row['TITLE']}<br>
            <b>Summary:</b> {row['SUMMARY']}<br>
            <b>Tonality:</b> {display_tonality}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if row["LINK"].startswith("http"):
        st.markdown(f"[🔗 Read Full Story]({row['LINK']})")

    st.markdown("---")

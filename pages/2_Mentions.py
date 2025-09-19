# mentions.py
import streamlit as st
import pandas as pd

# ---------- CONFIG ----------
CSV_URL = "https://docs.google.com/spreadsheets/d/10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ/export?format=csv"

# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    df['published_parsed'] = pd.to_datetime(df['published'], errors='coerce')
    return df

# Keep a session copy for edits
if "mentions_df" not in st.session_state:
    st.session_state.mentions_df = load_data()

df = st.session_state.mentions_df

st.title("💬 Mentions")

# ---------- FILTERS ----------
st.sidebar.header("Filters")
sources = sorted(df['source'].dropna().unique())
source_filter = st.sidebar.multiselect("Source", options=sources, default=sources)

tonalities = ["Positive", "Negative", "Neutral"]
tonality_filter = st.sidebar.multiselect("Tonality", options=tonalities, default=tonalities)

filtered = df[
    df['source'].isin(source_filter) &
    df['tonality'].isin(tonality_filter)
]

# ---------- DISPLAY ----------
if not filtered.empty:
    st.write("### Mentions View (with Manual Tonality Editing)")

    # Sort latest first
    filtered = filtered.sort_values(by="published_parsed", ascending=False).reset_index(drop=True)

    for i, row in filtered.iterrows():
        # background colors by tonality
        if row['tonality'] == "Positive":
            color = "#228B22"
        elif row['tonality'] == "Negative":
            color = "#B22222"
        else:
            color = "#696969"
        text_color = "white"

        st.markdown(
            f"""
            <div style="background-color:{color}; color:{text_color}; 
                        padding:15px; border-radius:10px; margin-bottom:10px">
                <b>{i+1}. {row['title']}</b><br>
                <i>Date: {row['published_parsed'].strftime("%d %B %Y")} | Source: {row['source']}</i><br><br>
                {row['summary']}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Dropdown to override tonality
        new_tonality = st.selectbox(
            f"Update Tonality for mention {i+1}",
            tonalities,
            index=tonalities.index(row['tonality']),
            key=f"tonality_{i}"
        )

        # Update the dataframe if changed
        if new_tonality != row['tonality']:
            st.session_state.mentions_df.loc[row.name, 'tonality'] = new_tonality

        # Add link if available
        if 'link' in row and pd.notna(row['link']):
            st.markdown(f"[🔗 Read full story]({row['link']})", unsafe_allow_html=True)

        st.markdown("---")

    # Option to download corrected dataset
    st.download_button(
        "💾 Download Corrected Mentions CSV",
        data=st.session_state.mentions_df.to_csv(index=False).encode("utf-8"),
        file_name="mentions_corrected.csv",
        mime="text/csv"
    )
else:
    st.warning("No mentions available for selected filters.")


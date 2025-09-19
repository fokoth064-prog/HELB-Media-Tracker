import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------- CONFIG ----------
SPREADSHEET_ID = "your_spreadsheet_id"  # Replace with your Google Sheet ID
WORKSHEET_NAME = "Sheet1"  # Replace with your worksheet name
EDITOR_PASSWORD = "MyHardSecret123"

# ---------- PASSWORD ----------
password = st.sidebar.text_input("Enter edit password", type="password")
is_editor = password == EDITOR_PASSWORD
if is_editor:
    st.sidebar.success("Editor mode ✅")
else:
    st.sidebar.info("Read-only mode 🔒")

# ---------- GOOGLE SHEETS AUTHENTICATION ----------
@st.cache_resource
def authenticate_gspread():
    creds = Credentials.from_service_account_info(
        st.secrets["connections"]["gsheets"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client

client = authenticate_gspread()
worksheet = client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

# ---------- LOAD DATA ----------
def load_data():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = [col.strip().lower() for col in df.columns]
    return df

df = load_data()

if df.empty:
    st.info("No data available.")
    st.stop()

df = df.sort_values(by="published", ascending=False).reset_index(drop=True)

# ---------- EDITOR PANEL ----------
if is_editor:
    st.sidebar.subheader("Edit Tonality")
    edited_values = {}

    with st.sidebar.container():
        st.markdown(
            '<div style="max-height:600px; overflow-y:auto; padding-right:5px;">', 
            unsafe_allow_html=True
        )
        for i in df.index:
            current = df.at[i, "tonality"]
            new_val = st.selectbox(
                f"{i+1}. {df.at[i, 'title'][:50]}...",
                options=["Positive", "Neutral", "Negative"],
                index=["Positive","Neutral","Negative"].index(current) if current in ["Positive","Neutral","Negative"] else 1,
                key=f"tonality_{i}"
            )
            edited_values[i] = new_val
        st.markdown('</div>', unsafe_allow_html=True)

    # Execute update button
    if st.sidebar.button("Execute Update"):
        for idx, val in edited_values.items():
            df.at[idx, "tonality"] = val
            worksheet.update_cell(idx + 2, df.columns.get_loc("tonality") + 1, val)  # Update Google Sheet
        st.sidebar.success("Tonality changes applied and saved!")

# ---------- DISPLAY MENTIONS ----------
st.title("📰 Mentions — Media Coverage")
st.subheader("Mentions List")

for i in df.index:
    row = df.loc[i]
    tonality = row["tonality"]
    bg_color = "#3b8132" if tonality == "Positive" else "#6E6F71" if tonality == "Neutral" else "#d1001f"
    text_color = "#ffffff" if tonality in ["Positive", "Negative"] else "#ffffff"

    st.markdown(
        f"""
        <div style="
            background-color:{bg_color};
            color:{text_color};
            padding:15px;
            border-radius:8px;
            margin-bottom:10px;
        ">
            <b>{i+1}. {row['published']}</b><br>
            <b>Source:</b> {row['source']}<br>
            <b>Title:</b> {row['title']}<br>
            <b>Summary:</b> {row['summary']}<br>
            <b>Tonality:</b> {tonality}
        </div>
        """,
        unsafe_allow_html=True
    )
    if row["link"].startswith("http"):
        st.markdown(f"[🔗 Read Full Story]({row['link']})")
    st.markdown("---")

# ---------- DOWNLOAD UPDATED CSV ----------
st.subheader("Export Updated Mentions")
csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 Download Updated Mentions CSV",
    data=csv_bytes,
    file_name="updated_mentions.csv",
    mime="text/csv"
)

# pages/3_Keyword_Trends.py
import streamlit as st
import pandas as pd

st.title("🔑 Keyword Trends")

# Example keyword counts
data = {
    "keyword": ["loan", "repayment", "support"],
    "count": [120, 75, 40]
}
df = pd.DataFrame(data)

st.write("### Keyword Frequency")
st.bar_chart(df.set_index("keyword"))

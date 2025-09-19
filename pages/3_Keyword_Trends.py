# pages/3_Keyword_Trends.py
import streamlit as st
import pandas as pd
from collections import Counter
from itertools import islice
import re

st.title("🔑 Keyword Trends")

# -------------------------------
# 🔹 Example mentions dataset (replace with your real data)
# -------------------------------
mentions = [
    {"date": "2025-09-15", "source": "Twitter", "title": "Loan repayment is overdue"},
    {"date": "2025-09-15", "source": "Facebook", "title": "Customer support was helpful"},
    {"date": "2025-09-14", "source": "News", "title": "Loan services are fast"},
    {"date": "2025-09-13", "source": "Blog", "title": "Repayment options are flexible"},
    {"date": "2025-09-12", "source": "News", "title": "Good support team for repayment"},
]

# Combine all titles for keyword extraction
all_text = " ".join([m["title"] for m in mentions]).lower()

# Simple tokenizer (split words, remove punctuation)
tokens = re.findall(r"\b\w+\b", all_text)

# -------------------------------
# 🔹 Keyword Frequency
# -------------------------------
word_counts = Counter(tokens)
df_keywords = pd.DataFrame(word_counts.items(), columns=["keyword", "count"]).sort_values(
    by="count", ascending=False
)

st.subheader("Top Keywords")
top_n = st.slider("Select number of top keywords", 5, 20, 10)
st.dataframe(df_keywords.head(top_n), use_container_width=True)

# -------------------------------
# 🔹 N-grams (bigrams & trigrams)
# -------------------------------
def get_ngrams(tokens, n):
    return zip(*[tokens[i:] for i in range(n)])

bigrams = Counter(get_ngrams(tokens, 2))
trigrams = Counter(get_ngrams(tokens, 3))

df_bigrams = pd.DataFrame(
    [(" ".join(k), v) for k, v in bigrams.items()],
    columns=["bigram", "count"]
).sort_values(by="count", ascending=False)

df_trigrams = pd.DataFrame(
    [(" ".join(k), v) for k, v in trigrams.items()],
    columns=["trigram", "count"]
).sort_values(by="count", ascending=False)

st.subheader("Top Bigrams")
st.dataframe(df_bigrams.head(10), use_container_width=True)

st.subheader("Top Trigrams")
st.dataframe(df_trigrams.head(10), use_container_width=True)

# -------------------------------
# 🔹 Export option
# -------------------------------
st.subheader("Export Data")
csv = df_keywords.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download keyword frequencies as CSV",
    csv,
    "keyword_frequencies.csv",
    "text/csv",
    key="download-csv",
)


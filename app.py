import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Column Pair Sorter", layout="wide")

st.title("📊 Column Pair Sorter (Info + Debug by ID)")

# =========================
# Upload
# =========================
uploaded_file = st.file_uploader("📥 Upload CSV file", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)
    st.write("### 🔍 Preview Data")
    st.dataframe(df.head())

    columns = df.columns.tolist()

    # =========================
    # Detect columns
    # =========================
    datetime_cols = [c for c in columns if "time" in c.lower() or "date" in c.lower()]
    info_cols = [c for c in columns if "info" in c.lower()]
    debug_cols = [c for c in columns if "debug" in c.lower()]

    st.write("### 🧠 Detected Columns")
    st.write("Datetime:", datetime_cols)
    st.write("Info:", info_cols)
    st.write("Debug:", debug_cols)

    # =========================
    # Extract ID
    # =========================
    def extract_id(col):
        match = re.search(r'(\d+)', col)
        return int(match.group(1)) if match else float('inf')

    # =========================
    # Pair Info + Debug
    # =========================
    pairs = []

    for info in info_cols:
        info_id = extract_id(info)

        matched_debug = None
        for debug in debug_cols:
            if extract_id(debug) == info_id:
                matched_debug = debug
                break

        pairs.append((info_id, info, matched_debug))

    # =========================
    # Sort
    # =========================
    pairs_sorted = sorted(pairs, key=lambda x: x[0])

    # =========================
    # Build new columns
    # =========================
    new_columns = []

    new_columns.extend(datetime_cols)

    for _, info, debug in pairs_sorted:
        if info:
            new_columns.append(info)
        if debug:
            new_columns.append(debug)

    new_columns = [c for c in new_columns if c in df.columns]

    df_new = df[new_columns]

    st.write("### ✅ Result Preview")
    st.dataframe(df_new.head())

    # =========================
    # Download
    # =========================
    csv = df_new.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Download Sorted CSV",
        data=csv,
        file_name="sorted_columns.csv",
        mime="text/csv",
    )

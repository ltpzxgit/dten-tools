import streamlit as st
import pandas as pd
from io import BytesIO
import sys
import os

# 🔥 FIX import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processors.dten_linkage import process_dten_linkage, process_device_list

st.set_page_config(page_title="DTEN Tool", layout="wide")
st.title("🔥 DTEN Tool (Multi-Sheet)")

file_req = st.file_uploader("📥 Upload Request File")
file_res = st.file_uploader("📥 Upload Response File")


# =========================
# Utils
# =========================
def read_file(f):
    try:
        if f.name.endswith("csv"):
            return pd.read_csv(f, encoding="utf-8-sig")
        return pd.read_excel(f)
    except Exception as e:
        st.error(f"❌ Read file error: {e}")
        st.stop()


def normalize_columns(df):
    df.columns = df.columns.str.strip().str.lower()
    return df


# =========================
# Main
# =========================
if file_req and file_res:

    df_req = normalize_columns(read_file(file_req))
    df_res = normalize_columns(read_file(file_res))

    st.write("📊 Request Columns:", df_req.columns.tolist())
    st.write("📊 Response Columns:", df_res.columns.tolist())

    # =========================
    # Process
    # =========================
    try:
        df_linkage = process_dten_linkage(df_req.copy(), df_res.copy())
    except Exception as e:
        st.error(f"❌ Linkage Error: {e}")
        st.stop()

    try:
        df_device = process_device_list(
            df_req.copy(),
            df_linkage.copy()
        )
    except Exception as e:
        st.error(f"❌ Device List Error: {e}")
        st.stop()

    # =========================
    # Show
    # =========================
    st.subheader("📄 Sheet 1: DTEN Linkage")
    st.dataframe(df_linkage, use_container_width=True)

    st.subheader("📄 Sheet 2: Device List")
    st.dataframe(df_device, use_container_width=True)

    # =========================
    # Download
    # =========================
    output = BytesIO()

    try:
        import xlsxwriter
        engine = "xlsxwriter"
    except:
        engine = "openpyxl"

    with pd.ExcelWriter(output, engine=engine) as writer:
        df_linkage.to_excel(writer, sheet_name="DTEN Linkage", index=False)
        df_device.to_excel(writer, sheet_name="Device List", index=False)

    output.seek(0)

    st.download_button(
        "📥 Download Excel (All Sheets)",
        data=output,
        file_name="final_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👆 Upload both Request + Response")

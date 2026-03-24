import streamlit as st
import pandas as pd
from io import BytesIO

from processors.dten_linkage import process_dten_linkage, process_device_list

st.set_page_config(page_title="DTEN Tool", layout="wide")
st.title("🔥 DTEN Tool (Multi-Sheet)")

file_req = st.file_uploader("📥 Upload Request File")
file_res = st.file_uploader("📥 Upload Response File")

def read_file(f):
    return pd.read_csv(f) if f.name.endswith("csv") else pd.read_excel(f)

if file_req and file_res:

    df_req = read_file(file_req)
    df_res = read_file(file_res)

    # =========================
    # Process
    # =========================
    df_linkage = process_dten_linkage(df_req.copy(), df_res.copy())
    df_device = process_device_list(df_req.copy())

    # =========================
    # Show
    # =========================
    st.subheader("📄 Sheet 1: DTEN Linkage")
    st.dataframe(df_linkage, use_container_width=True)

    st.subheader("📄 Sheet 2: Device List")
    st.dataframe(df_device, use_container_width=True)

    # =========================
    # Download (Multi Sheet)
    # =========================
    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
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

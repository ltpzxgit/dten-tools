import streamlit as st
import pandas as pd
from io import BytesIO

from processors.dten_linkage import process_dten_linkage

st.title("🔥 DTEN Tool")

file_req = st.file_uploader("Upload Request")
file_res = st.file_uploader("Upload Response")

if file_req and file_res:

    df_req = pd.read_csv(file_req) if file_req.name.endswith("csv") else pd.read_excel(file_req)
    df_res = pd.read_csv(file_res) if file_res.name.endswith("csv") else pd.read_excel(file_res)

    # 🔥 เรียกใช้ module
    df_result = process_dten_linkage(df_req, df_res)

    st.dataframe(df_result)

    output = BytesIO()
    df_result.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        "Download",
        data=output,
        file_name="result.xlsx"
    )

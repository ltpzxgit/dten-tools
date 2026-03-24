import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="DTEN Linkage Table", layout="wide")
st.title("🔥 DTEN Linkage (Match Final Sheet)")

# =========================
# Upload
# =========================
file_req = st.file_uploader("📥 Upload File 1 (Request)", type=["csv", "xlsx"])
file_res = st.file_uploader("📥 Upload File 2 (Response)", type=["csv", "xlsx"])


# =========================
# Extract Functions
# =========================
def extract_request_id(text):
    if pd.isna(text):
        return None
    match = re.search(r'[0-9a-fA-F\-]{30,}', str(text))
    return match.group(0) if match else None


# =========================
# Process
# =========================
if file_req and file_res:

    df_req = pd.read_csv(file_req) if file_req.name.endswith("csv") else pd.read_excel(file_req)
    df_res = pd.read_csv(file_res) if file_res.name.endswith("csv") else pd.read_excel(file_res)

    # =========================
    # Build Request Table
    # =========================
    df_req["Request ID"] = df_req.apply(
        lambda row: extract_request_id(" ".join(map(str, row.values))),
        axis=1
    )

    df_req["Request"] = df_req.apply(
        lambda row: " ".join(map(str, row.values)),
        axis=1
    )

    # 👉 date (ถ้ามี)
    if "date" in df_req.columns:
        df_req["date"] = df_req["date"]
    else:
        df_req["date"] = ""

    df_req = df_req.dropna(subset=["Request ID"])

    # =========================
    # Build Response Table
    # =========================
    df_res["Request ID"] = df_res.apply(
        lambda row: extract_request_id(" ".join(map(str, row.values))),
        axis=1
    )

    df_res["Response"] = df_res.apply(
        lambda row: " ".join(map(str, row.values)),
        axis=1
    )

    df_res = df_res.dropna(subset=["Request ID"])

    # =========================
    # 🔥 MERGE (1:1)
    # =========================
    df_merge = pd.merge(
        df_req[["Request ID", "date", "Request"]],
        df_res[["Request ID", "Response"]],
        on="Request ID",
        how="left"
    )

    # =========================
    # Add No.
    # =========================
    df_merge = df_merge.reset_index(drop=True)
    df_merge["No."] = df_merge.index + 1

    # =========================
    # Arrange Columns (เหมือน Excel)
    # =========================
    df_merge = df_merge[[
        "No.",
        "date",
        "Request ID",
        "Request",
        "Response"
    ]]

    # =========================
    # Show
    # =========================
    st.success("✅ DTEN Linkage = ตรงรูปเป๊ะ")
    st.dataframe(df_merge, use_container_width=True)

    # =========================
    # Download
    # =========================
    output = BytesIO()
    df_merge.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        "📥 Download DTEN Linkage",
        data=output,
        file_name="DTEN_Linkage.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👆 Upload Request + Response files")

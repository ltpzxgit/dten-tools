import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="DTEN Raw Table", layout="wide")
st.title("🔥 DTEN Raw Log Table (Match Excel)")

# =========================
# Upload
# =========================
file_req = st.file_uploader("📥 Upload Request File", type=["csv", "xlsx"])
file_res = st.file_uploader("📥 Upload Response File", type=["csv", "xlsx"])


# =========================
# Extract RequestId
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
    # Request File
    # =========================
    df_req["Request ID"] = df_req.apply(
        lambda row: extract_request_id(" ".join(map(str, row.values))),
        axis=1
    )

    df_req["Request"] = df_req.apply(
        lambda row: " ".join(map(str, row.values)),
        axis=1
    )

    # =========================
    # Response File
    # =========================
    df_res["Request ID"] = df_res.apply(
        lambda row: extract_request_id(" ".join(map(str, row.values))),
        axis=1
    )

    df_res["Response"] = df_res.apply(
        lambda row: " ".join(map(str, row.values)),
        axis=1
    )

    # =========================
    # 🔥 MERGE (ไม่ group)
    # =========================
    df_merge = pd.merge(
        df_req[["Request ID", "Request"]],
        df_res[["Request ID", "Response"]],
        on="Request ID",
        how="left"
    )

    # =========================
    # Add No. + date (optional)
    # =========================
    df_merge = df_merge.reset_index(drop=True)
    df_merge["No."] = df_merge.index + 1

    # ถ้ามี column date ใน request จะเอามาใช้
    if "date" in df_req.columns:
        df_merge["date"] = df_req["date"]

    # =========================
    # Reorder Columns
    # =========================
    cols = ["No.", "date", "Request ID", "Request", "Response"]
    cols = [c for c in cols if c in df_merge.columns]

    df_merge = df_merge[cols]

    # =========================
    # Show
    # =========================
    st.success("✅ Matched Raw Table (เหมือน Excel)")
    st.dataframe(df_merge, use_container_width=True)

    # =========================
    # Download
    # =========================
    output = BytesIO()
    df_merge.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        "📥 Download Excel",
        data=output,
        file_name="DTEN_Raw_Table.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👆 Upload Request + Response files")

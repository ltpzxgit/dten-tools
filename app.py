import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="DTEN Linkage Tool", layout="wide")
st.title("🔥 DTEN Linkage (INFO + DEBUG Pairing)")

# =========================
# Upload
# =========================
file_req = st.file_uploader("📥 Upload File 1 (Request)", type=["csv", "xlsx"])
file_res = st.file_uploader("📥 Upload File 2 (Response)", type=["csv", "xlsx"])

# =========================
# Regex
# =========================
REQ_ID_REGEX = r'Request ID:\s*([0-9a-fA-F\-]{36})'
DT_REGEX = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'

# =========================
# Functions
# =========================
def extract_datetime(text):
    match = re.search(DT_REGEX, text)
    return match.group(0) if match else None

def extract_request_id(text):
    match = re.search(REQ_ID_REGEX, text)
    return match.group(1) if match else None

def read_file(f):
    return pd.read_csv(f) if f.name.endswith("csv") else pd.read_excel(f)

# =========================
# Process
# =========================
if file_req and file_res:

    df_req = read_file(file_req)
    df_res = read_file(file_res)

    # รวม row เป็น text
    df_req["raw"] = df_req.apply(lambda r: " ".join(map(str, r.values)), axis=1)

    # =========================
    # 🔥 Pair INFO + DEBUG
    # =========================
    records = []
    current = {}

    for row in df_req["raw"]:

        # INFO → start record
        if "INFO" in row and "Request ID" in row:
            if current:
                records.append(current)
                current = {}

            current["Request ID"] = extract_request_id(row)
            current["date"] = extract_datetime(row)

        # DEBUG → attach request body
        elif "DEBUG" in row and "Request:" in row:
            if "Request:" in row:
                current["Request"] = row.split("Request:", 1)[1]

    # append last
    if current:
        records.append(current)

    df_req_clean = pd.DataFrame(records)

    # =========================
    # RESPONSE
    # =========================
    df_res["raw"] = df_res.apply(lambda r: " ".join(map(str, r.values)), axis=1)

    df_res["Request ID"] = df_res["raw"].apply(extract_request_id)
    df_res["Response"] = df_res["raw"]

    df_res = df_res.dropna(subset=["Request ID"])

    df_res_group = df_res.groupby("Request ID").agg({
        "Response": lambda x: " ".join(x)
    }).reset_index()

    # =========================
    # MERGE
    # =========================
    df_final = pd.merge(
        df_req_clean,
        df_res_group,
        on="Request ID",
        how="left"
    )

    # =========================
    # Sort + No.
    # =========================
    df_final = df_final.sort_values("date").reset_index(drop=True)
    df_final["No."] = df_final.index + 1

    # =========================
    # Arrange
    # =========================
    df_final = df_final[[
        "No.",
        "date",
        "Request ID",
        "Request",
        "Response"
    ]]

    # =========================
    # Show
    # =========================
    st.success("✅ DONE (INFO+DEBUG Pairing ถูกแล้ว)")
    st.dataframe(df_final, use_container_width=True)

    # =========================
    # Download
    # =========================
    output = BytesIO()
    df_final.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        "📥 Download Final Result",
        data=output,
        file_name="final_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👆 Upload Request + Response")

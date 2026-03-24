import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="DTEN Linkage Tool", layout="wide")
st.title("🔥 DTEN Linkage (Final Auto Tool - FIXED)")

# =========================
# Upload
# =========================
file_req = st.file_uploader("📥 Upload File 1 (Request)", type=["csv", "xlsx"])
file_res = st.file_uploader("📥 Upload File 2 (Response)", type=["csv", "xlsx"])

# =========================
# Regex
# =========================
GUID_REGEX = r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'
DT_REGEX = r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}'

# =========================
# Extract Functions
# =========================
def extract_request_id(row):
    # 🔥 1. หา column ที่มีคำว่า request ก่อน (แม่นสุด)
    for col in row.index:
        val = str(row[col])
        if "request" in col.lower():
            match = re.search(GUID_REGEX, val)
            if match:
                return match.group(0)

    # 🔥 2. fallback: หาในทั้ง row
    full_text = " ".join(map(str, row.values))
    match = re.search(GUID_REGEX, full_text)
    return match.group(0) if match else None


def extract_datetime(text):
    if pd.isna(text):
        return pd.NaT
    match = re.search(DT_REGEX, str(text))
    return pd.to_datetime(match.group(0)) if match else pd.NaT


def cut_ldcm(text):
    if pd.isna(text):
        return ""
    text = str(text)
    idx = text.find("LDCMLists")
    return text[idx:] if idx != -1 else ""


def read_file(f):
    return pd.read_csv(f) if f.name.endswith("csv") else pd.read_excel(f)

# =========================
# Process
# =========================
if file_req and file_res:

    df_req = read_file(file_req)
    df_res = read_file(file_res)

    # =========================
    # REQUEST
    # =========================
    df_req["raw"] = df_req.apply(lambda r: " ".join(map(str, r.values)), axis=1)

    df_req["Request ID"] = df_req.apply(extract_request_id, axis=1)
    df_req["date"] = df_req["raw"].apply(extract_datetime)
    df_req["Request"] = df_req["raw"].apply(cut_ldcm)

    df_req = df_req.dropna(subset=["Request ID"])

    # 🔥 รวม Request
    df_req_group = df_req.groupby("Request ID").agg({
        "date": "min",
        "Request": lambda x: " ".join([i for i in x if i])
    }).reset_index()

    df_req_group["date"] = df_req_group["date"].dt.strftime("%Y/%m/%d %H:%M:%S")

    # =========================
    # RESPONSE
    # =========================
    df_res["raw"] = df_res.apply(lambda r: " ".join(map(str, r.values)), axis=1)

    df_res["Request ID"] = df_res.apply(extract_request_id, axis=1)
    df_res["Response"] = df_res["raw"].apply(cut_ldcm)

    df_res = df_res.dropna(subset=["Request ID"])

    # 🔥 รวม Response
    df_res_group = df_res.groupby("Request ID").agg({
        "Response": lambda x: " ".join([i for i in x if i])
    }).reset_index()

    # =========================
    # MERGE
    # =========================
    df_final = pd.merge(
        df_req_group,
        df_res_group,
        on="Request ID",
        how="left"
    )

    # =========================
    # Sort + No.
    # =========================
    df_final["_dt"] = pd.to_datetime(df_final["date"], errors="coerce")
    df_final = df_final.sort_values("_dt").drop(columns=["_dt"]).reset_index(drop=True)

    df_final["No."] = df_final.index + 1

    # =========================
    # Final Format
    # =========================
    df_final = df_final[[
        "No.",
        "date",
        "Request ID",
        "Request",
        "Response"
    ]]

    # =========================
    # Debug (เช็คว่าดึง ID ได้จริง)
    # =========================
    st.write("🔍 Sample Request IDs:")
    st.write(df_final["Request ID"].head(10))

    # =========================
    # Show
    # =========================
    st.success("✅ DONE (Request ID FIXED)")
    st.dataframe(df_final, use_container_width=True)

    # =========================
    # Download
    # =========================
    output = BytesIO()
    df_final.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        label="📥 Download Final Result",
        data=output,
        file_name="final_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👆 Upload Request + Response")

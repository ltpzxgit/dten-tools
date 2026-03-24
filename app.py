import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="DTEN Linkage Tool", layout="wide")
st.title("🔥 DTEN Linkage (Auto Combine → Final Result)")

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


def extract_datetime(text):
    if pd.isna(text):
        return None
    match = re.search(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', str(text))
    return match.group(0) if match else None


def cut_ldcm(text):
    if pd.isna(text):
        return ""
    text = str(text)
    idx = text.find("LDCMLists")
    return text[idx:] if idx != -1 else ""


# =========================
# Process
# =========================
if file_req and file_res:

    df_req = pd.read_csv(file_req) if file_req.name.endswith("csv") else pd.read_excel(file_req)
    df_res = pd.read_csv(file_res) if file_res.name.endswith("csv") else pd.read_excel(file_res)

    # =========================
    # REQUEST
    # =========================
    df_req["raw"] = df_req.apply(lambda r: " ".join(map(str, r.values)), axis=1)

    df_req["Request ID"] = df_req["raw"].apply(extract_request_id)
    df_req["date"] = df_req["raw"].apply(extract_datetime)
    df_req["Request"] = df_req["raw"].apply(cut_ldcm)

    df_req = df_req.dropna(subset=["Request ID"])

    # 🔥 รวม Request (สำคัญ)
    df_req_group = df_req.groupby("Request ID").agg({
        "date": "first",
        "Request": lambda x: " ".join([i for i in x if i])
    }).reset_index()

    # =========================
    # RESPONSE
    # =========================
    df_res["raw"] = df_res.apply(lambda r: " ".join(map(str, r.values)), axis=1)

    df_res["Request ID"] = df_res["raw"].apply(extract_request_id)
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
    # Add No.
    # =========================
    df_final = df_final.reset_index(drop=True)
    df_final["No."] = df_final.index + 1

    # =========================
    # Arrange Columns
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
    st.success("✅ Final Result (เหมือน manual แล้ว)")
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

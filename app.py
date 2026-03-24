import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="DTEN Linkage Tool", layout="wide")
st.title("🔥 DTEN Linkage Processor (Match Final)")

# =========================
# Upload Files
# =========================
file_req = st.file_uploader("📥 Upload File 1 (Request)", type=["csv", "xlsx"])
file_res = st.file_uploader("📥 Upload File 2 (Response)", type=["csv", "xlsx"])


# =========================
# Extract Functions
# =========================
def extract_device_id(text):
    if pd.isna(text):
        return None
    match = re.search(r'\b[A-Z]{1,4}\d{4,8}\b', str(text))
    return match.group(0) if match else None


def extract_request_id(text):
    if pd.isna(text):
        return None
    match = re.search(r'\b[0-9a-fA-F\-]{30,}\b', str(text))
    return match.group(0) if match else None


def extract_from_row(row):
    device = None
    request = None

    for val in row:
        if not device:
            device = extract_device_id(val)
        if not request:
            request = extract_request_id(val)

    return pd.Series([device, request])


# =========================
# Process
# =========================
if file_req and file_res:

    # ===== Read Files =====
    df_req = pd.read_csv(file_req) if file_req.name.endswith("csv") else pd.read_excel(file_req)
    df_res = pd.read_csv(file_res) if file_res.name.endswith("csv") else pd.read_excel(file_res)

    # =========================
    # Extract Request File
    # =========================
    extracted_req = df_req.apply(extract_from_row, axis=1)
    extracted_req.columns = ["deviceId", "RequestId"]

    df_req["deviceId"] = extracted_req["deviceId"]
    df_req["RequestId"] = extracted_req["RequestId"]

    df_req = df_req.dropna(subset=["deviceId", "RequestId"])

    # =========================
    # Extract Response File
    # =========================
    df_res["RequestId"] = df_res.apply(
        lambda row: extract_request_id(" ".join(map(str, row.values))),
        axis=1
    )

    df_res["Result"] = df_res.apply(
        lambda row: " ".join(map(str, row.values)),
        axis=1
    )

    df_res = df_res.dropna(subset=["RequestId"])

    # =========================
    # 🔥 MERGE (หัวใจ)
    # =========================
    df_merge = pd.merge(
        df_req,
        df_res[["RequestId", "Result"]],
        on="RequestId",
        how="left"
    )

    st.write(f"🔍 Devices Found: {df_merge['deviceId'].nunique()}")

    # =========================
    # Group → 1 device ต่อ 1 row
    # =========================
    df_result = df_merge.groupby("deviceId").agg({
        "RequestId": "last",
        "Result": "last"
    }).reset_index()

    # =========================
    # Apply Business Logic
    # =========================
    df_result = df_result.sort_values("deviceId").reset_index(drop=True)

    df_result["No."] = df_result.index + 1
    df_result["ProStatus"] = "PROD"

    df_result["Carrier"] = df_result["deviceId"].apply(
        lambda x: "AIS" if str(x).startswith("A") else "TRUE"
    )

    df_result["DTENLinkage Result"] = df_result["Result"]

    df_result["sent to AIS"] = df_result["Carrier"].apply(
        lambda x: "Yes" if x == "AIS" else "No"
    )

    df_result["received from AIS"] = df_result["sent to AIS"]

    # =========================
    # Final Column Order (เหมือน sheet)
    # =========================
    final_cols = [
        "No.",
        "deviceId",
        "RequestId",
        "ProStatus",
        "Carrier",
        "DTENLinkage Result",
        "sent to AIS",
        "received from AIS"
    ]

    df_result = df_result[final_cols]

    # =========================
    # Show Result
    # =========================
    st.success("✅ Result Matched (DTEN Linkage)")
    st.dataframe(df_result, use_container_width=True)

    # =========================
    # Download (ไม่เป็น .bin)
    # =========================
    output = BytesIO()
    df_result.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        label="📥 Download DTEN Linkage Result",
        data=output,
        file_name="DTEN_Linkage_Result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👆 Upload Request + Response Files")

import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="DTEN Tool", layout="wide")
st.title("📊 DTEN Linkage Processor")

# =========================
# Upload Section
# =========================
dten_file = st.file_uploader("📥 Upload DTENLinkage File", type=["csv", "xlsx"])
tcap_file = st.file_uploader("📥 Upload DTENTCAPLinkage File", type=["csv", "xlsx"])
template_file = st.file_uploader("📥 Upload Template File", type=["xlsx"])


# =========================
# Helper Functions
# =========================
def extract_device_id(text):
    if pd.isna(text):
        return None
    text = str(text)
    match = re.search(r'\b[A-Z]{1,4}\d{4,8}\b', text)
    return match.group(0) if match else None


def extract_request_id(text):
    if pd.isna(text):
        return None
    text = str(text)
    match = re.search(r'\b[0-9a-fA-F\-]{30,}\b', text)
    return match.group(0) if match else None


def extract_all_from_row(row):
    device = None
    request_id = None

    for val in row:
        if not device:
            device = extract_device_id(val)
        if not request_id:
            request_id = extract_request_id(val)

    return pd.Series([device, request_id])


# =========================
# Process
# =========================
if dten_file and tcap_file and template_file:

    # --- Read files ---
    df_dten = pd.read_csv(dten_file) if dten_file.name.endswith("csv") else pd.read_excel(dten_file)
    df_tcap = pd.read_csv(tcap_file) if tcap_file.name.endswith("csv") else pd.read_excel(tcap_file)
    df_template = pd.read_excel(template_file)

    # --- Clean column name ---
    df_template.columns = df_template.columns.str.strip()

    # =========================
    # Extract (DTEN)
    # =========================
    df_dten[["deviceId", "RequestId"]] = df_dten.apply(extract_all_from_row, axis=1)
    df_dten = df_dten.dropna(subset=["deviceId"])

    st.write(f"🔍 Found Devices (DTEN): {df_dten['deviceId'].nunique()}")

    # =========================
    # Build Result Table
    # =========================
    df_result = pd.DataFrame()
    df_result["deviceId"] = sorted(df_dten["deviceId"].unique())

    # No.
    df_result = df_result.reset_index(drop=True)
    df_result["No."] = df_result.index + 1

    # RequestId (ล่าสุด)
    req_map = df_dten.groupby("deviceId")["RequestId"].last().to_dict()
    df_result["RequestId"] = df_result["deviceId"].map(req_map)

    # ProStatus
    df_result["ProStatus"] = "PROD"

    # Carrier
    df_result["Carrier"] = df_result["deviceId"].apply(
        lambda x: "AIS" if str(x).startswith("A") else "TRUE"
    )

    # DTEN Result (เอา log ล่าสุด)
    df_dten["full_text"] = df_dten.astype(str).apply(lambda row: " ".join(row), axis=1)
    result_map = df_dten.groupby("deviceId")["full_text"].last().to_dict()
    df_result["DTENLinkage Result"] = df_result["deviceId"].map(result_map)

    # =========================
    # TCAP
    # =========================
    df_tcap["deviceId"] = df_tcap.apply(lambda row: extract_device_id(" ".join(map(str, row))), axis=1)
    df_tcap = df_tcap.dropna(subset=["deviceId"])

    tcap_set = set(df_tcap["deviceId"])

    df_result["DTENTCAPLinkage"] = df_result["deviceId"].apply(
        lambda x: "Yes" if x in tcap_set else "No"
    )

    # =========================
    # AIS Logic
    # =========================
    df_result["sent to AIS"] = df_result["Carrier"].apply(
        lambda x: "Yes" if x == "AIS" else "No"
    )

    df_result["received from AIS"] = df_result["sent to AIS"]

    # =========================
    # 🔒 TEMPLATE LOCK (ห้ามเพี้ยน)
    # =========================
    final_df = df_template.copy()

    result_map_full = df_result.set_index("deviceId").to_dict(orient="index")

    for idx, row in final_df.iterrows():
        device = str(row.get("deviceId", "")).strip()

        if device in result_map_full:
            data = result_map_full[device]

            for col in final_df.columns:
                if col in data:
                    final_df.at[idx, col] = data[col]

    # =========================
    # Validation
    # =========================
    missing = set(df_result["deviceId"]) - set(final_df["deviceId"])
    if missing:
        st.warning(f"⚠️ Missing devices in template: {len(missing)}")

    # =========================
    # Output
    # =========================
    st.success("✅ Process completed successfully")
    st.dataframe(final_df, use_container_width=True)

    output_file = "result.xlsx"
    final_df.to_excel(output_file, index=False)

    with open(output_file, "rb") as f:
        st.download_button("📥 Download Result", f, file_name=output_file)

else:
    st.info("👆 Upload all files to start")

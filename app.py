import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="DTEN Full Processor", layout="wide")
st.title("🔥 DTEN Full Processor (All Columns)")

# =========================
# Upload Files
# =========================
uploaded_files = st.file_uploader(
    "📥 Upload Raw Files (1-8)",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

# =========================
# Extract Functions
# =========================
def extract_device_id(text):
    if pd.isna(text):
        return None
    return re.search(r'\b[A-Z]{1,4}\d{4,8}\b', str(text)).group(0) \
        if re.search(r'\b[A-Z]{1,4}\d{4,8}\b', str(text)) else None


def extract_request_id(text):
    if pd.isna(text):
        return None
    return re.search(r'\b[0-9a-fA-F\-]{30,}\b', str(text)).group(0) \
        if re.search(r'\b[0-9a-fA-F\-]{30,}\b', str(text)) else None


def extract_row(row):
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
if uploaded_files:

    all_df = []

    for file in uploaded_files:
        df = pd.read_csv(file) if file.name.endswith("csv") else pd.read_excel(file)

        df[["deviceId", "RequestId"]] = df.apply(extract_row, axis=1)
        df = df.dropna(subset=["deviceId"])

        df["raw_text"] = df.astype(str).agg(" ".join, axis=1)

        all_df.append(df)

    df_all = pd.concat(all_df, ignore_index=True)

    st.write(f"🔍 Devices Found: {df_all['deviceId'].nunique()}")

    # =========================
    # Build Base Table
    # =========================
    devices = sorted(df_all["deviceId"].unique())

    df_result = pd.DataFrame({
        "No.": range(1, len(devices) + 1),
        "deviceId": devices
    })

    # =========================
    # RequestId (ล่าสุด)
    # =========================
    req_map = df_all.groupby("deviceId")["RequestId"].last().to_dict()
    df_result["RequestId"] = df_result["deviceId"].map(req_map)

    # =========================
    # ProStatus
    # =========================
    df_result["ProStatus"] = "PROD"

    # =========================
    # Carrier
    # =========================
    df_result["Carrier"] = df_result["deviceId"].apply(
        lambda x: "AIS" if str(x).startswith("A") else "TRUE"
    )

    # =========================
    # DTEN Result (เอา log ล่าสุด)
    # =========================
    result_map = df_all.groupby("deviceId")["raw_text"].last().to_dict()
    df_result["DTENLinkage Result"] = df_result["deviceId"].map(result_map)

    # =========================
    # TCAP Detection
    # =========================
    tcap_devices = set(
        df_all[df_all["raw_text"].str.contains("TCAP", na=False)]["deviceId"]
    )

    df_result["DTENTCAPLinkage"] = df_result["deviceId"].apply(
        lambda x: "Yes" if x in tcap_devices else "No"
    )

    # =========================
    # AIS Logic
    # =========================
    df_result["sent to AIS"] = df_result["Carrier"].apply(
        lambda x: "Yes" if x == "AIS" else "No"
    )

    df_result["received from AIS"] = df_result["sent to AIS"]

    # =========================
    # Output
    # =========================
    st.success("✅ Done (Full Columns)")
    st.dataframe(df_result, use_container_width=True)

    df_result.to_excel("final_result.xlsx", index=False)

    with open("final_result.xlsx", "rb") as f:
        st.download_button("📥 Download Final Result", f)

else:
    st.info("👆 Upload files to start")

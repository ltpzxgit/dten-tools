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
# Helper
# =========================
def extract_device_id(text):
    if pd.isna(text):
        return None
    match = re.search(r'[A-Z]{1,3}\d{5}', str(text))
    return match.group(0) if match else None


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
    # Extract Device ID
    # =========================
    df_dten["deviceId"] = df_dten.astype(str).apply(lambda row: extract_device_id(" ".join(row)), axis=1)
    df_dten = df_dten.dropna(subset=["deviceId"])

    # =========================
    # Build Result Table
    # =========================
    df_result = pd.DataFrame()
    df_result["deviceId"] = df_dten["deviceId"].unique()

    # ProStatus
    df_result["ProStatus"] = "PROD"

    # Carrier
    df_result["Carrier"] = df_result["deviceId"].apply(
        lambda x: "AIS" if str(x).startswith("A") else "TRUE"
    )

    # DTENLinkage Result
    df_dten["full_text"] = df_dten.astype(str).apply(lambda row: " ".join(row), axis=1)
    result_map = df_dten.groupby("deviceId")["full_text"].first().to_dict()
    df_result["DTENLinkage Result"] = df_result["deviceId"].map(result_map)

    # =========================
    # TCAP Check
    # =========================
    df_tcap["deviceId"] = df_tcap.astype(str).apply(lambda row: extract_device_id(" ".join(row)), axis=1)
    tcap_set = set(df_tcap["deviceId"].dropna())

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
    # 🔒 FIX TEMPLATE (สำคัญสุด)
    # =========================
    final_df = df_template.copy()

    result_map_full = df_result.set_index("deviceId").to_dict(orient="index")

    if "deviceId" in final_df.columns:

        for idx, row in final_df.iterrows():
            device = row["deviceId"]

            if device in result_map_full:
                for col in result_map_full[device]:
                    if col in final_df.columns:
                        final_df.at[idx, col] = result_map_full[device][col]

    else:
        st.warning("⚠️ Template ไม่มี column deviceId → ใช้ append แทน")
        final_df = pd.concat([final_df, df_result], ignore_index=True)

    # =========================
    # Validation
    # =========================
    missing = set(df_result["deviceId"]) - set(final_df["deviceId"])
    if missing:
        st.warning(f"⚠️ Missing devices in template: {len(missing)}")

    # lock column order
    final_df = final_df[df_template.columns]

    # =========================
    # Output
    # =========================
    st.success("✅ Process completed successfully")
    st.dataframe(final_df, use_container_width=True)

    output_file = "result.xlsx"
    final_df.to_excel(output_file, index=False)

    with open(output_file, "rb") as f:
        st.download_button(
            "📥 Download Result",
            f,
            file_name=output_file
        )

else:
    st.info("👆 Upload all files to start")

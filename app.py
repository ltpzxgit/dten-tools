import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="DTEN Log → History Tool", layout="wide")
st.title("🚀 DTEN Log → History Builder")

# =========================
# 🔥 Extract log function
# =========================
def extract_log(df, log_type="request"):
    records = []
    current_id = None

    for msg in df["@message"].astype(str):

        # หา Request ID
        id_match = re.search(r"Request ID:\s*([a-f0-9\-]+)", msg)
        if id_match:
            current_id = id_match.group(1)

        # หา payload
        if "Request:" in msg or "Response:" in msg:
            records.append({
                "requestId": current_id,
                f"{log_type}_payload": msg.strip()
            })

    return pd.DataFrame(records)


# =========================
# Upload
# =========================
files = st.file_uploader("📥 Upload CSV (request/response)", accept_multiple_files=True)
template_file = st.file_uploader("📄 Upload History Template (.xlsx)")

if files and template_file:

    req_list = []
    res_list = []

    # =========================
    # แยก + extract
    # =========================
    for file in files:
        filename = file.name.lower()

        df_raw = pd.read_csv(file)

        if "@message" not in df_raw.columns:
            st.error(f"❌ ไฟล์ {file.name} ไม่มี @message")
            st.stop()

        if "request" in filename:
            df = extract_log(df_raw, "request")
            req_list.append(df)

        elif "response" in filename:
            df = extract_log(df_raw, "response")
            res_list.append(df)

    if not req_list or not res_list:
        st.error("❌ ต้องมีทั้ง request และ response")
        st.stop()

    df_req = pd.concat(req_list, ignore_index=True)
    df_res = pd.concat(res_list, ignore_index=True)

    # =========================
    # 🔥 Merge
    # =========================
    df_merge = pd.merge(
        df_req,
        df_res,
        on="requestId",
        how="left"
    )

    # =========================
    # โหลด template
    # =========================
    df_template = pd.read_excel(template_file)

    # =========================
    # 🔥 Map → History
    # =========================
    df_final = pd.DataFrame()

    for col in df_template.columns:

        if col.lower() in ["request id", "requestid"]:
            df_final[col] = df_merge["requestId"]

        elif "request" in col.lower() and "time" in col.lower():
            df_final[col] = df_merge["request_payload"].str.extract(
                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
            )

        elif "response" in col.lower() and "time" in col.lower():
            df_final[col] = df_merge["response_payload"].str.extract(
                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
            )

        elif "request" in col.lower():
            df_final[col] = df_merge["request_payload"]

        elif "response" in col.lower():
            df_final[col] = df_merge["response_payload"]

        elif "status" in col.lower():
            df_final[col] = df_merge["response_payload"].str.extract(
                r"status[=: ]+(\w+)"
            )

        else:
            df_final[col] = None

    # =========================
    # Format
    # =========================
    for col in df_final.columns:
        if "time" in col.lower():
            df_final[col] = pd.to_datetime(df_final[col], errors="coerce")

    # =========================
    # Preview
    # =========================
    st.subheader("🔍 Preview")
    st.dataframe(df_final.head(20), use_container_width=True)

    # =========================
    # Download
    # =========================
    output = io.BytesIO()
    df_final.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        "⬇️ Download History Result",
        data=output,
        file_name="history_result.xlsx"
    )

    st.success("✅ Build เสร็จแล้ว พร้อมใช้")

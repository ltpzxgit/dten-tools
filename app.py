import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Log Mapper Tool", layout="wide")

st.title("🚀 Log → History Mapper (Request + Response)")

# =========================
# Upload files
# =========================
files = st.file_uploader("📥 Upload CSV Files", accept_multiple_files=True)

if files:

    req_list = []
    res_list = []

    # =========================
    # แยก request / response
    # =========================
    for file in files:
        filename = file.name.lower()
        df = pd.read_csv(file)

        if "request" in filename:
            req_list.append(df)
        elif "response" in filename:
            res_list.append(df)

    if not req_list or not res_list:
        st.error("❌ ต้องมีทั้ง request และ response")
        st.stop()

    df_req = pd.concat(req_list, ignore_index=True)
    df_res = pd.concat(res_list, ignore_index=True)

    # =========================
    # 🔥 Merge request + response
    # =========================
    # 👉 เปลี่ยน key ตรงนี้ตามจริง เช่น requestId / correlationId
    merge_key = "requestId"

    if merge_key not in df_req.columns or merge_key not in df_res.columns:
        st.error(f"❌ ไม่เจอ column '{merge_key}' ในไฟล์")
        st.stop()

    df_merge = pd.merge(
        df_req,
        df_res,
        on=merge_key,
        how="left",
        suffixes=("_req", "_res")
    )

    # =========================
    # 🔥 Map Columns → History Format
    # =========================
    # 👉 แก้ mapping ตรงนี้ให้ตรงกับ History ของมึง
    column_mapping = {
        "requestId": "Request ID",
        "timestamp_req": "Request Time",
        "timestamp_res": "Response Time",
        "message_req": "Request Payload",
        "message_res": "Response Payload",
        "status_res": "Status"
    }

    df_final = pd.DataFrame()

    for src, dest in column_mapping.items():
        if src in df_merge.columns:
            df_final[dest] = df_merge[src]
        else:
            df_final[dest] = None

    # =========================
    # Optional: sort
    # =========================
    if "Request Time" in df_final.columns:
        df_final["Request Time"] = pd.to_datetime(df_final["Request Time"], errors="coerce")
        df_final = df_final.sort_values(by="Request Time")

    # =========================
    # Preview
    # =========================
    st.subheader("🔍 Preview")
    st.dataframe(df_final.head(20), use_container_width=True)

    # =========================
    # Download Excel
    # =========================
    output = io.BytesIO()
    df_final.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        label="⬇️ Download Excel",
        data=output,
        file_name="mapped_history.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.success("✅ Ready to download!")

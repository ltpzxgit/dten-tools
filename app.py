import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="CSV → History Builder", layout="wide")

st.title("📊 Build History from Raw CSV")

# =========================
# Upload
# =========================
csv_files = st.file_uploader("📥 Upload CSV (8 files)", accept_multiple_files=True)
history_template = st.file_uploader("📄 Upload History Template (.xlsx)")

if csv_files and history_template:

    # =========================
    # โหลด template
    # =========================
    df_template = pd.read_excel(history_template)

    st.subheader("📌 Template Columns")
    st.write(df_template.columns.tolist())

    # =========================
    # แยก request / response
    # =========================
    req_list = []
    res_list = []

    for file in csv_files:
        name = file.name.lower()
        df = pd.read_csv(file)

        if "request" in name:
            req_list.append(df)
        elif "response" in name:
            res_list.append(df)

    df_req = pd.concat(req_list, ignore_index=True)
    df_res = pd.concat(res_list, ignore_index=True)

    # =========================
    # 🔥 Merge (สำคัญ)
    # =========================
    merge_key = "requestId"  # 👉 เปลี่ยนตามของจริง

    df_merge = pd.merge(
        df_req,
        df_res,
        on=merge_key,
        how="left",
        suffixes=("_req", "_res")
    )

    # =========================
    # 🔥 Mapping แบบ Flexible
    # =========================
    df_final = pd.DataFrame()

    for col in df_template.columns:

        # 👇 logic mapping (แก้ตรงนี้ให้ match ของจริง)
        if col == "Request ID":
            df_final[col] = df_merge.get("requestId")

        elif col == "Request Time":
            df_final[col] = df_merge.get("timestamp_req")

        elif col == "Response Time":
            df_final[col] = df_merge.get("timestamp_res")

        elif col == "Request":
            df_final[col] = df_merge.get("message_req")

        elif col == "Response":
            df_final[col] = df_merge.get("message_res")

        elif col == "Status":
            df_final[col] = df_merge.get("status_res")

        else:
            # column ที่ไม่มีใน raw → ใส่ค่าว่าง
            df_final[col] = None

    # =========================
    # Format เพิ่ม
    # =========================
    if "Request Time" in df_final.columns:
        df_final["Request Time"] = pd.to_datetime(df_final["Request Time"], errors="coerce")

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

    st.success("✅ Build สำเร็จ")

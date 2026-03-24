import pandas as pd
import re

REQ_ID_REGEX = r'Request ID:\s*([0-9a-fA-F\-]{36})'
DT_REGEX = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'


# =========================
# COMMON
# =========================
def extract_datetime(text):
    match = re.search(DT_REGEX, text)
    return match.group(0) if match else None


def extract_request_id(text):
    match = re.search(REQ_ID_REGEX, text)
    return match.group(1) if match else None


def extract_ldcm(text):
    if pd.isna(text):
        return ""
    text = str(text).replace('"""', '"')
    match = re.search(r'(\{?\"?LDCMLists.*)', text)
    return match.group(1) if match else ""


def extract_all_device_ids(text):
    if pd.isna(text):
        return []
    return re.findall(r'\b[A-Z]{3}\d{5}\b', str(text))


# 🔥 NEW
def extract_quantity(text):
    if pd.isna(text):
        return None
    match = re.search(r'Quantity\s*=\s*(\d+)', str(text))
    return int(match.group(1)) if match else None


# =========================
# SHEET 1
# =========================
def process_dten_linkage(df_req, df_res):

    df_req["raw"] = df_req.apply(lambda r: " ".join(map(str, r.values)), axis=1)

    records_req = []
    current = {}

    for row in df_req["raw"]:

        if "INFO" in row and "Request ID" in row:
            if current:
                records_req.append(current)
                current = {}

            current["Request ID"] = extract_request_id(row)
            current["date"] = extract_datetime(row)

        elif "DEBUG" in row and "Request:" in row:
            current["Request"] = extract_ldcm(row)

    if current:
        records_req.append(current)

    df_req_clean = pd.DataFrame(records_req)

    # ===== RESPONSE =====
    df_res["raw"] = df_res.apply(lambda r: " ".join(map(str, r.values)), axis=1)

    records_res = []
    last_response = None

    for row in df_res["raw"]:

        if "Response:" in row:
            last_response = extract_ldcm(row)

        if "Request ID" in row:
            req_id = extract_request_id(row)

            if req_id:
                records_res.append({
                    "Request ID": req_id,
                    "Response": last_response if last_response else ""
                })

    df_res_group = pd.DataFrame(records_res)

    df_final = pd.merge(
        df_req_clean,
        df_res_group,
        on="Request ID",
        how="left"
    )

    df_final = df_final.sort_values("date", ascending=False).reset_index(drop=True)
    df_final["No."] = df_final.index + 1

    return df_final[[
        "No.",
        "date",
        "Request ID",
        "Request",
        "Response"
    ]]


# =========================
# SHEET 2
# =========================
def process_device_list(df_req, df_linkage):

    df_req["raw"] = df_req.apply(lambda r: " ".join(map(str, r.values)), axis=1)

    records = []
    current_req_id = None

    for row in df_req["raw"]:

        if "INFO" in row and "Request ID" in row:
            current_req_id = extract_request_id(row)

        elif "DEBUG" in row and "Request:" in row:
            devices = extract_all_device_ids(row)

            for d in devices:
                records.append({
                    "Request ID": current_req_id,
                    "deviceId": d
                })

    df_device = pd.DataFrame(records).drop_duplicates()

    df_device["ProStatus"] = "PROD"

    df_device["Carrier"] = df_device["deviceId"].apply(
        lambda x: "AIS" if str(x).startswith("A") else "TRUE"
    )

    # join response
    df_device = pd.merge(
        df_device,
        df_linkage[["Request ID", "Response"]],
        on="Request ID",
        how="left"
    )

    # 🔥 Quantity vs BYC
    df_device["Quantity"] = df_device["Response"].apply(extract_quantity)

    df_device["BYC_Count"] = df_device.groupby("Request ID")["deviceId"].transform("count")

    df_device["DTENLinkage Result"] = df_device.apply(
        lambda row: "✅ Match"
        if row["Quantity"] == row["BYC_Count"]
        else f"❌ Not Match ({row['BYC_Count']}/{row['Quantity']})",
        axis=1
    )

    df_device = df_device.reset_index(drop=True)
    df_device["No."] = df_device.index + 1

    return df_device[[
        "No.",
        "Request ID",
        "deviceId",
        "ProStatus",
        "Carrier",
        "DTENLinkage Result"
    ]]

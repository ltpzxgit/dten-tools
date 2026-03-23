import pandas as pd
import re

# =========================
# CONFIG
# =========================
input_file = "input.csv"
output_file = "output_sorted.csv"

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(input_file)

# =========================
# FIND COLUMNS
# =========================
columns = df.columns.tolist()

datetime_cols = [c for c in columns if "time" in c.lower() or "date" in c.lower()]

info_cols = [c for c in columns if "info" in c.lower()]
debug_cols = [c for c in columns if "debug" in c.lower()]

# =========================
# EXTRACT ID FROM COLUMN NAME
# เช่น info_123 → 123
# =========================
def extract_id(col):
    match = re.search(r'(\d+)', col)
    return int(match.group(1)) if match else float('inf')

# =========================
# GROUP PAIRS
# =========================
pairs = []

for info in info_cols:
    info_id = extract_id(info)

    # หา debug ที่ id เดียวกัน
    matched_debug = None
    for debug in debug_cols:
        if extract_id(debug) == info_id:
            matched_debug = debug
            break

    pairs.append((info_id, info, matched_debug))

# =========================
# SORT BY ID
# =========================
pairs_sorted = sorted(pairs, key=lambda x: x[0])

# =========================
# BUILD NEW COLUMN ORDER
# =========================
new_columns = []

# datetime มาก่อน
new_columns.extend(datetime_cols)

# ตามด้วย info + debug เป็นคู่
for _, info, debug in pairs_sorted:
    if info:
        new_columns.append(info)
    if debug:
        new_columns.append(debug)

# =========================
# FILTER ONLY EXISTING COLS
# =========================
new_columns = [c for c in new_columns if c in df.columns]

df_new = df[new_columns]

# =========================
# SAVE
# =========================
df_new.to_csv(output_file, index=False)

print("✅ Done! Saved to:", output_file)

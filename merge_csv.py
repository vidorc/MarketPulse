import pandas as pd
import glob

# ==========================================
# FIND ALL RESULTS CSV
# ==========================================

csv_files = glob.glob("results*.csv")

print("📂 TOTAL FILES:", len(csv_files))

all_data = []

# ==========================================
# READ ALL FILES
# ==========================================

for file in csv_files:

    try:

        print("📄 READING:", file)

        df = pd.read_csv(file)

        all_data.append(df)

    except Exception as e:

        print("❌ ERROR:", file, e)

# ==========================================
# MERGE
# ==========================================

merged_df = pd.concat(
    all_data,
    ignore_index=True
)

# ==========================================
# SAVE
# ==========================================

merged_df.to_csv(
    "merged_results.csv",
    index=False
)

print("✅ MERGED CSV CREATED")
print("📊 TOTAL ROWS:", len(merged_df))
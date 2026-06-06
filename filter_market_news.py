import pandas as pd

print("🚀 SCRIPT STARTED")

# ==========================================
# LOAD CSV
# ==========================================

print("📂 Reading merged_results.csv")

df = pd.read_csv("merged_results.csv")

print("✅ CSV LOADED")

print("📊 TOTAL ROWS:", len(df))

print("📊 COLUMNS:", df.columns.tolist())

# ==========================================
# FILTER
# ==========================================

filtered = df[
    df["classification"] == "Market-Moving"
]

print("📊 MARKET MOVING:", len(filtered))

# ==========================================
# SAVE
# ==========================================

filtered.to_csv(
    "market_moving_news.csv",
    index=False
)

print("✅ SAVED market_moving_news.csv")
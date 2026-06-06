import pandas as pd

url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"

df = pd.read_csv(url)

df.to_csv("nse_companies.csv", index=False)

print("✅ NSE company list downloaded")
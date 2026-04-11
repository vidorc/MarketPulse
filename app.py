import pandas as pd
import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

from prompt import create_prompt

# -----------------------------
# Load API key
# -----------------------------

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY not found in .env file"
    )

client = OpenAI(api_key=api_key)

# -----------------------------
# Load CSV file
# -----------------------------

file_name = "moneycontrol_100.csv"

print("\nLoading dataset...")

df = pd.read_csv(file_name)

print("Dataset loaded successfully")

print("\nColumns found:")
print(df.columns)

# -----------------------------
# Detect text column
# -----------------------------

possible_columns = [
    "article",
    "content",
    "text",
    "news",
    "headline",
    "title",
    "body",
    "Description"
]

text_column = None

for col in possible_columns:
    if col in df.columns:
        text_column = col
        break

if text_column is None:
    text_column = df.columns[0]

print("\nUsing column:", text_column)

# -----------------------------
# Classification
# -----------------------------

results = []

print("\nStarting classification...\n")

for i, article in tqdm(
    enumerate(df[text_column]),
    total=len(df)
):

    try:

        article = str(article)[:1500]

        prompt = create_prompt(article)

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        output = response.choices[0].message.content

    except Exception as e:

        print("Error on row", i, ":", e)

        output = "Label: Error"

    results.append(output)

    time.sleep(0.2)

# -----------------------------
# Save classification results
# -----------------------------

df["classification"] = results

df.to_csv("results.csv", index=False)

print("\nResults saved to results.csv")

# -----------------------------
# Extract label
# -----------------------------

def extract_label(text):

    if not isinstance(text, str):
        return "Error"

    if "Non-Market-Moving" in text:
        return "Non-Market-Moving"

    if "Market-Moving" in text:
        return "Market-Moving"

    return "Error"


df["label"] = df["classification"].apply(extract_label)

df.to_csv("results.csv", index=False)

print("\nLabel column created successfully")

# -----------------------------
# Generate statistics
# -----------------------------

print("\n----- FINAL STATISTICS -----\n")

total = len(df)

market_count = (df["label"] == "Market-Moving").sum()

non_market_count = (
    df["label"] == "Non-Market-Moving"
).sum()

error_count = (df["label"] == "Error").sum()

print("Total Articles:", total)

print("Market-Moving:", market_count)

print("Non-Market-Moving:", non_market_count)

print("Errors:", error_count)

print(
    "Market-Moving Percentage:",
    round((market_count / total) * 100, 2),
    "%"
)

print(
    "Non-Market-Moving Percentage:",
    round((non_market_count / total) * 100, 2),
    "%"
)

print(
    "Error Percentage:",
    round((error_count / total) * 100, 2),
    "%"
)
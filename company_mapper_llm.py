import os
import sys
import json
import time
import logging
import pandas as pd
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# 🎯 NEW: Import the modern Google GenAI SDK
from google import genai
from google.genai import types

# =====================================================================
# MODULE 1 — CONFIGURATION & SETUP
# =====================================================================
CONFIG = {
    "INPUT_FILE": "market_moving_news.csv",
    "COMPANY_FILE": "nse_companies.csv",
    "OUTPUT_FILE": "mapped_results.csv",
    "DEBUG_FILE": "pipeline_debug.jsonl",  
    "GROUND_TRUTH_FILE": "ground_truth.csv",
    "BENCHMARK_BREAKDOWN_FILE": "benchmark_breakdown.csv",
    "CHECKPOINT_FILE": "checkpoint.json",
    
    # 🎯 UPDATED: Using the latest supported Gemini 2.5 Flash model
    "MODEL": "gemini-2.5-flash",  
    "PROMPT_VERSION": "v12_few_shot_gemini_new_sdk",    
    
    "BATCH_SIZE": 10,                 
    "MAX_RETRIES": 5,
    "MAX_CHARS": 4000, 
    "RESET_OUTPUT_ON_COLD_START": True
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
load_dotenv()

# 🎯 Initialize the new Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY missing from .env file.")

client = genai.Client(api_key=api_key)

# =====================================================================
# MODULE 2 — UNIVERSE LOADER
# =====================================================================
def load_nse_universe() -> Tuple[Dict[str, str], str]:
    df = pd.read_csv(CONFIG["COMPANY_FILE"], low_memory=False).dropna(subset=["NAME OF COMPANY", "SYMBOL"])
    
    if df.empty:
        raise ValueError("FATAL: NSE universe is empty. Check COMPANY_FILE.")
    
    ticker_lookup = {str(row["NAME OF COMPANY"]).strip(): str(row["SYMBOL"]).strip() for _, row in df.iterrows()}
    company_block = "\n".join(ticker_lookup.keys())
    
    universe_chars = len(company_block)
    approx_tokens = universe_chars // 4
    logging.info(f"Loaded {len(ticker_lookup)} companies.")
    logging.info(f"Universe Block Size: {universe_chars:,} characters (approx {approx_tokens:,} tokens)")
    
    return ticker_lookup, company_block

# =====================================================================
# MODULE 3 — PROMPT BUILDER
# =====================================================================
def build_prompt(title: str, article: str, company_block: str) -> str:
    return f"""
You are an expert Indian equity research analyst.
You are given:
An article title.
An article body.
The complete NSE company universe.

Your task is to identify ONLY the materially relevant NSE-listed companies discussed in the article.

ARTICLE TITLE
=============
{title}

ARTICLE BODY
============
{article}

NSE COMPANY UNIVERSE
====================
{company_block}

REASONING PROCESS (MANDATORY)
Step 1: Identify all companies explicitly mentioned in the title or article body.
Step 2: For each mentioned company, determine whether it is materially relevant.
A company is materially relevant if ANY of the following are discussed:
• Quarterly or annual earnings/results
• Revenue, profit, margins, guidance
• Business operations or strategy
• Acquisitions, mergers, investments
• New projects, contracts, orders
• Capacity expansion
• Regulatory developments affecting the company
• Fund raising, stake sale, promoter activity
• Significant management commentary
• Major company-specific developments
• The company is the primary subject of the article

Step 3: Assign each company a confidence level (HIGH, MEDIUM, LOW).
- HIGH: Article is primarily about the company.
- MEDIUM: Company has material discussion but is not the main subject.
- LOW: Mentioned in passing, peer comparison, market roundup, stock movers list, analyst example, sector commentary.

Step 4 (Final Verification): For every company marked HIGH or MEDIUM, ask:
"Would removing this company materially change the meaning of the article?"
If NO: Downgrade to LOW.
If YES: Keep as HIGH/MEDIUM.

Step 5: Match the relevant companies against the provided NSE universe.

IMPORTANT RULES
- A company MUST be explicitly mentioned.
- Give highest weight to companies appearing in the title.
- For market commentary, market wrap, market mood, technical analysis, index movement, F&O, Nifty, Sensex, Mid-day Mood, Taking Stock, Opening Bell, Closing Bell, or market summary articles: DO NOT return companies merely because they are mentioned. Return them ONLY if company-specific earnings, guidance, business developments, management commentary, or corporate actions are discussed.
- Do NOT infer companies from sectors, themes, or macro commentary.
- Return ONLY exact names that exist in the provided NSE universe.

EXAMPLES
Example 1 (Earnings)
Title: REC Q4 results: Net profit climbs 33%
Article: REC reported net profit of Rs 4,079 crore...
Output:
{{
  "candidates": [
    {{"company": "REC Limited", "relevance": "HIGH"}}
  ]
}}

Example 2 (Market Wrap - Negative Example)
Title: Mid-day Mood | Nifty gains 200 points
Article: HDFC Bank, ICICI Bank, Reliance and Infosys supported the rally today amid strong global cues.
Output:
{{
  "candidates": []
}}

Example 3 (F&O Commentary - Negative Example)
Title: F&O Manual | Bank Nifty faces resistance
Article: Analysts discuss Nifty and Bank Nifty levels. HDFC Bank might see some pressure.
Output:
{{
  "candidates": [
    {{"company": "HDFC Bank Limited", "relevance": "LOW"}}
  ]
}}

Example 4 (Sector with one material standout)
Title: Q4 earnings: Positive surprises from banking majors
Article: ICICI Bank, Axis Bank, HDFC Bank and IndusInd Bank delivered strong results. ICICI specifically announced a major new acquisition.
Output:
{{
  "candidates": [
    {{"company": "ICICI Bank Limited", "relevance": "HIGH"}},
    {{"company": "Axis Bank Limited", "relevance": "MEDIUM"}},
    {{"company": "HDFC Bank Limited", "relevance": "MEDIUM"}},
    {{"company": "IndusInd Bank Limited", "relevance": "MEDIUM"}}
  ]
}}

OUTPUT FORMAT
Return ONLY valid JSON containing the "candidates" array.
"""

# =====================================================================
# MODULE 4 — PURE LLM EXTRACTOR
# =====================================================================
def extract_companies(title: str, article: str, company_block: str) -> Tuple[List[str], float, str, int, str]:
    article_text = str(article).strip()[:CONFIG["MAX_CHARS"]]
    prompt = build_prompt(title, article_text, company_block)
    
    prompt_size_chars = len(prompt)
    approx_tokens = prompt_size_chars // 4
    
    if approx_tokens > 30000:
        logging.warning(f"Large prompt detected ({approx_tokens:,} tokens)")
        
    logging.info(f"API Call Prep | Prompt chars={prompt_size_chars:,} | Approx tokens={approx_tokens:,}")
    
    for attempt in range(CONFIG["MAX_RETRIES"]):
        try:
            start_time = time.time()
            
            # 🎯 Generate content using the new SDK syntax
            response = client.models.generate_content(
                model=CONFIG["MODEL"],
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json"
                ),
            )
            
            latency = time.time() - start_time
            raw_text = response.text.strip()
            
            raw_json = raw_text
            if raw_json.startswith("```json"):
                raw_json = raw_json[7:-3].strip()
            elif raw_json.startswith("```"):
                raw_json = raw_json[3:-3].strip()
                
            parsed = json.loads(raw_json)
            
            # Filter strictly for HIGH and MEDIUM relevance
            valid_companies = []
            if isinstance(parsed, dict) and "candidates" in parsed:
                for candidate in parsed["candidates"]:
                    relevance = candidate.get("relevance", "").upper()
                    company_name = candidate.get("company", "")
                    
                    if relevance in ["HIGH", "MEDIUM"] and company_name:
                        valid_companies.append(company_name)
                        
                return valid_companies, latency, raw_text, prompt_size_chars, "SUCCESS"
            else:
                if "companies" in parsed:
                     return parsed["companies"], latency, raw_text, prompt_size_chars, "SUCCESS"
                raise ValueError("Malformed JSON output: missing 'candidates' array.")
            
        except Exception as e:
            logging.warning(f"API Error (Attempt {attempt+1}): {e}. Retrying in 15s...")
            time.sleep(15)
                
    return [], 0.0, "", prompt_size_chars, "FAILED"

# =====================================================================
# MODULE 5 — EXACT MAPPING LAYER
# =====================================================================
def map_tickers(extracted_companies: List[str], ticker_lookup: Dict[str, str]) -> Tuple[List[str], List[str], List[str]]:
    mapped_names, mapped_tickers, discarded = [], [], []
    
    cleaned_companies = []
    for c in extracted_companies:
        if isinstance(c, str) and c.strip():
            clean_c = c.strip()
            if clean_c not in cleaned_companies:
                cleaned_companies.append(clean_c)
    
    for company in cleaned_companies:
        if company in ticker_lookup:
            mapped_names.append(company)
            mapped_tickers.append(ticker_lookup[company])
        else:
            discarded.append(company)
            
    return mapped_names, mapped_tickers, discarded

# =====================================================================
# MODULE 6 — BENCHMARK EVALUATION (P/R/F1)
# =====================================================================
def run_benchmark_scoring():
    if not os.path.exists(CONFIG["GROUND_TRUTH_FILE"]) or not os.path.exists(CONFIG["OUTPUT_FILE"]):
        logging.info("Benchmark files missing. Skipping evaluation.")
        return

    try:
        res_df = pd.read_csv(CONFIG["OUTPUT_FILE"])
        tru_df = pd.read_csv(CONFIG["GROUND_TRUTH_FILE"])
        
        eval_df = pd.merge(res_df, tru_df, on=["title", "date_published"], how="inner", suffixes=('_pred', '_true'))
        
        if eval_df.empty: 
            return

        total_tp, total_fp, total_fn = 0, 0, 0
        breakdown_rows = []

        for _, row in eval_df.iterrows():
            pred_t = {t.strip().upper() for t in str(row.get("mapped_tickers", "")).split(",") if t.strip() and t.strip().lower() != "nan"}
            true_t_str = str(row.get("mapped_tickers_true", "")).replace("|", ",")
            true_t = {t.strip().upper() for t in true_t_str.split(",") if t.strip() and t.strip().lower() != "nan"}
            
            tp_set = pred_t & true_t
            fp_set = pred_t - true_t
            fn_set = true_t - pred_t
            
            tp_count = len(tp_set)
            fp_count = len(fp_set)
            fn_count = len(fn_set)
            
            total_tp += tp_count
            total_fp += fp_count
            total_fn += fn_count
            
            breakdown_rows.append({
                "title": row["title"], "date_published": row["date_published"],
                "predicted": ",".join(pred_t), "actual": ",".join(true_t),
                "tp": tp_count, "fp": fp_count, "fn": fn_count,
                "tp_details": ",".join(tp_set), "fp_details": ",".join(fp_set), "fn_details": ",".join(fn_set)
            })
            
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        pd.DataFrame(breakdown_rows).to_csv(CONFIG["BENCHMARK_BREAKDOWN_FILE"], index=False)
        
        logging.info("=== BENCHMARK: PURE LLM ARCHITECTURE (GEMINI) ===")
        logging.info(f"Rows Evaluated: {len(eval_df)}")
        logging.info(f"Precision: {precision:.4f}")
        logging.info(f"Recall:    {recall:.4f}")
        logging.info(f"F1 Score:  {f1:.4f}")
        
    except Exception as e:
        logging.error(f"Benchmark failed: {e}")

# =====================================================================
# MODULE 7 — I/O HELPERS
# =====================================================================
def save_checkpoint(next_row: int):
    with open(CONFIG["CHECKPOINT_FILE"], "w") as f:
        json.dump({"next_row": next_row}, f)

def append_with_dedup(file_path: str, new_row_dict: dict, subset: list):
    new_df = pd.DataFrame([new_row_dict])
    if os.path.exists(file_path):
        try:
            existing_df = pd.read_csv(file_path, engine="python", on_bad_lines="skip")
            combined_df = pd.concat([existing_df, new_df])
            combined_df = combined_df.drop_duplicates(subset=subset, keep="last")
            combined_df.to_csv(file_path, index=False)
        except Exception as e:
            logging.error(f"Deduplication failed due to CSV read error, appending blindly: {e}")
            new_df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        new_df.to_csv(file_path, index=False)

# =====================================================================
# MODULE 8 — BATCH RUNNER
# =====================================================================
def process_batch():
    ticker_lookup, company_block = load_nse_universe()
    universe_size = len(ticker_lookup)
    
    df = pd.read_csv(CONFIG["INPUT_FILE"], low_memory=False).fillna("")
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    
    start_row = 0
    if os.path.exists(CONFIG["CHECKPOINT_FILE"]):
        try:
            with open(CONFIG["CHECKPOINT_FILE"], "r") as f:
                start_row = json.load(f).get("next_row", 0)
        except json.JSONDecodeError:
            start_row = 0

    if start_row == 0 and CONFIG["RESET_OUTPUT_ON_COLD_START"]:
        logging.info("Cold start detected. Purging historical run files.")
        for f in [CONFIG["OUTPUT_FILE"], CONFIG["DEBUG_FILE"], CONFIG["CHECKPOINT_FILE"], CONFIG["BENCHMARK_BREAKDOWN_FILE"]]:
            if os.path.exists(f):
                os.remove(f)

    end_row = min(start_row + CONFIG["BATCH_SIZE"], len(df))
    target_slice = df.iloc[start_row:end_row]
    
    for idx, row in target_slice.iterrows():
        title = str(row["title"])
        article = str(row["article_text"])
        date_published = row.get("date_published", "")
        
        extracted, latency, raw_json, prompt_size, status = extract_companies(title, article, company_block)
            
        mapped_names, mapped_tickers, discarded = map_tickers(extracted, ticker_lookup)
        
        try:
            safe_json = json.dumps(json.loads(raw_json)) if raw_json else ""
        except Exception as e:
            logging.warning(f"Row {idx} | JSON parse failed, falling back to string strip: {e}")
            safe_json = str(raw_json).replace("\n", " ").replace("\r", "")
            
        safe_article = str(article).replace("\n", " ").replace("\r", "")
        
        out_dict = {
            "row_id": idx, 
            "title": title, 
            "date_published": date_published,
            "article_text": safe_article,
            "raw_llm_output": safe_json,
            "mapped_companies": ",".join(mapped_names), 
            "mapped_tickers": ",".join(mapped_tickers),
            "company_count": len(mapped_tickers)
        }
        
        debug_dict = {
            "row_id": idx, "title": title, "date_published": date_published,
            "model": CONFIG["MODEL"], "prompt_version": CONFIG["PROMPT_VERSION"],
            "universe_companies": universe_size, "api_latency": f"{latency:.2f}",
            "prompt_size_chars": prompt_size, "article_chars": len(article),
            "raw_extracted": ",".join(extracted), "mapped_companies": ",".join(mapped_names),
            "mapped_tickers": ",".join(mapped_tickers), "discarded_entities": ",".join(discarded),
            "raw_llm_json": safe_json
        }
        
        append_with_dedup(CONFIG["OUTPUT_FILE"], out_dict, subset=["title", "date_published"])
        
        with open(CONFIG["DEBUG_FILE"], "a", encoding="utf-8") as f:
            f.write(json.dumps(debug_dict) + "\n")
            
        save_checkpoint(idx + 1)
        
        logging.info(f"Row {idx} processed | Mapped: {len(mapped_tickers)} | Discarded: {len(discarded)}")

    if (start_row + len(target_slice)) >= len(df):
        run_benchmark_scoring()

if __name__ == "__main__":
    process_batch()
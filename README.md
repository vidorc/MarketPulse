# 🚀 MarketPulse — LLM-Based Financial News Impact Classification

> **An intelligent prompt-driven system that determines whether financial news can move markets.**
> Built using modern LLM workflows, data processing, and prompt engineering.

---

## 🌟 Project Overview

**MarketPulse** is a smart financial news analysis system that reads real-world news articles and predicts whether the information is likely to **move financial markets**.

The system leverages a **Large Language Model (LLM)** with carefully designed prompts to simulate how analysts interpret market-impacting information.

This project demonstrates practical skills in:

* Prompt Engineering
* LLM Integration
* Data Processing with Python
* Real-world Financial Reasoning
* GitHub Project Deployment

---

## 🎯 Objective

The goal of this project is to build a system that can:

* 📂 Read financial news from a CSV dataset
* 🧠 Use an LLM prompt to analyze each article
* 🏷️ Classify articles into:

  * **Market-Moving**
  * **Non-Market-Moving**
* 📊 Generate statistics summarizing results
* 🔍 Demonstrate how prompt design affects predictions

---

## 📘 Key Definitions

### 🟢 Market-Moving News

News that introduces **new, unexpected, or impactful information** likely to influence financial markets.

**Key Characteristics:**

* New or surprising information
* Changes investor expectations
* Triggers trading decisions
* Impacts prices or sentiment

**Examples:**

* Interest rate changes
* Earnings surprises
* Mergers and acquisitions
* Government policy changes
* Major geopolitical events

---

### 🔵 Non-Market-Moving News

News that is informative but does **not significantly influence market behavior**.

**Key Characteristics:**

* Routine updates
* Expected information
* Low urgency
* Minimal trading impact

**Examples:**

* Routine company announcements
* Minor operational updates
* Analyst commentary
* General informational reports

---

## 🏗️ System Architecture

```
Financial News CSV
        ↓
Prompt Engineering
        ↓
Large Language Model (LLM)
        ↓
News Classification
        ↓
Statistics Generation
        ↓
Results Saved (results.csv)
```

---

## 🛠️ Technologies Used

* 🐍 Python
* 📊 Pandas
* 🤖 OpenAI API
* 🧠 Prompt Engineering
* 🗂️ CSV Data Processing
* 🔧 Git & GitHub

---

## 📁 Project Structure

```
MarketPulse — LLM-Based Financial News Impact Classification
│
├── app.py
├── prompt.py
├── moneycontrol_100.csv
├── results.csv
├── requirements.txt
├── .gitignore
├── .env
└── README.md
```

---

## 🧠 Prompt Design

The system uses a structured prompt to guide consistent classification decisions.

```
You are a financial market analyst.

Classify the following financial news article as:

Market-Moving
or
Non-Market-Moving

Market-Moving:
- New or unexpected financial information
- Likely to affect stock prices
- Triggers trading activity

Non-Market-Moving:
- Routine or expected information
- Informational but not urgent
- No major financial impact

Return ONLY:

Label: <Market-Moving or Non-Market-Moving>
Reason: <short explanation>
```

---

## ⚙️ How the System Works

1. Load the CSV dataset
2. Detect the text column automatically
3. Send each article to the LLM
4. Receive classification output
5. Save results to a new CSV file
6. Generate summary statistics

---

## 🚀 Installation Instructions

### Step 1 — Clone the Repository

```
git clone https://github.com/your-username/MarketPulse.git
cd MarketPulse
```

### Step 2 — Create Virtual Environment

```
python -m venv .venv
```

Activate environment:

```
.venv\\Scripts\\activate
```

### Step 3 — Install Dependencies

```
pip install -r requirements.txt
```

### Step 4 — Add API Key

Create a file named:

```
.env
```

Add:

```
OPENAI_API_KEY=your_api_key_here
```

---

## ▶️ Running the Application

```
python app.py
```

---

## 📊 Output

The system generates:

```
results.csv
```

Containing:

* Classification results
* Clean label column
* Summary statistics

Example structure:

```
Title | Description | classification | label
```

---

## 🧪 Example Classification

### Example — Market-Moving

**Article:**

Central bank increases interest rates unexpectedly.

**Prediction:**

Market-Moving

**Reason:**

Unexpected monetary policy change likely to influence markets.

---

### Example — Non-Market-Moving

**Article:**

Company announces opening of a new office location.

**Prediction:**

Non-Market-Moving

**Reason:**

Routine operational update with minimal financial impact.

---

## 📈 Statistics Generated

The system automatically calculates:

* Total Articles
* Market-Moving Count
* Non-Market-Moving Count
* Percentage Distribution

Example output:

```
Total Articles: 100
Market-Moving: 48
Non-Market-Moving: 52
Market-Moving Percentage: 48%
Non-Market-Moving Percentage: 52%
```

---

## 🧩 Prompt Sensitivity (Bonus Insight)

Different prompt designs can change model behavior.

### Weak Prompt

```
Classify the article.
```

Result:

* Inconsistent predictions
* Low reliability

---

### Improved Prompt

```
Classify based on whether the news introduces new financial information that can affect markets.
```

Result:

* Better consistency
* More accurate decisions

---

### Strict Prompt

```
If the information is routine or expected, classify as Non-Market-Moving.
```

Result:

* Reduced false positives
* Higher precision

---

## ⚠️ Challenges Faced

* Handling API response latency
* Managing environment configuration
* Fixing statistics calculation bugs
* Debugging runtime errors

---

## 🎓 Key Learning Outcomes

* Practical prompt engineering
* Integrating LLM APIs into Python apps
* Data processing with Pandas
* Generating analytical statistics
* Debugging real-world systems
* Using Git and GitHub professionally

---

## 🔮 Future Improvements

* Add confidence scores
* Implement batch processing
* Build Streamlit dashboard
* Add visual analytics
* Support local LLM models

---

## 👨‍💻 Author

**Mayank Sharma**

---

## 🏷️ Project Title

**MarketPulse — LLM-Based Financial News Impact Classification**

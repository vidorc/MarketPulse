# MarketPulse — LLM-Based Financial News Impact Classification

## Project Overview

**MarketPulse** is a prompt-driven application that analyzes financial news articles and classifies them based on their potential impact on financial markets. The system uses a Large Language Model (LLM) to determine whether a news article is likely to be **Market-Moving** or **Non-Market-Moving**.

This project demonstrates the use of **prompt engineering**, **LLM-based classification**, **data processing**, and **result analysis** to solve a real-world financial analytics problem.

---

## Objective

The objective of this project is to:

* Read financial news articles from a CSV dataset
* Use an LLM prompt mechanism to analyze each article
* Classify each article into one of two categories:

  * **Market-Moving**
  * **Non-Market-Moving**
* Generate statistics summarizing classification results
* Demonstrate how prompt design influences model predictions

---

## Definitions

### Market-Moving News

News that introduces new or unexpected information that can significantly influence financial markets.

**Key Characteristics:**

* New and unexpected information
* Changes financial expectations
* Triggers trading activity
* Likely to impact prices or market sentiment

**Examples:**

* Interest rate changes
* Earnings surprises
* Mergers and acquisitions
* Economic policy changes
* Major geopolitical events

---

### Non-Market-Moving News

News that provides information but does not significantly influence financial markets.

**Key Characteristics:**

* Routine or expected updates
* Informational but not urgent
* Minimal impact on trading decisions

**Examples:**

* Routine company announcements
* Minor operational updates
* Analyst commentary without new insights
* General informational reports

---

## System Architecture

```
CSV Dataset
     ↓
Prompt Engineering
     ↓
Large Language Model (LLM)
     ↓
Classification
     ↓
Statistics Generation
     ↓
Results Output (results.csv)
```

---

## Technologies Used

* Python
* Pandas
* OpenAI API
* Prompt Engineering
* CSV Data Processing
* Git & GitHub

---

## Project Structure

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

## Prompt Design

The system uses a structured prompt to guide the LLM in making consistent classification decisions.

### Prompt Used

```
You are a financial market analyst.

Your task is to classify the following financial news article as:

Market-Moving
or
Non-Market-Moving

Definitions:

Market-Moving:
- New or unexpected financial information
- Likely to affect stock prices or markets
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

## How the System Works

1. Load the CSV dataset containing financial news articles
2. Detect the column containing article text
3. Send each article to the LLM using the designed prompt
4. Receive classification output
5. Store results in a new CSV file
6. Generate summary statistics

---

## Installation Instructions

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
.venv\Scripts\activate
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

## Running the Application

```
python app.py
```

---

## Output Files

### results.csv

Contains the classification results for each article.

Example structure:

```
Title | Description | classification | label
```

---

## Example Classification Results

### Example — Market-Moving

Article:

"Central bank increases interest rates unexpectedly."

Classification:

Market-Moving

Reason:

Unexpected monetary policy change likely to influence financial markets.

---

### Example — Non-Market-Moving

Article:

"Company announces opening of a new office location."

Classification:

Non-Market-Moving

Reason:

Routine operational update with minimal financial impact.

---

## Statistics Generation

The system calculates:

* Total number of articles
* Number of Market-Moving articles
* Number of Non-Market-Moving articles
* Percentage distribution

### Example Output

```
Total Articles: 100
Market-Moving: 48
Non-Market-Moving: 52
Market-Moving Percentage: 48%
Non-Market-Moving Percentage: 52%
```

---

## Prompt Sensitivity Analysis (Bonus Requirement)

The classification results can vary depending on how the prompt is designed.

### Simple Prompt

```
Classify the article.
```

**Impact:**

* Inconsistent predictions
* Lack of clear decision criteria

---

### Improved Prompt

```
Classify based on whether the news introduces new financial information that can affect markets.
```

**Impact:**

* More consistent classification
* Better alignment with financial impact criteria

---

### Strict Prompt

```
If the information is routine or expected, classify as Non-Market-Moving.
```

**Impact:**

* Reduced false positives
* Improved classification precision

---

## Challenges Faced

* Handling API response delays
* Managing environment configuration
* Ensuring correct dataset processing
* Avoiding incorrect statistics calculations

---

## Key Learning Outcomes

* Prompt engineering for classification tasks
* Integrating LLM APIs into Python applications
* Data processing using Pandas
* Generating analytical statistics
* Debugging runtime and environment issues
* Version control using Git and GitHub

---

## Future Improvements

* Add confidence scores for predictions
* Implement batch processing for faster execution
* Build a web interface using Streamlit
* Add visualization dashboards
* Use local LLM models for offline execution

---

## Author

Mayank Sharma

---

## Project Title

**MarketPulse — LLM-Based Financial News Impact Classification**

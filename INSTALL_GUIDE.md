# Installation & Setup Guide: Amazon Review Insight Pro Analyzer

This guide walks you through setting up and running **Amazon Review Insight Pro Analyzer** on Windows, macOS, or Linux.

---

## 📋 System Prerequisites

- **Python 3.10+** (Python 3.10, 3.11, 3.12, or 3.13)
- **pip** (Python package installer)
- Git (optional, for cloning)

Verify your Python installation:
```bash
python --version
```

---

## 🛠️ Step-by-Step Installation

### Step 1: Open the Project Directory
Navigate into the application folder:
```bash
cd "Amazon Review Insight Pro"
```

### Step 2: Set Up Virtual Environment
Creating an isolated virtual environment is recommended to avoid dependency conflicts.

**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
Install all platform dependencies via pip:
```bash
pip install -r requirements.txt
```

*(Includes: `streamlit`, `pandas`, `textblob`, `spacy`, `plotly`, `requests`, `beautifulsoup4`, `openpyxl`)*

### Step 4: Optional NLP Language Model
To enable advanced entity and noun/adjective tokenization:
```bash
python -m spacy download en_core_web_sm
```
*(If omitted, the platform gracefully uses built-in lightweight NLP processing).*

---

## 🚀 Running the Application

Start the server using Streamlit:
```bash
streamlit run app.py
```

On Windows, you can also double-click `start.bat`.

The application will initialize its database automatically on first launch and open in your default browser.

---

## 🧪 Verifying the Installation

Execute the comprehensive test suite to confirm all modules (authentication, data isolation, sentiment, suspicion rules, and file parsers) are working properly:

```bash
python -u tests/test_core.py
```

Expected output:
```
============================================================
Amazon Review Insight Pro Analyzer - Test Verification Suite
============================================================
[TEST] Password Security & User Authentication...
 [PASS] Password Security & User Authentication
[TEST] User Data Isolation (Account Privacy)...
 [PASS] User Data Isolation (Account Privacy)
[TEST] Sentiment Analysis Service...
 [PASS] Sentiment Analysis Service
[TEST] 7 Heuristic Suspicion Rules...
 [PASS] 7 Heuristic Suspicion Rules
[TEST] File Upload & Data Processor...
 [PASS] File Upload & Data Processor
[TEST] Amazon URL Parser & Product Link Generator...
 [PASS] Amazon URL Parser & Product Link Generator
============================================================
[SUCCESS] ALL TESTS COMPLETED SUCCESSFULLY!
============================================================
```

---

## ❓ Troubleshooting

### Database Access Issues
- The SQLite database file is automatically created at `data/reviews.db` with Write-Ahead Logging (WAL) enabled for concurrent safety.
- Ensure the user account running the application has read/write permissions to the `data/` folder.

### File Upload Column Warnings
- When uploading datasets, ensure the column containing customer review text is named `review_text` (or common variants like `review`, `comment`, or `text`).
- Star ratings should be in the range of 1.0 to 5.0.

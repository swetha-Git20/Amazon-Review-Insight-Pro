# 🛡️ Amazon Review Insight Pro Analyzer

A professional web application platform engineered to analyze consumer reviews, evaluate multi-dimensional sentiment polarity, and verify review authenticity using a 7-factor heuristic detection framework.

---

## ✨ Core Capabilities & Features

1. **Secure Multi-User Authentication & Data Privacy**
   - Individual user registration and sign-in portal.
   - Secure cryptographic password hashing using **PBKDF2-HMAC-SHA256** with 100,000 iterations and unique cryptographic salts.
   - **Strict Data Isolation**: Each user has a completely segregated workspace, reviews dataset, product list, and analysis history. Users can never access or view another user's data.

2. **Dataset File Upload & Validation**
   - Support for **CSV** (`.csv`) and **Excel** (`.xlsx`, `.xls`) formats.
   - Smart column alias auto-mapping (automatically detects variations like `review`, `comment`, `text`, `stars`, `rating`, `product`).
   - Interactive data previews with row counters and column inspection.
   - Informative, actionable validation error banners and data cleaning.

3. **Amazon Product URL Analysis & Direct Storefront Linking**
   - Universal Amazon URL parser supporting international domains (`.com`, `.in`, `.co.uk`, `.de`, etc.) and canonical ASIN extraction.
   - Curated demo products with immediate evaluation capability.
   - Direct **"View Product on Amazon"** external links opening the exact product listing in a new browser tab.
   - **Strict Authenticity Guarantee**: Never shows mock, fabricated, or simulated fake reviews. When Amazon anti-bot systems restrict automated scraping, it reports honestly and guides the user to import genuine reviews via CSV.

4. **Multi-Factor Heuristic Suspicion Framework**
   Evaluates each review against 7 independent linguistic and structural heuristics:
   - Very short reviews (< 5 words)
   - Excessive repeated words (30%+ token dominance)
   - Excessive capitalization (> 50% uppercase letters)
   - Excessive exclamation marks (3+ exclamation marks)
   - Repeated promotional trigger phrases
   - Hyperbolic extreme language
   - Corpus duplicate & high text similarity (85%+ ratio)
   - **Classification**: 0-2 triggers = `Genuine-looking`; 3+ triggers = `Suspicious`.

5. **Premium Responsive Dark Dashboard & Analytics**
   - Sleek dark theme interface styled with Google Fonts **Poppins**.
   - Metric cards: Total Reviews, Average Rating, Positive/Negative/Neutral counts, Authenticity Ratio.
   - Dark-mode Plotly charts: Sentiment Donut, Rating Breakdown, Genuine vs Suspicious Proportion, Suspicion Score Distribution.
   - NLP keyword extraction for positive praise and negative complaints (powered by spaCy).

6. **Comprehensive Export Suite**
   - Export analyzed datasets as **CSV**.
   - Export analysis summaries and metrics as structured **JSON**.
   - Export executive evaluation reports as formatted **Markdown**.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| Framework | Streamlit (>= 1.28.0) | Interactive reactive web application |
| Language | Python 3.10+ | Core language engine |
| Typography | Google Fonts Poppins | Modern, legible typography across all UI |
| Database | SQLite 3 (WAL mode) | Isolated relational user storage with foreign keys |
| Password Security | hashlib (PBKDF2-HMAC-SHA256) | NIST-approved credential protection |
| Data Processing | Pandas & openpyxl | CSV & Excel parsing, validation, and cleaning |
| Sentiment Analysis | TextBlob | Polarity (-1.0 to +1.0) and subjectivity scoring |
| NLP & Linguistics | spaCy | Linguistic tokenization and keyword extraction |
| Visualizations | Plotly Express & Graph Objects | Dark-themed interactive visualizations |
| Web Scraping | Requests & BeautifulSoup4 | Live Amazon product detail extraction |

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 or higher installed
- pip (Python package manager)

### 1. Clone or Open the Repository
```bash
cd "Amazon Review Insight Pro"
```

### 2. Create and Activate Virtual Environment
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

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Optional: Download spaCy Language Model
```bash
python -m spacy download en_core_web_sm
```
*(The application automatically operates in lightweight fallback mode if this step is skipped).*

---

## 🏃 Running the Application

Launch the application with:
```bash
streamlit run app.py
```
Or execute `start.bat` on Windows. The application will launch and open automatically in your web browser.

---

## 🧪 Testing & Verification

Run the full automated test suite covering authentication, user data isolation, sentiment analysis, heuristic rules, file upload processing, and Amazon URL parsing:

```bash
python -u tests/test_core.py
```

All tests execute in clean UTF-8 mode and report status for each subsystem.

---

## 🚢 Preparing for Deployment

The application is structured for simple production deployment:

### Deployment on Streamlit Community Cloud
1. Push this repository to GitHub.
2. Link the repository in [Streamlit Cloud](https://share.streamlit.io/).
3. Set the Main file path to `app.py`.
4. Deploy. All dependencies in `requirements.txt` will be installed automatically.

### Deployment via Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## 📄 License & Notes
Amazon Review Insight Pro Analyzer is developed for research, education, and consumer sentiment intelligence. Suspicious review classifications are heuristic indicators and do not constitute legal proof of review manipulation.

# 🚀 Amazon Review Insight Pro

## 📌 About the Project

Amazon Review Insight Pro is a web application that analyzes product reviews to understand customer sentiment and identify suspicious review patterns. It helps users make informed purchasing decisions by detecting potentially fake or manipulated reviews while understanding genuine customer feedback.

## ✨ Features

- **Dashboard**: Overview metrics with interactive charts for sentiment distribution, rating distribution, and authenticity analysis
- **Review Analyzer**: Analyze individual reviews or batch process CSV files with sentiment and pattern detection
- **Review Data Management**: Browse, filter, search, and manage stored reviews with export functionality
- **Advanced Analytics**: Keyword extraction, polarity analysis, and trend insights
- **Amazon URL Fetcher**: Attempt to fetch reviews directly from Amazon product pages (with CSV fallback)

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| Python | Core programming language |
| Streamlit | Web application framework |
| Pandas | Data manipulation and analysis |
| TextBlob | Sentiment analysis |
| spaCy | Natural language processing for keyword extraction |
| Plotly | Interactive data visualization |
| SQLite | Built-in database for data persistence |
| Requests & BeautifulSoup | Web scraping for Amazon reviews |

## 🔄 How It Works

```
Input Review Data (CSV/Manual/URL)
    ↓
Data Cleaning & Validation
    ↓
NLP Processing (TextBlob & spaCy)
    ↓
Sentiment Analysis (Polarity & Subjectivity)
    ↓
Review Pattern Analysis (7 Heuristic Rules)
    ↓
Store Results in SQLite Database
    ↓
Display Insights & Visualizations
```

## 📊 Main Analysis

### Sentiment Analysis
- Uses TextBlob to calculate polarity (-1 to +1) and subjectivity (0 to 1)
- Classifies reviews as Positive, Negative, or Neutral based on polarity scores
- Provides numerical sentiment scores for detailed analysis

### Classification
- **Positive**: Polarity > 0
- **Negative**: Polarity < 0  
- **Neutral**: Polarity = 0

### Review Statistics
- Total reviews count and average rating
- Sentiment distribution percentages
- Subjectivity analysis for objectivity vs. opinion

### Suspicious Review Pattern Analysis
- Applies 7 rule-based heuristics to detect suspicious patterns:
  1. Very short reviews (fewer than 5 words)
  2. Excessive repeated words (30%+ same word)
  3. Excessive capital letters (50%+ uppercase)
  4. Too many exclamation marks (3+)
  5. Repeated promotional phrases
  6. Very extreme language
  7. Duplicate or highly similar text
- Classification: 0-2 indicators = "Genuine-looking", 3+ = "Suspicious"

**Note**: This is a heuristic analysis for educational purposes and does not guarantee fake review detection.

### Charts and Visualizations
- Sentiment distribution pie chart
- Rating distribution bar chart
- Genuine vs Suspicious comparison
- Rating vs Sentiment correlation matrix
- Polarity and suspicion score histograms
- Keyword frequency analysis

## 📁 Project Structure

```
amazon-review-insight-pro/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
├── INSTALL_GUIDE.md                # Installation instructions
├── .streamlit/
│   └── config.toml                # Streamlit theme configuration
├── data/
│   ├── sample_reviews.csv         # Sample data for testing
│   └── reviews.db                 # SQLite database (auto-created)
├── database/
│   ├── __init__.py
│   └── database.py                # Database operations
├── services/
│   ├── __init__.py
│   ├── sentiment.py               # Sentiment analysis
│   ├── review_analyzer.py         # Suspicion detection rules
│   ├── data_processor.py          # CSV processing and cleaning
│   └── review_fetcher.py          # Amazon URL fetcher
├── utils/
│   ├── __init__.py
│   └── helpers.py                 # UI components and helpers
└── tests/
    ├── __init__.py
    └── test_core.py               # Unit tests
```

## ⚙️ Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)

### Steps

1. **Navigate to project directory**
   ```bash
   cd "C:\Users\laksh\Music\Amazon Review Insight Pro"
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv venv
   
   # Mac/Linux
   python3 -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install spaCy model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

The application will open automatically at `http://localhost:8501`

## 🚀 Usage

1. **Open the Application**: Launch the Streamlit app using the command above
2. **Upload Data**: Go to "Review Analyzer" and upload a CSV file with reviews or enter a single review manually
3. **Analyze**: Click "Analyze Reviews" to process the data through sentiment and pattern analysis
4. **View Results**: Check the "Dashboard" for overview metrics and charts
5. **Explore Analytics**: Visit the "Analytics" page for detailed insights and keyword analysis
6. **Manage Data**: Use "Review Data" to filter, search, and manage your review database

## ⚠️ Limitations

- **Rule-based approach**: May produce false positives/negatives; not based on machine learning
- **Amazon scraping**: Often blocked by anti-bot measures; CSV upload is recommended
- **Language support**: Optimized for English reviews only
- **Context unaware**: Doesn't understand product-specific context or sarcasm
- **Not legal proof**: Analysis is for educational purposes only
- **50 review limit**: Performance constraint for batch processing
- **spaCy dependency**: Keyword extraction requires spaCy model; other features work without it

## 🔮 Future Enhancements

- Machine learning models for improved accuracy
- Multi-language support for global reviews
- User authentication and data privacy features
- Real-time review monitoring from multiple platforms
- Advanced visualization options and export formats
- Integration with additional e-commerce platforms

## 📄 License

This project is created for educational purposes as a college project.

---

**Note**: This is a college project for educational purposes. The suspicious review detection is based on simple heuristics and should not be used as definitive proof of fake reviews.

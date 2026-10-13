"""
Data processor service for Amazon Review Insight Pro Analyzer
Handles file parsing (CSV/Excel), column auto-mapping, data validation,
text cleaning, and batch NLP processing.
"""

import pandas as pd
import re
import io
from typing import Dict, List, Tuple, Optional


# Standard expected columns
REQUIRED_COLUMNS = ['review_text']
RECOMMENDED_COLUMNS = ['rating', 'product_name']

# Column aliases for flexible user upload experience
COLUMN_ALIASES = {
    'review_text': ['review_text', 'review', 'text', 'content', 'review_body', 'comment', 'feedback', 'reviews'],
    'rating': ['rating', 'score', 'stars', 'star_rating', 'user_rating', 'overall_rating'],
    'product_name': ['product_name', 'product', 'title', 'item_name', 'product_title', 'asin_title']
}

# Maximum reviews analyzed per batch
MAX_REVIEWS = 100


def map_column_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Automatically map common column name variations to standard names.
    
    Why: Improves UX by accepting files exported from various scrapers or tools.
    """
    df_mapped = df.copy()
    lower_to_orig = {col.lower().strip().replace(' ', '_'): col for col in df_mapped.columns}
    
    rename_dict = {}
    for standard_col, aliases in COLUMN_ALIASES.items():
        if standard_col not in df_mapped.columns:
            for alias in aliases:
                if alias in lower_to_orig:
                    orig_col = lower_to_orig[alias]
                    rename_dict[orig_col] = standard_col
                    break
    
    if rename_dict:
        df_mapped = df_mapped.rename(columns=rename_dict)
    
    return df_mapped


def parse_uploaded_file(uploaded_file) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
    Parse uploaded file (CSV or Excel) into a pandas DataFrame.
    Supports UTF-8, Latin-1, CP1252 encodings.
    """
    if uploaded_file is None:
        return False, "No file was uploaded.", None
    
    filename = uploaded_file.name.lower()
    
    try:
        if filename.endswith('.csv'):
            bytes_data = uploaded_file.getvalue()
            # Try multiple encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            df = None
            last_err = None
            
            for enc in encodings:
                try:
                    df = pd.read_csv(io.BytesIO(bytes_data), encoding=enc)
                    break
                except Exception as e:
                    last_err = e
            
            if df is None:
                return False, f"Could not parse CSV file. Encoding error: {str(last_err)}", None
                
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            return False, "Unsupported file format. Please upload a .csv, .xlsx, or .xls file.", None
        
        if df.empty:
            return False, "The uploaded file is empty. Please upload a file containing review data.", None
        
        # Apply alias mapping
        df = map_column_aliases(df)
        return True, "File parsed successfully.", df
        
    except Exception as e:
        return False, f"Error reading file '{uploaded_file.name}': {str(e)}", None


def validate_csv(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate that DataFrame has required columns and at least one non-empty review.
    """
    if df is None or df.empty:
        return False, "Dataset is empty. Please upload a file with review data."
    
    df_mapped = map_column_aliases(df)
    
    if 'review_text' not in df_mapped.columns:
        cols_found = ", ".join([f"'{c}'" for c in df.columns])
        return (
            False,
            f"Missing required column 'review_text'. Found columns: {cols_found}. "
            "Please ensure your file has a column named 'review_text' or 'review'."
        )
    
    # Check if review_text has valid content
    text_series = df_mapped['review_text'].dropna().astype(str).str.strip()
    if text_series.empty or (text_series == '').all():
        return False, "The 'review_text' column contains only empty or missing values."
    
    return True, ""


def clean_text(text: str) -> str:
    """
    Clean review text: removes URLs, HTML tags, normalize whitespace,
    while preserving standard punctuation and semantics.
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove excessive repeated symbols
    text = re.sub(r'([!?.])\1{4,}', r'\1\1\1', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def clean_rating(rating) -> Optional[float]:
    """
    Validate and clamp rating to 1.0 - 5.0 range.
    """
    if pd.isna(rating):
        return None
    try:
        val = float(rating)
        if 1.0 <= val <= 5.0:
            return round(val, 1)
        elif 0.0 <= val <= 1.0:
            # Handle normalized 0-1 scale
            return round(val * 5.0, 1)
        elif 5.0 < val <= 10.0:
            # Handle 1-10 scale
            return round(val / 2.0, 1)
        return None
    except (ValueError, TypeError):
        return None


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize DataFrame.
    """
    df_clean = map_column_aliases(df)
    
    if 'product_name' not in df_clean.columns:
        df_clean['product_name'] = 'General Product'
    else:
        df_clean['product_name'] = df_clean['product_name'].fillna('General Product').astype(str).str.strip()
        df_clean['product_name'] = df_clean['product_name'].replace('', 'General Product')
    
    if 'rating' not in df_clean.columns:
        df_clean['rating'] = None
    else:
        df_clean['rating'] = df_clean['rating'].apply(clean_rating)
    
    # Clean review text
    df_clean['cleaned_text'] = df_clean['review_text'].apply(clean_text)
    
    # Filter out empty cleaned reviews
    df_clean = df_clean[df_clean['cleaned_text'].str.strip() != '']
    
    # Deduplicate exact duplicate reviews for the same product
    df_clean = df_clean.drop_duplicates(subset=['product_name', 'cleaned_text'])
    
    df_clean = df_clean.reset_index(drop=True)
    return df_clean


def limit_reviews(df: pd.DataFrame, max_limit: int = MAX_REVIEWS) -> Tuple[pd.DataFrame, bool]:
    """
    Limit review batch to max_limit to ensure fast NLP processing.
    """
    if len(df) > max_limit:
        return df.head(max_limit), True
    return df, False


def process_reviews_batch(df: pd.DataFrame, sentiment_analyzer, review_analyzer) -> List[Dict]:
    """
    Execute batch sentiment analysis and suspicion heuristic classification.
    """
    processed_reviews = []
    if df.empty:
        return processed_reviews
    
    cleaned_texts = df['cleaned_text'].tolist()
    
    for _, row in df.iterrows():
        text = row['cleaned_text']
        if not text:
            continue
        
        # Sentiment
        sentiment_res = sentiment_analyzer(text)
        
        # Suspicion score (cross-check against other reviews in batch for similarity)
        other_texts = [t for t in cleaned_texts if t != text]
        suspicion_res = review_analyzer(text, other_texts)
        
        processed_reviews.append({
            'product_name': str(row.get('product_name', 'General Product')),
            'review_text': str(row['review_text']),
            'rating': row['rating'],
            'sentiment': sentiment_res['sentiment'],
            'polarity': sentiment_res['polarity'],
            'subjectivity': sentiment_res['subjectivity'],
            'suspicion_score': suspicion_res['suspicion_score'],
            'classification': suspicion_res['classification']
        })
    
    return processed_reviews


def get_sample_csv_path() -> str:
    """Path to sample review dataset."""
    import os
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sample_reviews.csv')


def load_sample_csv() -> pd.DataFrame:
    """Load default sample review dataset."""
    try:
        path = get_sample_csv_path()
        return pd.read_csv(path)
    except Exception as e:
        print(f"Error loading sample CSV: {e}")
        return pd.DataFrame()

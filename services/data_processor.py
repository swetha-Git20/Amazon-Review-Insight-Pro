"""
Data processor service for Amazon Review Insight Pro
Handles CSV validation, data cleaning, and batch processing of reviews.
"""

import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
import sys


# Required columns for CSV
REQUIRED_COLUMNS = ['review_text', 'rating']
OPTIONAL_COLUMNS = ['product_name']

# Maximum reviews per analysis
MAX_REVIEWS = 50


def validate_csv(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate that CSV has required columns and data.
    
    Why: Ensure uploaded data meets minimum requirements before processing.
    
    Input: df (pd.DataFrame) - DataFrame from uploaded CSV
    
    Output: Tuple[bool, str] - (is_valid, error_message)
    """
    # Check if DataFrame is empty
    if df.empty:
        return False, "CSV file is empty. Please upload a file with data."
    
    # Check for required columns
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}. Required: {', '.join(REQUIRED_COLUMNS)}"
    
    # Check if review_text column has data
    if df['review_text'].isna().all() or (df['review_text'].str.strip() == '').all():
        return False, "Review text column is empty. Please ensure reviews have text."
    
    return True, ""


def clean_text(text: str) -> str:
    """
    Clean review text by removing URLs, HTML, extra symbols, and normalizing whitespace.
    
    Why: Standardize text for consistent analysis while preserving original for display.
    
    Input: text (str) - Raw review text
    
    Output: str - Cleaned text
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # Remove extra symbols (keep basic punctuation)
    text = re.sub(r'[^\w\s\.,!?;:\-\'"]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def clean_rating(rating) -> Optional[float]:
    """
    Clean and validate rating value.
    
    Why: Ensure rating is a valid number between 1 and 5.
    
    Input: rating - Raw rating value (any type)
    
    Output: Optional[float] - Validated rating or None if invalid
    """
    try:
        # Convert to float
        rating_float = float(rating)
        
        # Check if rating is in valid range
        if 1 <= rating_float <= 5:
            return rating_float
        else:
            return None
    except (ValueError, TypeError):
        return None


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the entire DataFrame.
    
    Why: Remove invalid data while preserving valid reviews for analysis.
    
    Input: df (pd.DataFrame) - Raw DataFrame
    
    Output: pd.DataFrame - Cleaned DataFrame
    """
    # Make a copy to avoid modifying original
    df_clean = df.copy()
    
    # Add product_name column if missing
    if 'product_name' not in df_clean.columns:
        df_clean['product_name'] = 'Unknown Product'
    
    # Clean review text (keep original for display, add cleaned column)
    df_clean['cleaned_text'] = df_clean['review_text'].apply(clean_text)
    
    # Clean rating
    df_clean['rating'] = df_clean['rating'].apply(clean_rating)
    
    # Drop rows with missing values in critical columns
    df_clean = df_clean.dropna(subset=['cleaned_text', 'rating'])
    
    # Drop rows with empty cleaned text
    df_clean = df_clean[df_clean['cleaned_text'].str.strip() != '']
    
    # Drop exact duplicate reviews (same product and text)
    df_clean = df_clean.drop_duplicates(subset=['product_name', 'review_text'])
    
    # Reset index
    df_clean = df_clean.reset_index(drop=True)
    
    return df_clean


def limit_reviews(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """
    Limit reviews to maximum allowed (50) and warn if exceeded.
    
    Why: Prevent performance issues with large datasets.
    
    Input: df (pd.DataFrame) - DataFrame to limit
    
    Output: Tuple[pd.DataFrame, bool] - (limited_df, was_limited)
    """
    if len(df) > MAX_REVIEWS:
        return df.head(MAX_REVIEWS), True
    return df, False


def process_reviews_batch(df: pd.DataFrame, sentiment_analyzer, review_analyzer) -> List[Dict]:
    """
    Process a batch of reviews with sentiment and suspicion analysis.
    
    Why: Apply NLP analysis to all reviews in a CSV upload.
    
    Input: df (pd.DataFrame) - Cleaned DataFrame
           sentiment_analyzer - Sentiment analysis function
           review_analyzer - Review analyzer function
    
    Output: List[Dict] - List of processed review dictionaries
    """
    processed_reviews = []
    
    # Get existing texts for duplicate check
    existing_texts = df['cleaned_text'].tolist()
    
    for _, row in df.iterrows():
        # Get text for analysis
        text = row['cleaned_text']
        
        # Skip if text is empty
        if not text or text.strip() == '':
            continue
        
        # Analyze sentiment
        sentiment_result = sentiment_analyzer(text)
        
        # Analyze suspicion (remove current text from existing for comparison)
        other_texts = [t for t in existing_texts if t != text]
        suspicion_result = review_analyzer(text, other_texts)
        
        # Build review dictionary
        review_data = {
            'product_name': row.get('product_name', 'Unknown Product'),
            'review_text': row['review_text'],  # Keep original text
            'rating': row['rating'],
            'sentiment': sentiment_result['sentiment'],
            'polarity': sentiment_result['polarity'],
            'subjectivity': sentiment_result['subjectivity'],
            'suspicion_score': suspicion_result['suspicion_score'],
            'classification': suspicion_result['classification']
        }
        
        processed_reviews.append(review_data)
    
    return processed_reviews


def get_sample_csv_path() -> str:
    """
    Get the path to the sample CSV file.
    
    Why: Provide easy access to sample data for testing.
    
    Input: None
    
    Output: str - Path to sample CSV file
    """
    import os
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sample_reviews.csv')


def load_sample_csv() -> pd.DataFrame:
    """
    Load the sample CSV file.
    
    Why: Provide default data for testing and demonstration.
    
    Input: None
    
    Output: pd.DataFrame - Sample reviews DataFrame
    """
    try:
        sample_path = get_sample_csv_path()
        return pd.read_csv(sample_path)
    except Exception as e:
        print(f"Error loading sample CSV: {e}")
        return pd.DataFrame()

"""
Sentiment analysis service for Amazon Review Insight Pro
Uses TextBlob to analyze sentiment and subjectivity of review text.
"""

from textblob import TextBlob
from typing import Dict


def analyze_sentiment(text: str) -> Dict:
    """
    Analyze the sentiment of a given text using TextBlob.
    
    Why: Determine if a review is positive, negative, or neutral based on polarity.
    
    Input: text (str) - The review text to analyze
    
    Output: Dict - Dictionary containing sentiment, polarity, and subjectivity
    """
    try:
        # Create TextBlob object
        blob = TextBlob(text)
        
        # Get polarity (-1 to 1) and subjectivity (0 to 1)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Classify sentiment based on polarity
        if polarity > 0:
            sentiment = "Positive"
        elif polarity < 0:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
        
        return {
            'sentiment': sentiment,
            'polarity': round(polarity, 3),
            'subjectivity': round(subjectivity, 3)
        }
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        # Return neutral sentiment on error
        return {
            'sentiment': 'Neutral',
            'polarity': 0.0,
            'subjectivity': 0.0
        }


def classify_sentiment(polarity: float) -> str:
    """
    Classify sentiment based on polarity score.
    
    Why: Reusable helper for consistent sentiment classification.
    
    Input: polarity (float) - Polarity score from -1 to 1
    
    Output: str - 'Positive', 'Negative', or 'Neutral'
    """
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

"""
Unit tests for Amazon Review Insight Pro core functionality.
Tests sentiment analysis, suspicion rules, classification, CSV validation, and database operations.
"""

import sys
import os
import pandas as pd
import tempfile
import sqlite3

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.sentiment import analyze_sentiment, classify_sentiment
from services.review_analyzer import (
    check_very_short_review,
    check_excessive_repeated_words,
    check_excessive_capital_letters,
    check_too_many_exclamation_marks,
    check_repeated_promotional_phrases,
    check_very_extreme_language,
    check_duplicate_or_similar,
    calculate_suspicion_score,
    get_all_rule_descriptions
)
from services.data_processor import validate_csv, clean_dataframe, limit_reviews, MAX_REVIEWS
from database.database import (
    init_db, insert_review, insert_reviews, get_reviews, 
    delete_review, clear_all, get_products, get_review_count
)


def test_sentiment_classification():
    """Test sentiment classification (positive, negative, neutral)."""
    print("Testing sentiment classification...")
    
    # Test positive
    result = analyze_sentiment("I love this product! It's amazing and wonderful.")
    assert result['sentiment'] == 'Positive', f"Expected Positive, got {result['sentiment']}"
    assert result['polarity'] > 0, "Positive text should have polarity > 0"
    
    # Test negative
    result = analyze_sentiment("I hate this product. It's terrible and awful.")
    assert result['sentiment'] == 'Negative', f"Expected Negative, got {result['sentiment']}"
    assert result['polarity'] < 0, "Negative text should have polarity < 0"
    
    # Test neutral
    result = analyze_sentiment("This product is okay. It does what it says.")
    assert result['sentiment'] in ['Neutral', 'Positive'], f"Expected Neutral or Positive, got {result['sentiment']}"
    
    print("✓ Sentiment classification tests passed")


def test_suspicion_rules():
    """Test all 7 suspicion detection rules."""
    print("Testing suspicion rules...")
    
    # Rule 1: Very short review
    assert check_very_short_review("OK") == True, "Very short review should trigger"
    assert check_very_short_review("This is a normal length review with enough words.") == False, "Normal review should not trigger"
    
    # Rule 2: Excessive repeated words
    assert check_excessive_repeated_words("good good good good good good") == True, "Excessive repetition should trigger"
    assert check_excessive_repeated_words("This is a normal review without repetition.") == False, "Normal text should not trigger"
    
    # Rule 3: Excessive capital letters
    assert check_excessive_capital_letters("THIS IS ALL CAPS TEXT") == True, "All caps should trigger"
    assert check_excessive_capital_letters("This is normal text with some CAPS.") == False, "Normal text should not trigger"
    
    # Rule 4: Too many exclamation marks
    assert check_too_many_exclamation_marks("Great product!!!") == True, "3 exclamation marks should trigger"
    assert check_too_many_exclamation_marks("Great product!") == False, "1 exclamation mark should not trigger"
    
    # Rule 5: Repeated promotional phrases
    assert check_repeated_promotional_phrases("Best product ever! Must buy now!") == True, "Promotional phrases should trigger"
    assert check_repeated_promotional_phrases("This is a normal review about the product.") == False, "Normal text should not trigger"
    
    # Rule 6: Very extreme language
    assert check_very_extreme_language("This is the worst and most terrible product ever!") == True, "Extreme language should trigger"
    assert check_very_extreme_language("This product is not very good.") == False, "Normal text should not trigger"
    
    # Rule 7: Duplicate or similar text
    existing = ["This is a great product"]
    assert check_duplicate_or_similar("This is a great product", existing) == True, "Exact duplicate should trigger"
    assert check_duplicate_or_similar("This is a great product!", existing) == True, "Similar text should trigger"
    assert check_duplicate_or_similar("This is a different review", existing) == False, "Different text should not trigger"
    
    print("✓ All 7 suspicion rule tests passed")


def test_classification_threshold():
    """Test classification threshold (0-2 = Genuine, 3+ = Suspicious)."""
    print("Testing classification threshold...")
    
    # Test genuine classification (0-2 indicators)
    result = calculate_suspicion_score("This is a normal review with good content and reasonable length.")
    assert result['classification'] == 'Genuine-looking', f"Expected Genuine-looking, got {result['classification']}"
    assert result['suspicion_score'] <= 2, "Normal review should have low suspicion score"
    
    # Test suspicious classification (3+ indicators)
    suspicious_text = "BEST PRODUCT EVER!!! MUST BUY NOW!!! AMAZING!!!"
    result = calculate_suspicion_score(suspicious_text)
    assert result['classification'] == 'Suspicious', f"Expected Suspicious, got {result['classification']}"
    assert result['suspicion_score'] >= 3, "Suspicious review should have high suspicion score"
    
    print("✓ Classification threshold tests passed")


def test_csv_validation():
    """Test CSV validation (missing columns, empty file, bad rating)."""
    print("Testing CSV validation...")
    
    # Test missing columns
    df_missing = pd.DataFrame({'text': ['review1'], 'rating': [5]})
    is_valid, error = validate_csv(df_missing)
    assert is_valid == False, "CSV with missing columns should be invalid"
    assert 'review_text' in error, "Error should mention missing column"
    
    # Test empty CSV
    df_empty = pd.DataFrame()
    is_valid, error = validate_csv(df_empty)
    assert is_valid == False, "Empty CSV should be invalid"
    assert 'empty' in error.lower(), "Error should mention empty file"
    
    # Test valid CSV
    df_valid = pd.DataFrame({
        'review_text': ['Great product', 'Not bad'],
        'rating': [5, 4]
    })
    is_valid, error = validate_csv(df_valid)
    assert is_valid == True, "Valid CSV should pass validation"
    assert error == "", "Valid CSV should have no error message"
    
    print("✓ CSV validation tests passed")


def test_fifty_review_limit():
    """Test 50 review limit enforcement."""
    print("Testing 50 review limit...")
    
    # Create DataFrame with 60 reviews
    df_large = pd.DataFrame({
        'review_text': [f'Review {i}' for i in range(60)],
        'rating': [5] * 60,
        'product_name': ['Test Product'] * 60
    })
    
    # Apply limit
    df_limited, was_limited = limit_reviews(df_large)
    
    assert len(df_limited) == MAX_REVIEWS, f"Should limit to {MAX_REVIEWS} reviews"
    assert was_limited == True, "Should indicate that limiting occurred"
    
    # Test with under limit
    df_small = pd.DataFrame({
        'review_text': [f'Review {i}' for i in range(10)],
        'rating': [5] * 10,
        'product_name': ['Test Product'] * 10
    })
    
    df_not_limited, was_not_limited = limit_reviews(df_small)
    assert len(df_not_limited) == 10, "Should not limit if under max"
    assert was_not_limited == False, "Should indicate no limiting occurred"
    
    print("✓ 50 review limit tests passed")


def test_database_operations():
    """Test database insert, read, delete, and clear operations."""
    print("Testing database operations...")
    
    # Use temporary database for testing
    original_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'reviews.db')
    temp_db_path = tempfile.mktemp(suffix='.db')
    
    # Monkey patch the database path
    import database.database
    original_path = database.database.DB_PATH
    database.database.DB_PATH = temp_db_path
    
    try:
        # Initialize database
        assert init_db() == True, "Database initialization should succeed"
        
        # Test insert single review
        review_data = {
            'product_name': 'Test Product',
            'review_text': 'This is a test review',
            'rating': 5.0,
            'sentiment': 'Positive',
            'polarity': 0.5,
            'subjectivity': 0.3,
            'suspicion_score': 0,
            'classification': 'Genuine-looking'
        }
        review_id = insert_review(review_data)
        assert review_id is not None, "Insert should return an ID"
        assert review_id > 0, "Insert should return positive ID"
        
        # Test get reviews
        reviews = get_reviews()
        assert len(reviews) == 1, "Should have 1 review"
        assert reviews[0]['product_name'] == 'Test Product', "Should retrieve correct product"
        
        # Test insert bulk
        bulk_reviews = [
            {
                'product_name': 'Product A',
                'review_text': 'Review A',
                'rating': 4.0,
                'sentiment': 'Positive',
                'polarity': 0.3,
                'subjectivity': 0.4,
                'suspicion_score': 1,
                'classification': 'Genuine-looking'
            },
            {
                'product_name': 'Product B',
                'review_text': 'Review B',
                'rating': 3.0,
                'sentiment': 'Neutral',
                'polarity': 0.0,
                'subjectivity': 0.5,
                'suspicion_score': 0,
                'classification': 'Genuine-looking'
            }
        ]
        inserted_count = insert_reviews(bulk_reviews)
        assert inserted_count == 2, "Should insert 2 reviews"
        
        # Test get count
        count = get_review_count()
        assert count == 3, "Should have 3 total reviews"
        
        # Test get products
        products = get_products()
        assert len(products) == 3, "Should have 3 unique products"
        
        # Test delete review
        assert delete_review(review_id) == True, "Delete should succeed"
        reviews_after_delete = get_reviews()
        assert len(reviews_after_delete) == 2, "Should have 2 reviews after delete"
        
        # Test clear all
        assert clear_all() == True, "Clear all should succeed"
        reviews_after_clear = get_reviews()
        assert len(reviews_after_clear) == 0, "Should have 0 reviews after clear"
        
        print("✓ Database operation tests passed")
        
    finally:
        # Restore original database path
        database.database.DB_PATH = original_path
        # Clean up temporary database
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)


def test_all_rule_descriptions():
    """Test that all 7 rule descriptions are available."""
    print("Testing rule descriptions...")
    
    rules = get_all_rule_descriptions()
    assert len(rules) == 7, f"Should have 7 rules, got {len(rules)}"
    
    expected_rules = [
        "Very short review",
        "Excessive repeated words",
        "Excessive capital letters",
        "Too many exclamation marks",
        "Repeated promotional phrases",
        "Very extreme language",
        "Duplicate/similar review text"
    ]
    
    for rule in expected_rules:
        assert rule in rules, f"Rule '{rule}' should be in descriptions"
    
    print("✓ Rule descriptions tests passed")


def test_data_cleaning():
    """Test data cleaning functionality."""
    print("Testing data cleaning...")
    
    # Create test DataFrame with dirty data
    df_dirty = pd.DataFrame({
        'review_text': [
            'Great product! http://spam.com <b>HTML</b>',
            '  Extra   spaces  ',
            'Normal review'
        ],
        'rating': [5, 4, 3],
        'product_name': ['Product A', 'Product A', 'Product B']
    })
    
    df_clean = clean_dataframe(df_dirty)
    
    # Check that URLs and HTML are removed
    assert 'http' not in df_clean['cleaned_text'].iloc[0], "URLs should be removed"
    assert '<b>' not in df_clean['cleaned_text'].iloc[0], "HTML tags should be removed"
    
    # Check that extra spaces are normalized
    assert df_clean['cleaned_text'].iloc[1] == 'Extra spaces', "Extra spaces should be normalized"
    
    # Check that DataFrame is not empty
    assert len(df_clean) > 0, "Cleaned DataFrame should not be empty"
    
    print("✓ Data cleaning tests passed")


def run_all_tests():
    """Run all unit tests."""
    print("=" * 50)
    print("Running Amazon Review Insight Pro Unit Tests")
    print("=" * 50)
    
    try:
        test_sentiment_classification()
        test_suspicion_rules()
        test_classification_threshold()
        test_csv_validation()
        test_fifty_review_limit()
        test_database_operations()
        test_all_rule_descriptions()
        test_data_cleaning()
        
        print("=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        return True
        
    except AssertionError as e:
        print("=" * 50)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 50)
        return False
    except Exception as e:
        print("=" * 50)
        print(f"❌ ERROR: {e}")
        print("=" * 50)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

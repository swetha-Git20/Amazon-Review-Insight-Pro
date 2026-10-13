"""
Comprehensive Unit and Integration Tests for Amazon Review Insight Pro Analyzer
Tests authentication, user data isolation, sentiment analysis, suspicion heuristics,
file upload processing, Amazon URL parsing, and export generation.
"""

import sys
import os
import io
import pandas as pd
import tempfile
import sqlite3

# Ensure UTF-8 output on Windows consoles to prevent UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import (
    init_db, register_user, authenticate_user, hash_password, verify_password,
    insert_review, insert_reviews, get_reviews, delete_review, clear_all,
    get_products, get_review_count, get_user_history, delete_history_item,
    get_user_product_summary, delete_product_reviews
)
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
from services.data_processor import (
    parse_uploaded_file, validate_csv, clean_dataframe,
    clean_text, clean_rating, limit_reviews, map_column_aliases, MAX_REVIEWS
)
from services.review_fetcher import (
    extract_amazon_details, validate_amazon_url, DEMO_PRODUCTS
)


def log_test(name: str):
    print(f"[TEST] {name}...")


def log_pass(name: str):
    print(f" [PASS] {name}")


def test_password_security_and_auth():
    """Test PBKDF2 password hashing, salt uniqueness, and user authentication."""
    log_test("Password Security & User Authentication")
    
    init_db()
    
    # 1. Hashing and verification
    pwd = "SecurePassword123!"
    hash1, salt1 = hash_password(pwd)
    hash2, salt2 = hash_password(pwd)
    
    assert salt1 != salt2, "Each password hash must have a unique random salt"
    assert hash1 != hash2, "Identical passwords with different salts must yield different hashes"
    assert verify_password(pwd, salt1, hash1) == True, "Verification must succeed with matching credentials"
    assert verify_password("WrongPassword!", salt1, hash1) == False, "Verification must fail with incorrect password"
    
    # 2. Registration validation
    import uuid
    unique_suffix = uuid.uuid4().hex[:6]
    test_user = f"user_{unique_suffix}"
    test_email = f"{test_user}@testdomain.com"
    
    # Short username rejected
    ok, err, _ = register_user("ab", test_email, pwd)
    assert ok == False, "Username < 3 chars must be rejected"
    
    # Invalid email rejected
    ok, err, _ = register_user(test_user, "invalid-email", pwd)
    assert ok == False, "Invalid email format must be rejected"
    
    # Valid registration
    ok, msg, uid = register_user(test_user, test_email, pwd)
    assert ok == True, f"Valid user registration failed: {msg}"
    assert uid is not None, "Registered user must receive a valid user ID"
    
    # Duplicate username rejected
    dup_ok, _, _ = register_user(test_user, f"another_{test_email}", pwd)
    assert dup_ok == False, "Duplicate username registration must be rejected"
    
    # 3. Authentication
    auth_ok, auth_msg, u_data = authenticate_user(test_user, pwd)
    assert auth_ok == True, f"Authentication with username failed: {auth_msg}"
    assert u_data['username'] == test_user
    
    # Authentication with email
    auth_email_ok, _, _ = authenticate_user(test_email, pwd)
    assert auth_email_ok == True, "Authentication with email must succeed"
    
    # Authentication failure
    fail_ok, _, _ = authenticate_user(test_user, "WrongPassword999")
    assert fail_ok == False, "Authentication with wrong password must fail"
    
    log_pass("Password Security & User Authentication")
    return uid


def test_user_data_isolation():
    """Test Requirement 2: Strict isolation between separate user accounts."""
    log_test("User Data Isolation (Account Privacy)")
    
    init_db()
    import uuid
    suffix_a = uuid.uuid4().hex[:6]
    suffix_b = uuid.uuid4().hex[:6]
    
    _, _, uid_a = register_user(f"analyst_a_{suffix_a}", f"a_{suffix_a}@example.com", "PasswordA123!")
    _, _, uid_b = register_user(f"analyst_b_{suffix_b}", f"b_{suffix_b}@example.com", "PasswordB123!")
    
    assert uid_a != uid_b, "User A and User B must have distinct IDs"
    
    # User A inserts reviews
    rev_a = {
        'product_name': 'Private Product A',
        'review_text': 'This is User A private review text for product A.',
        'rating': 5.0,
        'sentiment': 'Positive',
        'polarity': 0.8,
        'subjectivity': 0.5,
        'suspicion_score': 0,
        'classification': 'Genuine-looking'
    }
    insert_review(uid_a, rev_a)
    
    # User B inserts reviews
    rev_b = {
        'product_name': 'Private Product B',
        'review_text': 'This is User B private review text for product B.',
        'rating': 2.0,
        'sentiment': 'Negative',
        'polarity': -0.6,
        'subjectivity': 0.4,
        'suspicion_score': 1,
        'classification': 'Genuine-looking'
    }
    insert_review(uid_b, rev_b)
    
    # Verify User A only sees Product A and Review A
    reviews_a = get_reviews(uid_a)
    products_a = get_products(uid_a)
    count_a = get_review_count(uid_a)
    
    assert count_a == 1, f"Expected 1 review for User A, found {count_a}"
    assert len(reviews_a) == 1
    assert reviews_a[0]['product_name'] == 'Private Product A'
    assert 'Private Product B' not in products_a, "CRITICAL: User A must never see User B's products!"
    
    # Verify User B only sees Product B and Review B
    reviews_b = get_reviews(uid_b)
    products_b = get_products(uid_b)
    count_b = get_review_count(uid_b)
    
    assert count_b == 1, f"Expected 1 review for User B, found {count_b}"
    assert len(reviews_b) == 1
    assert reviews_b[0]['product_name'] == 'Private Product B'
    assert 'Private Product A' not in products_b, "CRITICAL: User B must never see User A's products!"
    
    # Test User A cannot delete User B's review
    b_review_id = reviews_b[0]['id']
    del_res = delete_review(uid_a, b_review_id)
    assert del_res == False, "User A must NOT be able to delete User B's review"
    assert get_review_count(uid_b) == 1, "User B's review must remain intact"
    
    # Test Product Summaries isolation (Requirement 5)
    summary_b = get_user_product_summary(uid_b)
    assert len(summary_b) == 1
    assert summary_b[0]['product_name'] == 'Private Product B'
    assert summary_b[0]['total_reviews'] == 1
    
    # Test User A product summary is empty
    summary_a = get_user_product_summary(uid_a)
    assert len(summary_a) == 1
    assert summary_a[0]['product_name'] == 'Private Product A'
    
    # Test Clear All is user-isolated
    clear_all(uid_a)
    assert get_review_count(uid_a) == 0, "User A reviews must be cleared"
    assert get_review_count(uid_b) == 1, "User B reviews must NOT be cleared when User A clears data"
    
    # Test delete_product_reviews
    del_p_res = delete_product_reviews(uid_b, 'Private Product B')
    assert del_p_res == True
    assert get_review_count(uid_b) == 0
    
    # Clean up User B
    clear_all(uid_b)
    
    log_pass("User Data Isolation (Account Privacy)")


def test_sentiment_analysis():
    """Test TextBlob sentiment polarity, subjectivity, and classification."""
    log_test("Sentiment Analysis Service")
    
    # Positive
    res_pos = analyze_sentiment("This product is fantastic and exceeded all my expectations!")
    assert res_pos['sentiment'] == 'Positive'
    assert res_pos['polarity'] > 0
    
    # Negative
    res_neg = analyze_sentiment("Terrible experience. The item arrived broken and useless.")
    assert res_neg['sentiment'] == 'Negative'
    assert res_neg['polarity'] < 0
    
    # Neutral
    res_neu = analyze_sentiment("The package arrived on Tuesday.")
    assert res_neu['sentiment'] in ['Neutral', 'Positive']
    
    # Helper classification
    assert classify_sentiment(0.5) == "Positive"
    assert classify_sentiment(-0.5) == "Negative"
    assert classify_sentiment(0.0) == "Neutral"
    
    log_pass("Sentiment Analysis Service")


def test_suspicion_heuristics():
    """Test all 7 heuristic suspicion detection rules."""
    log_test("7 Heuristic Suspicion Rules")
    
    # Rule 1: Very short review
    assert check_very_short_review("Good.") == True
    assert check_very_short_review("This is a detailed and well-written review of the item.") == False
    
    # Rule 2: Excessive repeated words
    assert check_excessive_repeated_words("wow wow wow wow wow wow great") == True
    assert check_excessive_repeated_words("This is a balanced and natural sentence structure.") == False
    
    # Rule 3: Excessive capital letters
    assert check_excessive_capital_letters("BUY THIS RIGHT NOW IT IS THE GREATEST") == True
    assert check_excessive_capital_letters("This is a standard review with normal capitalization.") == False
    
    # Rule 4: Too many exclamation marks
    assert check_too_many_exclamation_marks("Incredible headphones!!!") == True
    assert check_too_many_exclamation_marks("Incredible headphones!") == False
    
    # Rule 5: Repeated promotional phrases
    assert check_repeated_promotional_phrases("Best product ever! You must buy now!") == True
    assert check_repeated_promotional_phrases("The build quality is quite solid for the price.") == False
    
    # Rule 6: Very extreme language
    assert check_very_extreme_language("This is the worst, most horrible product ever made.") == True
    assert check_very_extreme_language("It works fine but has a minor flaw.") == False
    
    # Rule 7: Duplicate or similar text
    existing = ["The battery life lasts all day and audio is clear."]
    assert check_duplicate_or_similar("The battery life lasts all day and audio is clear.", existing) == True
    assert check_duplicate_or_similar("The battery life lasts all day and audio is clear!", existing) == True
    assert check_duplicate_or_similar("A completely different review about comfort.", existing) == False
    
    # Overall scoring & classification
    clean_review = "I bought these headphones for commuting. The noise cancellation works well and comfort is good."
    score_clean = calculate_suspicion_score(clean_review)
    assert score_clean['classification'] == 'Genuine-looking'
    assert score_clean['suspicion_score'] <= 2
    
    spam_review = "BEST PRODUCT EVER! MUST BUY NOW! AMAZING AMAZING AMAZING! BUY THIS RIGHT NOW!!!"
    score_spam = calculate_suspicion_score(spam_review)
    assert score_spam['classification'] == 'Suspicious'
    assert score_spam['suspicion_score'] >= 3
    
    log_pass("7 Heuristic Suspicion Rules")


def test_file_upload_processor():
    """Test Requirement 3: CSV/Excel validation, alias mapping, and error reporting."""
    log_test("File Upload & Data Processor")
    
    # 1. Alias mapping
    raw_df = pd.DataFrame({
        'Comment': ['Loved the battery life', 'Cheap plastic'],
        'Stars': [5, 1],
        'Item_Name': ['Gadget A', 'Gadget A']
    })
    mapped = map_column_aliases(raw_df)
    assert 'review_text' in mapped.columns
    assert 'rating' in mapped.columns
    assert 'product_name' in mapped.columns
    
    # 2. Validation
    is_valid, err = validate_csv(mapped)
    assert is_valid == True, f"Mapped dataframe should be valid: {err}"
    
    # Invalid missing review text
    bad_df = pd.DataFrame({'other_col': [1, 2]})
    bad_valid, bad_err = validate_csv(bad_df)
    assert bad_valid == False
    assert "review_text" in bad_err
    
    # 3. Text & rating cleaning
    raw_html_text = "<p>Great sound! Visit http://promo.com for discount.</p>"
    cleaned = clean_text(raw_html_text)
    assert "<p>" not in cleaned
    assert "http" not in cleaned
    assert "Great sound!" in cleaned
    
    assert clean_rating("4.5") == 4.5
    assert clean_rating("5") == 5.0
    assert clean_rating("invalid") is None
    assert clean_rating(10) == 5.0  # normalized from 10 scale
    
    # 4. In-memory CSV parsing test
    csv_bytes = b"review_text,rating,product_name\nGreat item!,5,Earbuds\nPoor quality.,1,Earbuds\n"
    
    class FakeUploadedFile:
        def __init__(self, name, content):
            self.name = name
            self._content = content
        def getvalue(self):
            return self._content
            
    fake_csv = FakeUploadedFile("reviews.csv", csv_bytes)
    ok, msg, parsed_df = parse_uploaded_file(fake_csv)
    assert ok == True
    assert len(parsed_df) == 2
    
    log_pass("File Upload & Data Processor")


def test_amazon_url_details():
    """Test Requirement 4: Amazon URL parser, ASIN extraction, and demo products."""
    log_test("Amazon URL Parser & Product Link Generator")
    
    test_urls = [
        ("https://www.amazon.com/dp/B0863TXGM3", "B0863TXGM3", "amazon.com"),
        ("https://www.amazon.in/boAt-Rockerz-450/dp/B07PR1CL3S", "B07PR1CL3S", "amazon.in"),
        ("https://amazon.co.uk/gp/product/B08N5WRWNW?ref=nav", "B08N5WRWNW", "amazon.co.uk"),
        ("https://www.amazon.de/product-reviews/B09TMN58KL", "B09TMN58KL", "amazon.de")
    ]
    
    for url, expected_asin, expected_domain in test_urls:
        details = extract_amazon_details(url)
        assert details['is_valid'] == True, f"Failed on valid URL: {url}"
        assert details['asin'] == expected_asin, f"Expected {expected_asin}, got {details['asin']}"
        assert expected_domain in details['domain'], f"Expected domain {expected_domain}, got {details['domain']}"
        assert details['canonical_url'].startswith("https://www."), "Canonical URL must be well-formed"
        assert expected_asin in details['canonical_url']
        
    # Invalid URLs
    invalid_urls = [
        "https://www.google.com/search?q=amazon",
        "https://www.amazon.com/help",
        "not-a-url"
    ]
    for inv in invalid_urls:
        det = extract_amazon_details(inv)
        assert det['is_valid'] == False, f"Invalid URL should not be marked valid: {inv}"
        
    # Demo products verification
    assert len(DEMO_PRODUCTS) >= 3, "Curated demo products must be provided"
    for demo in DEMO_PRODUCTS:
        assert validate_amazon_url(demo['url']) == True
        assert demo['asin'] is not None
        
    log_pass("Amazon URL Parser & Product Link Generator")


def run_all_tests():
    """Execute complete test suite."""
    print("=" * 60)
    print("Amazon Review Insight Pro Analyzer - Test Verification Suite")
    print("=" * 60)
    
    try:
        test_password_security_and_auth()
        test_user_data_isolation()
        test_sentiment_analysis()
        test_suspicion_heuristics()
        test_file_upload_processor()
        test_amazon_url_details()
        
        print("=" * 60)
        print("[SUCCESS] ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"[FAIL] Assertion Failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

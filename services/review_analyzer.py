"""
Review analyzer service for Amazon Review Insight Pro
Implements rule-based suspicious review detection using 7 heuristics.
"""

import re
import difflib
from typing import Dict, List, Tuple


# Suspicion rule thresholds (named constants for easy adjustment)
MIN_WORD_COUNT = 5  # For very short review check
REPEAT_WORD_THRESHOLD = 0.30  # 30% of same word
REPEAT_WORD_MIN_WORDS = 6  # Minimum words to check repetition
CAPS_THRESHOLD = 0.50  # 50% uppercase letters
CAPS_MIN_LENGTH = 10  # Minimum letters to check caps
EXCLAMATION_LIMIT = 3  # Maximum exclamation marks
SIMILARITY_THRESHOLD = 0.85  # For duplicate/similar review detection

# Promotional phrases list
PROMOTIONAL_PHRASES = [
    "best product ever",
    "must buy",
    "highly recommended",
    "buy now",
    "five stars",
    "100% genuine",
    "amazing product",
    "don't miss",
    "limited time",
    "act now"
]

# Extreme language words
EXTREME_WORDS = [
    "worst",
    "perfect",
    "amazing",
    "terrible",
    "awful",
    "incredible",
    "best ever",
    "useless",
    "horrible",
    "fantastic",
    "garbage",
    "excellent",
    "phenomenal",
    "disgusting",
    "outstanding"
]


def check_very_short_review(text: str) -> bool:
    """
    Check if review is very short (fewer than 5 words).
    
    Why: Extremely short reviews often lack detail and may be spam.
    
    Input: text (str) - Review text
    
    Output: bool - True if suspicious, False otherwise
    """
    words = text.split()
    return len(words) < MIN_WORD_COUNT


def check_excessive_repeated_words(text: str) -> bool:
    """
    Check if a single word makes up 30% or more of the words.
    
    Why: Excessive repetition is common in spam/fake reviews.
    
    Input: text (str) - Review text
    
    Output: bool - True if suspicious, False otherwise
    """
    words = text.lower().split()
    
    # Need minimum words to check
    if len(words) < REPEAT_WORD_MIN_WORDS:
        return False
    
    # Count word frequency
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # Check if any word exceeds threshold
    max_count = max(word_counts.values())
    return (max_count / len(words)) >= REPEAT_WORD_THRESHOLD


def check_excessive_capital_letters(text: str) -> bool:
    """
    Check if more than 50% of letters are uppercase.
    
    Why: Excessive capitalization is often used for emphasis in fake reviews.
    
    Input: text (str) - Review text
    
    Output: bool - True if suspicious, False otherwise
    """
    # Remove non-letter characters
    letters = re.findall(r'[A-Za-z]', text)
    
    # Need minimum letters to check
    if len(letters) < CAPS_MIN_LENGTH:
        return False
    
    # Count uppercase letters
    uppercase = sum(1 for char in letters if char.isupper())
    
    return (uppercase / len(letters)) > CAPS_THRESHOLD


def check_too_many_exclamation_marks(text: str) -> bool:
    """
    Check if there are 3 or more exclamation marks.
    
    Why: Excessive punctuation is common in promotional/fake reviews.
    
    Input: text (str) - Review text
    
    Output: bool - True if suspicious, False otherwise
    """
    return text.count('!') >= EXCLAMATION_LIMIT


def check_repeated_promotional_phrases(text: str) -> bool:
    """
    Check if 2 or more promotional phrases are present.
    
    Why: Promotional language is common in biased/fake reviews.
    
    Input: text (str) - Review text
    
    Output: bool - True if suspicious, False otherwise
    """
    text_lower = text.lower()
    found_phrases = 0
    
    for phrase in PROMOTIONAL_PHRASES:
        if phrase in text_lower:
            found_phrases += 1
            if found_phrases >= 2:
                return True
    
    return False


def check_very_extreme_language(text: str) -> bool:
    """
    Check if 2 or more extreme language words are present.
    
    Why: Extreme language is often used in fake reviews to influence.
    
    Input: text (str) - Review text
    
    Output: bool - True if suspicious, False otherwise
    """
    text_lower = text.lower()
    found_words = 0
    
    for word in EXTREME_WORDS:
        if word in text_lower:
            found_words += 1
            if found_words >= 2:
                return True
    
    return False


def check_duplicate_or_similar(text: str, existing_texts: List[str]) -> bool:
    """
    Check if review is an exact duplicate or highly similar to existing reviews.
    
    Why: Duplicate or near-duplicate reviews suggest fake review campaigns.
    
    Input: text (str) - Review text to check
           existing_texts (List[str]) - List of existing review texts
    
    Output: bool - True if suspicious, False otherwise
    """
    for existing_text in existing_texts:
        # Check exact duplicate
        if text == existing_text:
            return True
        
        # Check similarity using difflib
        similarity = difflib.SequenceMatcher(None, text, existing_text).ratio()
        if similarity >= SIMILARITY_THRESHOLD:
            return True
    
    return False


def calculate_suspicion_score(text: str, existing_texts: List[str] = None) -> Dict:
    """
    Calculate suspicion score by checking all 7 rules.
    
    Why: Combine multiple heuristics to identify potentially suspicious reviews.
    
    Input: text (str) - Review text to analyze
           existing_texts (List[str]) - Existing reviews for duplicate check
    
    Output: Dict - Dictionary with score, triggered rules, and classification
    """
    if existing_texts is None:
        existing_texts = []
    
    triggered_rules = []
    
    # Check each rule
    if check_very_short_review(text):
        triggered_rules.append("Very short review")
    
    if check_excessive_repeated_words(text):
        triggered_rules.append("Excessive repeated words")
    
    if check_excessive_capital_letters(text):
        triggered_rules.append("Excessive capital letters")
    
    if check_too_many_exclamation_marks(text):
        triggered_rules.append("Too many exclamation marks")
    
    if check_repeated_promotional_phrases(text):
        triggered_rules.append("Repeated promotional phrases")
    
    if check_very_extreme_language(text):
        triggered_rules.append("Very extreme language")
    
    if check_duplicate_or_similar(text, existing_texts):
        triggered_rules.append("Duplicate/similar review text")
    
    # Calculate score (number of triggered rules)
    suspicion_score = len(triggered_rules)
    
    # Classify based on score
    if suspicion_score <= 2:
        classification = "Genuine-looking"
    else:
        classification = "Suspicious"
    
    return {
        'suspicion_score': suspicion_score,
        'triggered_rules': triggered_rules,
        'classification': classification
    }


def get_all_rule_descriptions() -> List[str]:
    """
    Get descriptions of all 7 suspicion rules.
    
    Why: Display in UI for transparency about what is being checked.
    
    Input: None
    
    Output: List[str] - List of rule descriptions
    """
    return [
        "Very short review",
        "Excessive repeated words",
        "Excessive capital letters",
        "Too many exclamation marks",
        "Repeated promotional phrases",
        "Very extreme language",
        "Duplicate/similar review text"
    ]

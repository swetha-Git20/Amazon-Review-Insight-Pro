"""
Review fetcher service for Amazon Review Insight Pro
Handles fetching reviews from Amazon product URLs.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Tuple, Optional


# Amazon URL pattern for validation
AMAZON_URL_PATTERN = r'https?://www\.amazon\.[a-z]{2,3}/dp/[A-Z0-9]{10}'


def validate_amazon_url(url: str) -> bool:
    """
    Validate if the URL is a valid Amazon product URL.
    
    Why: Ensure we only attempt to fetch from valid Amazon product pages.
    
    Input: url (str) - URL to validate
    
    Output: bool - True if valid Amazon URL, False otherwise
    """
    return bool(re.match(AMAZON_URL_PATTERN, url))


def fetch_reviews_from_url(url: str) -> Tuple[bool, str, Optional[list]]:
    """
    Attempt to fetch reviews from an Amazon product URL.
    
    Why: Allow users to import reviews directly from Amazon product pages.
    
    Input: url (str) - Amazon product URL
    
    Output: Tuple[bool, str, Optional[list]] - (success, message, reviews_list)
    """
    # Validate URL format
    if not validate_amazon_url(url):
        return False, "Invalid Amazon URL. Please use a valid Amazon product URL (e.g., https://www.amazon.com/dp/B08N5WRWNW)", None
    
    try:
        # Set up headers with a normal User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # Make a polite request with timeout
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if request was successful
        if response.status_code != 200:
            return False, f"Could not fetch page. Status code: {response.status_code}", None
        
        # Check if we were redirected to login or CAPTCHA
        if 'signin' in response.url.lower() or 'captcha' in response.text.lower():
            return False, "Could not fetch reviews automatically. Amazon requires login or CAPTCHA. Please use the CSV upload option.", None
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find review elements (Amazon's structure changes frequently)
        reviews = []
        review_elements = soup.find_all('div', {'data-hook': 'review'})
        
        if not review_elements:
            # Try alternative selectors
            review_elements = soup.find_all('div', class_='review')
        
        if not review_elements:
            return False, "Could not find reviews on the page. The page structure may have changed or reviews may not be available. Please use the CSV upload option.", None
        
        # Extract review data
        for review in review_elements:
            try:
                # Try to extract review text
                review_text_elem = review.find('span', {'data-hook': 'review-body'})
                if not review_text_elem:
                    review_text_elem = review.find('span', class_='review-text')
                
                review_text = review_text_elem.get_text(strip=True) if review_text_elem else ""
                
                # Try to extract rating
                rating_elem = review.find('i', {'data-hook': 'review-star-rating'})
                if not rating_elem:
                    rating_elem = review.find('i', class_='review-rating')
                
                rating = None
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    # Extract number from rating text (e.g., "4.0 out of 5 stars")
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                if review_text:  # Only add if we have text
                    reviews.append({
                        'review_text': review_text,
                        'rating': rating,
                        'product_name': 'Amazon Product'  # Could be extracted from page title
                    })
                
                # Limit to reasonable number for demo
                if len(reviews) >= 50:
                    break
                    
            except Exception as e:
                print(f"Error extracting individual review: {e}")
                continue
        
        if not reviews:
            return False, "Could not extract review data from the page. Please use the CSV upload option.", None
        
        return True, f"Successfully fetched {len(reviews)} reviews", reviews
        
    except requests.exceptions.Timeout:
        return False, "Request timed out. Please check your connection and try again, or use CSV upload.", None
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {str(e)}. Please use the CSV upload option.", None
    except Exception as e:
        return False, f"Error fetching reviews: {str(e)}. Please use the CSV upload option.", None

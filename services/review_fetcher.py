"""
Review fetcher service for Amazon Review Insight Pro Analyzer
Handles URL parsing, canonical Amazon link generation, and honest live review extraction.
Strict Policy: Never returns mock, simulated, or hardcoded reviews for URL imports.
"""

import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import Tuple, Optional, Dict, List


# Regex pattern to capture Amazon domains and 10-character ASINs
AMAZON_DOMAIN_PATTERN = r'https?://(?:www\.)?(amazon\.[a-z\.]+)'
ASIN_PATTERN = r'(?:/dp/|/gp/product/|/gp/aw/d/|/product-reviews/|/d/|/ASIN/)([A-Z0-9]{10})'

# Curated list of verified demo products with valid Amazon URLs
DEMO_PRODUCTS = [
    {
        "name": "boAt Rockerz 450 Bluetooth On-Ear Headphones",
        "url": "https://www.amazon.in/dp/B07PR1CL3S",
        "asin": "B07PR1CL3S",
        "marketplace": "Amazon India (.in)",
        "category": "Electronics / Audio"
    },
    {
        "name": "Sony WH-1000XM4 Wireless Premium Noise Canceling Headphones",
        "url": "https://www.amazon.com/dp/B0863TXGM3",
        "asin": "B0863TXGM3",
        "marketplace": "Amazon US (.com)",
        "category": "Electronics / Audio"
    },
    {
        "name": "JBL Tune 510BT Wireless On-Ear Headphones",
        "url": "https://www.amazon.com/dp/B08WM3LMJF",
        "asin": "B08WM3LMJF",
        "marketplace": "Amazon US (.com)",
        "category": "Electronics / Audio"
    },
    {
        "name": "UltraSonic Wireless Earbuds Pro",
        "url": "https://www.amazon.com/dp/B0BDHWDR12",
        "asin": "B0BDHWDR12",
        "marketplace": "Amazon US (.com)",
        "category": "Electronics / Earbuds"
    },
    {
        "name": "Amazon Kindle Paperwhite (16 GB) 6.8 inch Display",
        "url": "https://www.amazon.com/dp/B09TMN58KL",
        "asin": "B09TMN58KL",
        "marketplace": "Amazon US (.com)",
        "category": "Devices / E-Reader"
    }
]


def extract_amazon_details(url: str) -> Dict[str, Optional[str]]:
    """
    Parse any valid Amazon product URL to extract the ASIN, marketplace domain, and canonical URL.
    
    Why: Supports all international Amazon domains, URL formats (with/without slugs, queries),
    missing http/https protocols, and shortened Amazon links (a.co, amzn.to).
    
    Input: url (str) - Any Amazon product link
    Output: Dict containing is_valid, asin, domain, and canonical_url
    """
    if not url or not isinstance(url, str):
        return {"is_valid": False, "asin": None, "domain": None, "canonical_url": None, "clean_url": url}
    
    url = url.strip()
    
    # Auto-prefix protocol if missing (e.g. amazon.com/dp/B0863TXGM3)
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    try:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        hostname = (parsed.netloc or '').lower()
    except Exception:
        hostname = ''
        parsed = None
    
    # Handle shortened Amazon domains (e.g. a.co/d/..., amzn.to/...)
    if any(short in hostname for short in ['a.co', 'amzn.to', 'amzn.in', 'amzn.eu']):
        try:
            resp = requests.head(url, allow_redirects=True, timeout=5)
            if resp.url and resp.url != url:
                url = resp.url
                parsed = urlparse(url)
                hostname = (parsed.netloc or '').lower()
        except Exception:
            pass

    # Extract marketplace domain
    domain = None
    if 'amazon.' in hostname:
        domain_match = re.search(r'(amazon\.[a-z\.]+)', hostname)
        if domain_match:
            domain = domain_match.group(1).lower()
    if not domain:
        # Fallback regex search on the entire URL
        domain_match = re.search(AMAZON_DOMAIN_PATTERN, url, re.IGNORECASE)
        if domain_match:
            domain = domain_match.group(1).lower()
            
    # Extract 10-character ASIN
    asin = None
    # 1. Standard path structures: /dp/ASIN, /gp/product/ASIN, /gp/aw/d/ASIN, /product-reviews/ASIN, /product/ASIN, /d/ASIN, /ASIN/ASIN
    path_str = parsed.path if parsed else url
    path_match = re.search(
        r'(?:/dp/|/gp/product/|/gp/aw/d/|/product-reviews/|/product/|/d/|/ASIN/|/)([A-Za-z0-9]{10})(?:[/?&#]|$)',
        path_str,
        re.IGNORECASE
    )
    if path_match:
        asin = path_match.group(1).upper()
    else:
        # 2. Query parameter check (e.g. ?asin=B0863TXGM3 or &dp=B0863TXGM3)
        if parsed and parsed.query:
            qs = parse_qs(parsed.query)
            for key in ['asin', 'ASIN', 'dp', 'product']:
                if key in qs and qs[key]:
                    val = qs[key][0].strip().upper()
                    if re.match(r'^[A-Z0-9]{10}$', val):
                        asin = val
                        break
        # 3. Direct general regex search anywhere in the URL
        if not asin:
            gen_match = re.search(r'(?:[/?&=]|^)([A-Za-z0-9]{10})(?:[/?&#]|$)', url)
            if gen_match and domain:
                candidate = gen_match.group(1).upper()
                if not candidate.startswith(('HTTP', 'WWW', 'AMAZ')):
                    asin = candidate
                    
    is_valid = bool(domain and asin)
    canonical_domain = domain if domain else "amazon.com"
    canonical_url = f"https://www.{canonical_domain}/dp/{asin}" if is_valid else url
    
    return {
        "is_valid": is_valid,
        "asin": asin,
        "domain": domain,
        "canonical_url": canonical_url,
        "clean_url": url
    }


def validate_amazon_url(url: str) -> bool:
    """
    Validate if a string is a recognizable Amazon product link containing an ASIN.
    """
    details = extract_amazon_details(url)
    return details["is_valid"]


def fetch_reviews_from_url(url: str) -> Tuple[bool, str, Optional[List[Dict]], Optional[Dict]]:
    """
    Attempt to fetch genuine reviews directly from an Amazon product page.
    
    Strict Authenticity Policy:
    - Extracts ONLY real HTML customer reviews for that specific product.
    - NEVER returns fake, mock, simulated, or extra reviews from other datasets.
    - If Amazon blocks with Robot Check / CAPTCHA or dynamically hydrates via JavaScript,
      reports honestly without generating synthetic reviews.
    
    Returns:
        Tuple[bool, str, Optional[List[Dict]], Optional[Dict]]
        (success, message, reviews_list, metadata)
    """
    details = extract_amazon_details(url)
    if not details["is_valid"]:
        return (
            False,
            "Invalid Amazon product link. Please ensure the URL is a valid Amazon product URL with an ASIN (e.g., https://www.amazon.com/dp/B0863TXGM3 or https://www.amazon.in/dp/B07PR1CL3S).",
            None,
            {"url": url}
        )
    
    target_url = details["canonical_url"]
    asin = details["asin"]
    domain = details["domain"] or "amazon.com"
    
    meta = {
        "asin": asin,
        "domain": domain,
        "canonical_url": target_url,
        "input_url": url,
        "product_name": f"Amazon Product ({asin})"
    }
    
    # Authentic browser headers
    header_variants = [
        {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Upgrade-Insecure-Requests': '1',
        }
    ]
    
    session = requests.Session()
    
    for h_idx, headers in enumerate(header_variants):
        try:
            response = session.get(target_url, headers=headers, timeout=12)
            page_html = response.text
            
            # Check for Amazon bot/CAPTCHA challenge
            is_bot_check = (
                "api-services-support@amazon.com" in page_html or
                "Type the characters you see in this image" in page_html or
                "To discuss automated access to Amazon data" in page_html or
                "Robot Check" in page_html or
                response.status_code in [403, 429, 503]
            )
            
            if is_bot_check:
                # Try next header variant if available
                if h_idx < len(header_variants) - 1:
                    continue
                return (
                    False,
                    f"Amazon's automated anti-bot security (Robot Check / CAPTCHA) intercepted access for ASIN {asin}. "
                    "In strict compliance with our data authenticity policy, this platform NEVER generates fake or hardcoded reviews. "
                    "Please use the Batch Upload tab to analyze genuine reviews exported from Amazon.",
                    None,
                    meta
                )
            
            if response.status_code != 200:
                if h_idx < len(header_variants) - 1:
                    continue
                return (
                    False,
                    f"Amazon server returned HTTP status {response.status_code}. The page could not be accessed directly.",
                    None,
                    meta
                )
            
            soup = BeautifulSoup(page_html, 'html.parser')
            
            # Extract actual product title from page
            title_elem = soup.find('span', {'id': 'productTitle'}) or soup.find('h1', {'id': 'title'})
            if not title_elem:
                title_elem = soup.find('title')
                if title_elem:
                    raw_title = title_elem.get_text(strip=True)
                    # Clean trailing Amazon branding
                    clean_t = re.sub(r'\s*:\s*Amazon\..*$', '', raw_title, flags=re.I)
                    clean_t = re.sub(r'^Amazon\.[a-z.]+:\s*', '', clean_t, flags=re.I)
                    if clean_t:
                        meta["product_name"] = clean_t
            else:
                meta["product_name"] = title_elem.get_text(strip=True)
                
            # Find review elements
            review_elements = soup.find_all('div', {'data-hook': 'review'})
            if not review_elements:
                review_elements = soup.find_all(attrs={'data-hook': 'review'})
            if not review_elements:
                review_elements = soup.find_all('div', class_=re.compile(r'\breview\b', re.I))
            
            reviews = []
            for rev in review_elements:
                try:
                    # 1. Rating
                    rating = None
                    rating_elem = (
                        rev.find(attrs={'data-hook': 'review-star-rating'}) or
                        rev.find(attrs={'data-hook': 'cmps-review-star-rating'}) or
                        rev.find('i', class_=re.compile(r'a-star-\d')) or
                        rev.find(class_=re.compile(r'review-rating'))
                    )
                    if rating_elem:
                        rating_text = rating_elem.get_text(strip=True)
                        match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                        if match:
                            try:
                                rating = float(match.group(1))
                            except ValueError:
                                pass
                    
                    # 2. Title
                    title_elem = (
                        rev.find(attrs={'data-hook': 'reviewTitle'}) or
                        rev.find(attrs={'data-hook': 'review-title'})
                    )
                    title_text = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # 3. Body text
                    body_elem = (
                        rev.find(attrs={'data-hook': 'reviewRichContentContainer'}) or
                        rev.find(attrs={'data-hook': 'reviewText'}) or
                        rev.find(attrs={'data-hook': 'review-body'}) or
                        rev.find(class_=re.compile(r'review-text', re.I))
                    )
                    if body_elem:
                        # Decompose collapsible teaser elements
                        for teaser in body_elem.find_all(class_=re.compile(r'a-hidden|a-teaser', re.I)):
                            teaser.decompose()
                        body_text = body_elem.get_text(separator=' ', strip=True)
                    else:
                        body_text = ""
                    
                    full_text = (title_text + '. ' + body_text).strip(' .') if title_text and body_text else (body_text or title_text)
                    # Normalize excessive spaces
                    full_text = re.sub(r'\s+', ' ', full_text).strip()
                    
                    if full_text and len(full_text) >= 3:
                        reviews.append({
                            'review_text': full_text,
                            'rating': rating,
                            'product_name': meta["product_name"]
                        })
                    
                    if len(reviews) >= 50:
                        break
                except Exception:
                    continue
            
            if reviews:
                return (
                    True,
                    f"Successfully extracted {len(reviews)} genuine reviews directly from Amazon for '{meta['product_name']}'.",
                    reviews,
                    meta
                )
                
            # If no reviews found with this header, try next variant
            if h_idx < len(header_variants) - 1:
                continue
                
            return (
                False,
                f"Connected to product page '{meta['product_name']}', but review elements were dynamically loaded by Amazon via JavaScript. "
                "In strict compliance with our data authenticity policy, no fake or extra reviews were added. "
                "Please click 'View Product on Amazon' and export genuine customer reviews to CSV for analysis.",
                None,
                meta
            )
            
        except requests.exceptions.Timeout:
            if h_idx < len(header_variants) - 1:
                continue
            return (
                False,
                "The connection to Amazon timed out. Please check your internet connection or use the CSV upload option.",
                None,
                meta
            )
        except requests.exceptions.RequestException as e:
            if h_idx < len(header_variants) - 1:
                continue
            return (
                False,
                f"Network communication error with Amazon: {str(e)}. Please use the CSV upload option.",
                None,
                meta
            )
        except Exception as e:
            return (
                False,
                f"Unexpected error while fetching reviews: {str(e)}. Please use the CSV upload option.",
                None,
                meta
            )
            
    return (
        False,
        "Unable to fetch reviews directly from Amazon. Please use the CSV upload option.",
        None,
        meta
    )


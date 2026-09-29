"""
Database module for Amazon Review Insight Pro
Handles SQLite database operations for storing and retrieving review data.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple


# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'reviews.db')


def init_db() -> bool:
    """
    Initialize the database and create the reviews table if it doesn't exist.
    
    Why: Ensures the database structure is ready before any operations.
    
    Input: None
    
    Output: bool - True if successful, False if failed
    """
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                review_text TEXT NOT NULL,
                rating REAL,
                sentiment TEXT,
                polarity REAL,
                subjectivity REAL,
                suspicion_score INTEGER,
                classification TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


def insert_review(review_data: Dict) -> Optional[int]:
    """
    Insert a single review into the database.
    
    Why: Save individual reviews with their analysis results.
    
    Input: review_data (Dict) - Dictionary containing review fields
    
    Output: Optional[int] - ID of inserted review, or None if failed
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reviews 
            (product_name, review_text, rating, sentiment, polarity, subjectivity, 
             suspicion_score, classification, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            review_data.get('product_name', ''),
            review_data.get('review_text', ''),
            review_data.get('rating'),
            review_data.get('sentiment'),
            review_data.get('polarity'),
            review_data.get('subjectivity'),
            review_data.get('suspicion_score'),
            review_data.get('classification'),
            datetime.now().isoformat()
        ))
        
        review_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return review_id
    except Exception as e:
        print(f"Error inserting review: {e}")
        return None


def insert_reviews(reviews_list: List[Dict]) -> int:
    """
    Insert multiple reviews into the database in bulk.
    
    Why: Efficiently save multiple reviews from CSV uploads.
    
    Input: reviews_list (List[Dict]) - List of review dictionaries
    
    Output: int - Number of successfully inserted reviews
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        inserted_count = 0
        for review_data in reviews_list:
            cursor.execute('''
                INSERT INTO reviews 
                (product_name, review_text, rating, sentiment, polarity, subjectivity, 
                 suspicion_score, classification, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                review_data.get('product_name', ''),
                review_data.get('review_text', ''),
                review_data.get('rating'),
                review_data.get('sentiment'),
                review_data.get('polarity'),
                review_data.get('subjectivity'),
                review_data.get('suspicion_score'),
                review_data.get('classification'),
                datetime.now().isoformat()
            ))
            inserted_count += 1
        
        conn.commit()
        conn.close()
        return inserted_count
    except Exception as e:
        print(f"Error inserting reviews: {e}")
        return 0


def get_reviews(product_name: Optional[str] = None) -> List[Dict]:
    """
    Retrieve reviews from the database, optionally filtered by product.
    
    Why: Load reviews for dashboard and data display.
    
    Input: product_name (Optional[str]) - Filter by specific product, or None for all
    
    Output: List[Dict] - List of review dictionaries
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if product_name:
            cursor.execute('''
                SELECT * FROM reviews WHERE product_name = ? ORDER BY created_at DESC
            ''', (product_name,))
        else:
            cursor.execute('''
                SELECT * FROM reviews ORDER BY created_at DESC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error getting reviews: {e}")
        return []


def delete_review(review_id: int) -> bool:
    """
    Delete a specific review by ID.
    
    Why: Allow users to remove individual reviews.
    
    Input: review_id (int) - ID of the review to delete
    
    Output: bool - True if successful, False if failed
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM reviews WHERE id = ?', (review_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting review: {e}")
        return False


def clear_all() -> bool:
    """
    Delete all reviews from the database.
    
    Why: Allow users to reset the entire dataset.
    
    Input: None
    
    Output: bool - True if successful, False if failed
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM reviews')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error clearing database: {e}")
        return False


def get_products() -> List[str]:
    """
    Get list of unique product names from the database.
    
    Why: Populate product selector dropdown in dashboard.
    
    Input: None
    
    Output: List[str] - List of unique product names
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT product_name FROM reviews ORDER BY product_name')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows if row[0]]
    except Exception as e:
        print(f"Error getting products: {e}")
        return []


def get_review_count() -> int:
    """
    Get total number of reviews in the database.
    
    Why: Display metrics and handle empty states.
    
    Input: None
    
    Output: int - Total count of reviews
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM reviews')
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    except Exception as e:
        print(f"Error getting review count: {e}")
        return 0

"""
Database module for Amazon Review Insight Pro Analyzer
Handles SQLite database operations for user authentication, reviews storage,
and user-scoped analysis history.
"""

import sqlite3
import os
import hashlib
import secrets
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple


# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'reviews.db')


def get_db_connection() -> sqlite3.Connection:
    """
    Get a SQLite database connection with row factory, WAL mode, and busy timeout.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash a password securely using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    
    Why: NIST-approved secure cryptographic password storage.
    
    Input: password (str), optional salt (str)
    Output: Tuple[str, str] - (password_hash_hex, salt_hex)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return key.hex(), salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """
    Verify a password against stored salt and hash using constant-time comparison.
    """
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, expected_hash)


def init_db() -> bool:
    """
    Initialize database schema with users, reviews, and upload_history tables.
    Also handles safe schema migrations for existing databases.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT
            )
        ''')
        
        # 2. Reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                product_name TEXT NOT NULL,
                review_text TEXT NOT NULL,
                rating REAL,
                sentiment TEXT,
                polarity REAL,
                subjectivity REAL,
                suspicion_score INTEGER,
                classification TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Check if reviews table needs user_id migration
        cursor.execute("PRAGMA table_info(reviews)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'user_id' not in columns:
            cursor.execute("ALTER TABLE reviews ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
        
        # 3. Upload History table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upload_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                source_name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                product_name TEXT,
                total_reviews INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Create helpful indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(user_id, product_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_user_id ON upload_history(user_id)")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        if conn:
            conn.close()


# ==========================================
# User Authentication Functions
# ==========================================

def register_user(username: str, email: str, password: str) -> Tuple[bool, str, Optional[int]]:
    """
    Register a new user with secure password hashing.
    
    Validates:
    - Username length >= 3, alphanumeric and underscores
    - Valid email format
    - Password length >= 6
    """
    username = username.strip()
    email = email.strip().lower()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long.", None
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores.", None
    
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        return False, "Please provide a valid email address.", None
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long.", None
    
    pwd_hash, salt = hash_password(password)
    now_str = datetime.now().isoformat()
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, salt, created_at, last_login)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, email, pwd_hash, salt, now_str, now_str))
        
        user_id = cursor.lastrowid
        conn.commit()
        return True, "Account created successfully! Please sign in.", user_id
    except sqlite3.IntegrityError as e:
        err_msg = str(e).lower()
        if 'username' in err_msg:
            return False, "This username is already taken. Please choose another.", None
        elif 'email' in err_msg:
            return False, "An account with this email already exists.", None
        else:
            return False, "Username or email is already registered.", None
    except Exception as e:
        return False, f"Registration error: {str(e)}", None
    finally:
        if conn:
            conn.close()


def authenticate_user(username_or_email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Authenticate user by username or email. Updates last_login on success.
    """
    identifier = username_or_email.strip()
    if not identifier or not password:
        return False, "Please enter both username/email and password.", None
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, salt, created_at
            FROM users
            WHERE username = ? OR email = ?
        ''', (identifier, identifier.lower()))
        
        user = cursor.fetchone()
        if not user:
            return False, "Invalid username/email or password.", None
        
        user_dict = dict(user)
        if not verify_password(password, user_dict['salt'], user_dict['password_hash']):
            return False, "Invalid username/email or password.", None
        
        # Update last_login
        now_str = datetime.now().isoformat()
        cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_str, user_dict['id']))
        conn.commit()
        
        # Return sanitized user data without sensitive hashes
        return True, "Login successful!", {
            'id': user_dict['id'],
            'username': user_dict['username'],
            'email': user_dict['email'],
            'created_at': user_dict['created_at']
        }
    except Exception as e:
        return False, f"Authentication error: {str(e)}", None
    finally:
        if conn:
            conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Retrieve user details by user ID (excluding sensitive credentials)."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, created_at, last_login FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception:
        return None
    finally:
        if conn:
            conn.close()


def reset_user_password(username_or_email: str, new_password: str) -> Tuple[bool, str]:
    """
    Reset a user's password given their username or email.
    """
    ident = username_or_email.strip()
    if not ident:
        return False, "Please enter your username or email address."
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."
    
    pwd_hash, salt = hash_password(new_password)
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET password_hash = ?, salt = ?
            WHERE username = ? OR email = ?
        ''', (pwd_hash, salt, ident, ident.lower()))
        if cursor.rowcount > 0:
            conn.commit()
            return True, "Password reset successfully! You can now sign in with your new password."
        else:
            return False, "No account was found matching that username or email address."
    except Exception as e:
        return False, f"Password reset error: {str(e)}"
    finally:
        if conn:
            conn.close()



# ==========================================
# User-Scoped Review Operations
# ==========================================

def insert_review(user_id: int, review_data: Dict) -> Optional[int]:
    """
    Insert a single review for a specific user into the database.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reviews 
            (user_id, product_name, review_text, rating, sentiment, polarity, subjectivity, 
             suspicion_score, classification, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            review_data.get('product_name', 'Unknown Product'),
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
        return review_id
    except Exception as e:
        print(f"Error inserting review: {e}")
        return None
    finally:
        if conn:
            conn.close()


def insert_reviews(user_id: int, reviews_list: List[Dict], source_name: str = "CSV Upload", source_type: str = "csv") -> int:
    """
    Insert multiple reviews for a specific user and log to upload history.
    """
    if not reviews_list:
        return 0
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now_str = datetime.now().isoformat()
        inserted_count = 0
        products_seen = set()
        
        for review_data in reviews_list:
            prod_name = review_data.get('product_name', 'Unknown Product')
            products_seen.add(prod_name)
            cursor.execute('''
                INSERT INTO reviews 
                (user_id, product_name, review_text, rating, sentiment, polarity, subjectivity, 
                 suspicion_score, classification, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                prod_name,
                review_data.get('review_text', ''),
                review_data.get('rating'),
                review_data.get('sentiment'),
                review_data.get('polarity'),
                review_data.get('subjectivity'),
                review_data.get('suspicion_score'),
                review_data.get('classification'),
                now_str
            ))
            inserted_count += 1
        
        # Log to upload history
        prod_summary = ", ".join(list(products_seen)[:3])
        if len(products_seen) > 3:
            prod_summary += f" +{len(products_seen) - 3} more"
            
        cursor.execute('''
            INSERT INTO upload_history
            (user_id, source_name, source_type, product_name, total_reviews, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, source_name, source_type, prod_summary, inserted_count, now_str))
        
        conn.commit()
        return inserted_count
    except Exception as e:
        print(f"Error inserting reviews: {e}")
        return 0
    finally:
        if conn:
            conn.close()


def get_reviews(user_id: int, product_name: Optional[str] = None) -> List[Dict]:
    """
    Retrieve reviews for a specific user, optionally filtered by product.
    Guarantees isolation: Never returns reviews belonging to other users.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if product_name and product_name != "All Products":
            cursor.execute('''
                SELECT * FROM reviews 
                WHERE user_id = ? AND product_name = ? 
                ORDER BY id DESC
            ''', (user_id, product_name))
        else:
            cursor.execute('''
                SELECT * FROM reviews 
                WHERE user_id = ? 
                ORDER BY id DESC
            ''', (user_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error getting reviews: {e}")
        return []
    finally:
        if conn:
            conn.close()


def delete_review(user_id: int, review_id: int) -> bool:
    """
    Delete a specific review by ID, ensuring it belongs to the authenticated user.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM reviews WHERE id = ? AND user_id = ?', (review_id, user_id))
        rows_affected = cursor.rowcount
        
        conn.commit()
        return rows_affected > 0
    except Exception as e:
        print(f"Error deleting review: {e}")
        return False
    finally:
        if conn:
            conn.close()


def clear_all(user_id: int) -> bool:
    """
    Delete all reviews belonging to a specific user.
    Does NOT touch other users' data.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM reviews WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM upload_history WHERE user_id = ?', (user_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error clearing database: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_products(user_id: int) -> List[str]:
    """
    Get list of unique product names analyzed by a specific user.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT product_name 
            FROM reviews 
            WHERE user_id = ? AND product_name IS NOT NULL AND product_name != ''
            ORDER BY product_name
        ''', (user_id,))
        
        rows = cursor.fetchall()
        return [row[0] for row in rows if row[0]]
    except Exception as e:
        print(f"Error getting products: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_review_count(user_id: int) -> int:
    """
    Get total number of reviews analyzed by a specific user.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM reviews WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"Error getting review count: {e}")
        return 0
    finally:
        if conn:
            conn.close()


def get_user_history(user_id: int) -> List[Dict]:
    """
    Retrieve upload and analysis history for a specific user.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM upload_history 
            WHERE user_id = ? 
            ORDER BY id DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error getting user history: {e}")
        return []
    finally:
        if conn:
            conn.close()


def delete_history_item(user_id: int, history_id: int) -> bool:
    """
    Delete a specific history entry belonging to the user.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM upload_history WHERE id = ? AND user_id = ?', (history_id, user_id))
        rows_affected = cursor.rowcount
        conn.commit()
        return rows_affected > 0
    except Exception as e:
        print(f"Error deleting history item: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_user_product_summary(user_id: int) -> List[Dict]:
    """
    Get aggregated analysis summary for all products analyzed by a user.
    Includes total reviews, average rating, sentiment counts, and last analyzed timestamp.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                product_name,
                COUNT(*) as total_reviews,
                AVG(CASE WHEN rating IS NOT NULL THEN rating END) as avg_rating,
                SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END) as negative_count,
                SUM(CASE WHEN sentiment = 'Neutral' THEN 1 ELSE 0 END) as neutral_count,
                SUM(CASE WHEN classification = 'Genuine-looking' THEN 1 ELSE 0 END) as genuine_count,
                SUM(CASE WHEN classification = 'Suspicious' THEN 1 ELSE 0 END) as suspicious_count,
                MAX(created_at) as last_analyzed
            FROM reviews
            WHERE user_id = ? AND product_name IS NOT NULL AND product_name != ''
            GROUP BY product_name
            ORDER BY last_analyzed DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error getting product summary: {e}")
        return []
    finally:
        if conn:
            conn.close()


def delete_product_reviews(user_id: int, product_name: str) -> bool:
    """
    Delete all reviews for a specific product belonging to the user.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reviews WHERE user_id = ? AND product_name = ?', (user_id, product_name))
        rev_count = cursor.rowcount
        cursor.execute('DELETE FROM upload_history WHERE user_id = ? AND product_name = ?', (user_id, product_name))
        hist_count = cursor.rowcount
        conn.commit()
        return (rev_count > 0 or hist_count > 0)
    except Exception as e:
        print(f"Error deleting product reviews: {e}")
        return False
    finally:
        if conn:
            conn.close()



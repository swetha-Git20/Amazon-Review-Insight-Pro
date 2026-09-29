"""
Amazon Review Insight Pro - Main Application
A college project for analyzing Amazon product reviews with sentiment analysis and fake review detection.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import spacy
from io import StringIO

# Import project modules
from database.database import init_db, get_reviews, get_products, delete_review, clear_all, insert_review, insert_reviews, get_review_count
from services.sentiment import analyze_sentiment
from services.review_analyzer import calculate_suspicion_score, get_all_rule_descriptions
from services.data_processor import validate_csv, clean_dataframe, limit_reviews, process_reviews_batch, load_sample_csv, get_sample_csv_path
from services.review_fetcher import fetch_reviews_from_url
from utils.helpers import (
    inject_custom_css, metric_card, sentiment_badge, status_badge, info_box, 
    empty_state, display_suspicion_indicators, display_rating_stars, get_color_palette
)

# Page configuration
st.set_page_config(
    page_title="Amazon Review Insight Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()

# Load spaCy model with fallback
@st.cache_resource
def load_spacy_model():
    """
    Load spaCy model for keyword extraction.
    
    Why: Cache the model to avoid reloading on every interaction.
    
    Input: None
    
    Output: spaCy model or None if unavailable
    """
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        try:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True, capture_output=True)
            return spacy.load("en_core_web_sm")
        except:
            return None

nlp = load_spacy_model()

# Load sample CSV with caching
@st.cache_data
def get_sample_data():
    """
    Load sample review data with caching.
    
    Why: Cache to avoid reloading the same file repeatedly.
    
    Input: None
    
    Output: pd.DataFrame - Sample reviews
    """
    return load_sample_csv()

# Inject custom CSS
inject_custom_css()

# Session state for navigation
if 'page' not in st.session_state:
    st.session_state.page = 'Dashboard'

# Custom sidebar navigation
def render_sidebar():
    """
    Render custom sidebar with navigation buttons.
    
    Why: Provide consistent navigation matching the Stitch design.
    
    Input: None
    
    Output: None (renders sidebar in Streamlit)
    """
    with st.sidebar:
        st.markdown("### 📊 Review Insight Pro")
        st.markdown("---")
        
        # Navigation buttons
        pages = [
            ('Dashboard', '📈'),
            ('Review Analyzer', '🔍'),
            ('Review Data', '📋'),
            ('Analytics', '📊'),
            ('About Project', 'ℹ️')
        ]
        
        for page_name, icon in pages:
            if st.button(f"{icon} {page_name}", key=f"nav_{page_name}", use_container_width=True):
                st.session_state.page = page_name
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📌 Quick Stats")
        total_reviews = get_review_count()
        st.metric("Total Reviews", total_reviews)
        
        products = get_products()
        st.metric("Products", len(products))

# Render Dashboard page
def render_dashboard():
    """
    Render the Dashboard page with metrics and charts.
    
    Why: Provide overview of analyzed reviews with visual insights.
    
    Input: None
    
    Output: None (renders dashboard in Streamlit)
    """
    st.title("📈 Dashboard")
    st.markdown("Overview of the analyzed product reviews")
    
    # Get all reviews
    all_reviews = get_reviews()
    
    if not all_reviews:
        empty_state(
            "No reviews analyzed yet",
            "Import or select a product dataset to start uncovering deep review insights.",
            "Go to Review Analyzer",
            lambda: setattr(st.session_state, 'page', 'Review Analyzer')
        )
        return
    
    # Get products for selector
    products = get_products()
    selected_product = st.selectbox("Select Product", ["All Products"] + products, key="dashboard_product")
    
    # Filter reviews by product
    if selected_product != "All Products":
        reviews = [r for r in all_reviews if r['product_name'] == selected_product]
    else:
        reviews = all_reviews
    
    df = pd.DataFrame(reviews)
    
    # Calculate metrics
    total = len(df)
    avg_rating = df['rating'].mean() if total > 0 else 0
    positive = len(df[df['sentiment'] == 'Positive'])
    negative = len(df[df['sentiment'] == 'Negative'])
    neutral = len(df[df['sentiment'] == 'Neutral'])
    genuine = len(df[df['classification'] == 'Genuine-looking'])
    suspicious = len(df[df['classification'] == 'Suspicious'])
    
    # Display metric cards
    col1, col2 = st.columns(2)
    with col1:
        metric_card("Total Reviews", str(total), "Analyzed dataset", "💬")
        metric_card("Average Rating", f"{avg_rating:.1f} / 5", "Customer satisfaction", "⭐")
    with col2:
        metric_card("Positive Reviews", str(positive), f"{positive/total*100:.0f}%" if total > 0 else "0%", "😊", "success")
        metric_card("Negative Reviews", str(negative), f"{negative/total*100:.0f}%" if total > 0 else "0%", "😞", "error")
    
    col3, col4 = st.columns(2)
    with col3:
        metric_card("Neutral Reviews", str(neutral), f"{neutral/total*100:.0f}%" if total > 0 else "0%", "😐", "warning")
        metric_card("Genuine-looking", str(genuine), f"{genuine/total*100:.0f}%" if total > 0 else "0%", "✅", "info")
    with col4:
        metric_card("Suspicious", str(suspicious), f"{suspicious/total*100:.0f}%" if total > 0 else "0%", "⚠️", "suspicious")
    
    # Generate summary insight
    if total > 0:
        if positive > negative and positive > neutral:
            summary = "Most customers gave positive feedback."
        elif negative > positive and negative > neutral:
            summary = "Most customers expressed negative sentiment."
        elif neutral > positive and neutral > negative:
            summary = "Most customer reviews are neutral in tone."
        else:
            summary = "Customer feedback is mixed across sentiments."
        
        if suspicious > 0:
            summary += f" {suspicious} review(s) show suspicious patterns pointing towards repetitive phrasing or extreme language."
        
        info_box(summary, "info")
    
    # Display charts
    colors = get_color_palette()
    
    # Sentiment Distribution
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sentiment Distribution")
        sentiment_counts = df['sentiment'].value_counts()
        fig_sentiment = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            color=sentiment_counts.index,
            color_discrete_map={'Positive': colors['positive'], 'Negative': colors['negative'], 'Neutral': colors['neutral']},
            hole=0.4
        )
        fig_sentiment.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_sentiment, use_container_width=True)
    
    with col2:
        st.subheader("Rating Distribution")
        rating_counts = df['rating'].value_counts().sort_index()
        fig_rating = px.bar(
            x=rating_counts.index,
            y=rating_counts.values,
            labels={'x': 'Rating', 'y': 'Count'},
            color=rating_counts.index,
            color_continuous_scale=[colors['error'], colors['warning'], colors['neutral'], colors['primary'], colors['success']]
        )
        fig_rating.update_layout(showlegend=False)
        st.plotly_chart(fig_rating, use_container_width=True)
    
    # Genuine vs Suspicious
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Genuine vs Suspicious")
        classification_counts = df['classification'].value_counts()
        fig_classification = px.pie(
            values=classification_counts.values,
            names=classification_counts.index,
            color=classification_counts.index,
            color_discrete_map={'Genuine-looking': colors['genuine'], 'Suspicious': colors['suspicious']},
            hole=0.4
        )
        fig_classification.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_classification, use_container_width=True)
    
    with col4:
        st.subheader("Rating vs Sentiment")
        sentiment_rating = pd.crosstab(df['sentiment'], df['rating'])
        fig_matrix = px.imshow(
            sentiment_rating,
            labels=dict(x="Rating", y="Sentiment", color="Count"),
            color_continuous_scale='Blues'
        )
        fig_classification.update_layout(showlegend=False)
        st.plotly_chart(fig_matrix, use_container_width=True)

# Render Review Analyzer page
def render_analyzer():
    """
    Render the Review Analyzer page with single review and batch upload tabs.
    
    Why: Provide tools for analyzing individual reviews and batch processing.
    
    Input: None
    
    Output: None (renders analyzer in Streamlit)
    """
    st.title("🔍 Review Analyzer")
    
    # Tab navigation
    tab1, tab2 = st.tabs(["Analyze One Review", "Upload CSV / Product URL"])
    
    # Tab 1: Analyze One Review
    with tab1:
        st.subheader("Analyze a Single Review")
        
        # Input
        review_text = st.text_area("Enter a review", height=150, placeholder="I really liked this product. The quality is excellent.")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            product_name = st.text_input("Product Name (optional)", placeholder="UltraSonic Wireless Earbuds Pro")
        with col2:
            st.write("")
            st.write("")
            save_to_db = st.checkbox("Save to database", value=True)
        
        # Buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Analyze Review", use_container_width=True):
                if review_text.strip():
                    # Analyze sentiment
                    sentiment_result = analyze_sentiment(review_text)
                    
                    # Analyze suspicion
                    existing_reviews = get_reviews()
                    existing_texts = [r['review_text'] for r in existing_reviews]
                    suspicion_result = calculate_suspicion_score(review_text, existing_texts)
                    
                    # Display results
                    st.success("Analysis Complete")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Sentiment:** {sentiment_badge(sentiment_result['sentiment'])}")
                        st.markdown(f"**Polarity:** {sentiment_result['polarity']}")
                        st.markdown(f"**Subjectivity:** {sentiment_result['subjectivity']}")
                    with col2:
                        st.markdown(f"**Classification:** {status_badge(suspicion_result['classification'])}")
                        st.markdown(f"**Suspicion Score:** {suspicion_result['suspicion_score']}/7")
                    
                    # Display suspicion indicators
                    all_rules = get_all_rule_descriptions()
                    display_suspicion_indicators(suspicion_result['triggered_rules'], all_rules)
                    
                    # Save to database if requested
                    if save_to_db:
                        review_data = {
                            'product_name': product_name if product_name.strip() else 'Unknown Product',
                            'review_text': review_text,
                            'rating': None,
                            'sentiment': sentiment_result['sentiment'],
                            'polarity': sentiment_result['polarity'],
                            'subjectivity': sentiment_result['subjectivity'],
                            'suspicion_score': suspicion_result['suspicion_score'],
                            'classification': suspicion_result['classification']
                        }
                        insert_review(review_data)
                        st.success("Review saved to database")
                else:
                    st.error("Please enter a review text")
        
        with col2:
            if st.button("Use Sample", use_container_width=True):
                st.session_state.sample_review = "Absolute game changer! The audio clarity is phenomenal and the battery easily lasts all day. Highly recommended!"
                st.rerun()
        
        with col3:
            if st.button("Clear", use_container_width=True):
                st.session_state.sample_review = ""
                st.rerun()
        
        # Display sample if set
        if 'sample_review' in st.session_state and st.session_state.sample_review:
            st.text_area("Sample Review", st.session_state.sample_review, height=150, key="sample_display")
    
    # Tab 2: Upload CSV / Product URL
    with tab2:
        st.subheader("Upload CSV or Fetch from URL")
        
        # CSV Upload
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        
        if uploaded_file:
            # Read CSV
            try:
                df = pd.read_csv(uploaded_file)
                
                # Validate CSV
                is_valid, error_msg = validate_csv(df)
                if not is_valid:
                    st.error(error_msg)
                    return
                
                # Show preview
                st.write("Preview of first 5 rows:")
                st.dataframe(df.head())
                
                # Clean and limit
                df_clean = clean_dataframe(df)
                df_limited, was_limited = limit_reviews(df_clean)
                
                if was_limited:
                    st.warning(f"Only first {MAX_REVIEWS := 50} reviews will be analyzed (maximum limit).")
                
                # Analyze
                if st.button("Analyze Reviews", use_container_width=True):
                    with st.spinner("Analyzing reviews..."):
                        processed = process_reviews_batch(df_limited, analyze_sentiment, calculate_suspicion_score)
                        
                        if processed:
                            # Insert into database
                            inserted = insert_reviews(processed)
                            st.success(f"Successfully analyzed and saved {inserted} reviews to database")
                            st.info("Go to Dashboard to see results")
                        else:
                            st.error("No valid reviews to analyze")
            
            except Exception as e:
                st.error(f"Error processing CSV: {str(e)}")
        
        # Download sample CSV
        st.markdown("---")
        st.markdown("### 📥 Download Sample CSV")
        if st.button("Download Sample CSV", use_container_width=True):
            sample_df = get_sample_data()
            csv = sample_df.to_csv(index=False)
            st.download_button(
                label="Download sample_reviews.csv",
                data=csv,
                file_name="sample_reviews.csv",
                mime="text/csv"
            )
        
        # Product URL fetcher
        st.markdown("---")
        st.markdown("### 🔗 Fetch from Amazon URL")
        url = st.text_input("Amazon Product URL", placeholder="https://www.amazon.com/dp/B08N5WRWNW")
        
        if st.button("Fetch Reviews", use_container_width=True):
            if url.strip():
                with st.spinner("Fetching reviews..."):
                    success, message, reviews = fetch_reviews_from_url(url)
                    
                    if success:
                        st.success(message)
                        
                        # Convert to DataFrame and process
                        df = pd.DataFrame(reviews)
                        df_clean = clean_dataframe(df)
                        df_limited, was_limited = limit_reviews(df_clean)
                        
                        if was_limited:
                            st.warning(f"Only first {MAX_REVIEWS := 50} reviews will be analyzed (maximum limit).")
                        
                        # Analyze
                        processed = process_reviews_batch(df_limited, analyze_sentiment, calculate_suspicion_score)
                        
                        if processed:
                            inserted = insert_reviews(processed)
                            st.success(f"Successfully analyzed and saved {inserted} reviews to database")
                        else:
                            st.error("No valid reviews to analyze")
                    else:
                        st.error(message)
            else:
                st.error("Please enter a valid Amazon URL")

# Render Review Data page
def render_data():
    """
    Render the Review Data page with filtering and table view.
    
    Why: Allow users to browse, filter, and manage stored reviews.
    
    Input: None
    
    Output: None (renders data page in Streamlit)
    """
    st.title("📋 Review Data")
    st.markdown("Browse, filter, and manage saved reviews")
    
    # Get all reviews
    all_reviews = get_reviews()
    
    if not all_reviews:
        empty_state(
            "No reviews in database",
            "Upload or analyze reviews to populate the database.",
            "Go to Review Analyzer",
            lambda: setattr(st.session_state, 'page', 'Review Analyzer')
        )
        return
    
    df = pd.DataFrame(all_reviews)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("Search reviews", placeholder="Search text or product...")
    with col2:
        product_filter = st.selectbox("Filter by Product", ["All Products"] + get_products())
    with col3:
        sentiment_filter = st.selectbox("Filter by Sentiment", ["All", "Positive", "Negative", "Neutral"])
    
    # Apply filters
    filtered_df = df.copy()
    
    if search:
        filtered_df = filtered_df[
            filtered_df['review_text'].str.contains(search, case=False, na=False) |
            filtered_df['product_name'].str.contains(search, case=False, na=False)
        ]
    
    if product_filter != "All Products":
        filtered_df = filtered_df[filtered_df['product_name'] == product_filter]
    
    if sentiment_filter != "All":
        filtered_df = filtered_df[filtered_df['sentiment'] == sentiment_filter]
    
    # Display filtered count
    st.info(f"Showing {len(filtered_df)} of {len(df)} reviews")
    
    # Display table
    if not filtered_df.empty:
        # Select columns to display
        display_df = filtered_df[[
            'id', 'product_name', 'review_text', 'rating', 'sentiment', 
            'classification', 'suspicion_score', 'created_at'
        ]].copy()
        
        # Add formatting
        display_df['sentiment'] = display_df['sentiment'].apply(lambda x: sentiment_badge(x))
        display_df['classification'] = display_df['classification'].apply(lambda x: status_badge(x))
        display_df['rating'] = display_df['rating'].apply(lambda x: display_rating_stars(x) if pd.notna(x) else 'N/A')
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Download filtered data
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv,
            file_name="filtered_reviews.csv",
            mime="text/csv"
        )
    else:
        st.warning("No reviews match the current filters.")
    
    # Delete operations
    st.markdown("---")
    st.subheader("Manage Data")
    
    col1, col2 = st.columns(2)
    with col1:
        review_id = st.number_input("Delete Review by ID", min_value=1, value=1)
        if st.button("Delete Review", use_container_width=True):
            if delete_review(review_id):
                st.success(f"Review {review_id} deleted successfully")
                st.rerun()
            else:
                st.error(f"Review {review_id} not found")
    
    with col2:
        if st.button("Clear All Data", use_container_width=True):
            if st.session_state.get('confirm_clear', False):
                if clear_all():
                    st.success("All reviews deleted successfully")
                    st.session_state.confirm_clear = False
                    st.rerun()
                else:
                    st.error("Error clearing database")
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm deletion of ALL reviews")

# Render Analytics page
def render_analytics():
    """
    Render the Analytics page with advanced charts and insights.
    
    Why: Provide deeper analysis with keyword extraction and trends.
    
    Input: None
    
    Output: None (renders analytics in Streamlit)
    """
    st.title("📊 Analytics")
    st.markdown("Advanced insights and trend analysis")
    
    # Get all reviews
    all_reviews = get_reviews()
    
    if not all_reviews:
        empty_state(
            "No data to analyze",
            "Upload reviews to generate advanced analytics.",
            "Go to Review Analyzer",
            lambda: setattr(st.session_state, 'page', 'Review Analyzer')
        )
        return
    
    df = pd.DataFrame(all_reviews)
    colors = get_color_palette()
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Polarity", f"{df['polarity'].mean():.3f}")
    with col2:
        st.metric("Avg Subjectivity", f"{df['subjectivity'].mean():.3f}")
    with col3:
        st.metric("Avg Suspicion Score", f"{df['suspicion_score'].mean():.1f}")
    with col4:
        suspicious_pct = (df['classification'] == 'Suspicious').sum() / len(df) * 100
        st.metric("% Suspicious", f"{suspicious_pct:.1f}%")
    
    # Polarity histogram
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Polarity Distribution")
        fig_polarity = px.histogram(df, x='polarity', nbins=20, color_discrete_sequence=[colors['primary']])
        fig_polarity.update_layout(showlegend=False)
        st.plotly_chart(fig_polarity, use_container_width=True)
    
    with col2:
        st.subheader("Suspicion Score Distribution")
        fig_suspicion = px.histogram(df, x='suspicion_score', nbins=8, color_discrete_sequence=[colors['suspicious']])
        fig_suspicion.update_layout(showlegend=False)
        st.plotly_chart(fig_suspicion, use_container_width=True)
    
    # Average polarity by rating
    st.subheader("Average Polarity by Rating")
    polarity_by_rating = df.groupby('rating')['polarity'].mean().reset_index()
    fig_polarity_rating = px.line(polarity_by_rating, x='rating', y='polarity', markers=True)
    fig_polarity_rating.update_layout(showlegend=False)
    st.plotly_chart(fig_polarity_rating, use_container_width=True)
    
    # Sentiment by product
    st.subheader("Sentiment Distribution by Product")
    sentiment_product = pd.crosstab(df['product_name'], df['sentiment'])
    fig_sentiment_product = px.bar(sentiment_product, barmode='group')
    st.plotly_chart(fig_sentiment_product, use_container_width=True)
    
    # Keyword extraction using spaCy
    if nlp:
        st.subheader("Top Keywords in Reviews")
        
        # Extract keywords from positive reviews
        positive_reviews = df[df['sentiment'] == 'Positive']['review_text'].tolist()
        negative_reviews = df[df['sentiment'] == 'Negative']['review_text'].tolist()
        
        def extract_keywords(reviews, top_n=10):
            """Extract top keywords from reviews using spaCy."""
            if not reviews:
                return []
            
            all_text = ' '.join(reviews)
            doc = nlp(all_text)
            
            # Filter for nouns and adjectives, remove stopwords and punctuation
            keywords = [
                token.text.lower() for token in doc 
                if (token.pos_ in ['NOUN', 'ADJ'] and 
                    not token.is_stop and 
                    not token.is_punct and
                    len(token.text) > 2)
            ]
            
            # Count frequency
            from collections import Counter
            keyword_counts = Counter(keywords)
            
            return keyword_counts.most_common(top_n)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 😊 Positive Review Keywords")
            positive_keywords = extract_keywords(positive_reviews)
            if positive_keywords:
                keywords_df = pd.DataFrame(positive_keywords, columns=['Keyword', 'Count'])
                fig_keywords_pos = px.bar(keywords_df, x='Count', y='Keyword', orientation='h', color_discrete_sequence=[colors['success']])
                st.plotly_chart(fig_keywords_pos, use_container_width=True)
            else:
                st.info("No positive reviews found")
        
        with col2:
            st.markdown("### 😞 Negative Review Keywords")
            negative_keywords = extract_keywords(negative_reviews)
            if negative_keywords:
                keywords_df = pd.DataFrame(negative_keywords, columns=['Keyword', 'Count'])
                fig_keywords_neg = px.bar(keywords_df, x='Count', y='Keyword', orientation='h', color_discrete_sequence=[colors['error']])
                st.plotly_chart(fig_keywords_neg, use_container_width=True)
            else:
                st.info("No negative reviews found")
    else:
        info_box("spaCy model not available. Keyword extraction is disabled.", "warning")
    
    # Most suspicious reviews
    st.subheader("Most Suspicious Reviews")
    suspicious_df = df[df['classification'] == 'Suspicious'].sort_values('suspicion_score', ascending=False).head(5)
    if not suspicious_df.empty:
        for _, row in suspicious_df.iterrows():
            with st.expander(f"Suspicion Score: {row['suspicion_score']}/7 - {row['product_name']}"):
                st.markdown(f"**Review:** {row['review_text']}")
                st.markdown(f"**Sentiment:** {sentiment_badge(row['sentiment'])}")
                st.markdown(f"**Rating:** {display_rating_stars(row['rating']) if pd.notna(row['rating']) else 'N/A'}")
    else:
        st.info("No suspicious reviews found")
    
    # Trend bullets
    st.subheader("Key Insights")
    insights = []
    
    if len(df) > 0:
        if df['sentiment'].value_counts().idxmax() == 'Positive':
            insights.append("✅ Overall customer sentiment is positive")
        elif df['sentiment'].value_counts().idxmax() == 'Negative':
            insights.append("❌ Overall customer sentiment is negative")
        else:
            insights.append("😐 Overall customer sentiment is neutral")
        
        suspicious_count = (df['classification'] == 'Suspicious').sum()
        if suspicious_count > len(df) * 0.2:
            insights.append(f"⚠️ High number of suspicious reviews ({suspicious_count} out of {len(df)})")
        else:
            insights.append(f"✅ Low number of suspicious reviews ({suspicious_count} out of {len(df)})")
        
        if df['rating'].mean() >= 4:
            insights.append("⭐ Average rating is high (4+ stars)")
        elif df['rating'].mean() <= 2:
            insights.append("⭐ Average rating is low (2 or fewer stars)")
        else:
            insights.append("⭐ Average rating is moderate (2-4 stars)")
    
    for insight in insights:
        st.markdown(insight)

# Render About Project page
def render_about():
    """
    Render the About Project page with documentation.
    
    Why: Provide project overview, flow diagram, and technical details.
    
    Input: None
    
    Output: None (renders about page in Streamlit)
    """
    st.title("ℹ️ About Project")
    
    # Overview
    st.markdown("## 📖 Overview")
    st.markdown("""
    **Amazon Review Insight Pro** is a college project that analyzes Amazon product reviews to help 
    identify genuine customer feedback versus potentially suspicious or fake reviews. The system 
    uses sentiment analysis and rule-based heuristics to provide insights into review authenticity.
    """)
    
    # Problem Statement
    st.markdown("## 🎯 Problem Statement")
    st.markdown("""
    Online reviews heavily influence purchasing decisions, but fake reviews distort consumer perception. 
    This project aims to provide a simple tool to analyze reviews for suspicious patterns while 
    understanding genuine customer sentiment.
    """)
    
    # Flow Diagram
    st.markdown("## 🔄 System Flow")
    st.markdown("""
    ```
    Product URL / CSV / Manual Review
           ↓
    Data Cleaning & Validation
           ↓
    Sentiment Analysis (TextBlob)
           ↓
    Suspicion Scoring (7 Rules)
           ↓
    Save to SQLite Database
           ↓
    Dashboard & Analytics
    ```
    """)
    
    # Technologies
    st.markdown("## 🛠️ Technologies Used")
    st.markdown("""
    - **Python 3.10+** - Core programming language
    - **Streamlit** - Web application framework
    - **Pandas** - Data manipulation and analysis
    - **TextBlob** - Sentiment analysis
    - **spaCy** - Natural language processing for keyword extraction
    - **SQLite** - Built-in database for data persistence
    - **Plotly** - Interactive data visualization
    - **Requests & BeautifulSoup** - Web scraping (for Amazon URL fetching)
    """)
    
    # How Sentiment is Calculated
    st.markdown("## 📊 How Sentiment is Calculated")
    st.markdown("""
    Sentiment analysis uses **TextBlob** to calculate:
    
    - **Polarity (-1 to 1):** 
      - > 0: Positive sentiment
      - < 0: Negative sentiment  
      - = 0: Neutral sentiment
    
    - **Subjectivity (0 to 1):**
      - 0: Very objective (factual)
      - 1: Very subjective (opinion-based)
    """)
    
    # How Suspicion Scoring Works
    st.markdown("## 🔍 How Suspicion Scoring Works")
    st.markdown("""
    The system uses **7 rule-based heuristics** (each adds 1 point):
    
    1. **Very short review** - Fewer than 5 words
    2. **Excessive repeated words** - One word makes up 30%+ of words
    3. **Excessive capital letters** - More than 50% uppercase
    4. **Too many exclamation marks** - 3 or more
    5. **Repeated promotional phrases** - 2+ phrases from promotional list
    6. **Very extreme language** - 2+ words from extreme language list
    7. **Duplicate/similar text** - Exact duplicate or 85%+ similarity
    
    **Classification:**
    - 0-2 indicators: "Genuine-looking"
    - 3+ indicators: "Suspicious"
    
    ⚠️ **Important:** This is a heuristic analysis and does not prove a review is fake.
    """)
    
    # Limitations
    st.markdown("## ⚠️ Limitations")
    st.markdown("""
    - **Rule-based approach:** May produce false positives/negatives
    - **Amazon scraping:** Often blocked by anti-bot measures; CSV upload recommended
    - **Language support:** Optimized for English reviews only
    - **Context unaware:** Doesn't understand product-specific context
    - **Not legal proof:** Analysis is for educational purposes only
    - **50 review limit:** Performance constraint for batch processing
    """)
    
    # Future Enhancements
    st.markdown("## 🚀 Future Enhancements")
    st.markdown("""
    - Machine learning model for better accuracy
    - Multi-language support
    - Advanced visualization options
    - User authentication and data privacy
    - Real-time review monitoring
    - Integration with multiple e-commerce platforms
    """)

# Main app logic
def main():
    """
    Main application entry point.
    
    Why: Coordinate page rendering and navigation.
    
    Input: None
    
    Output: None (runs Streamlit app)
    """
    # Render sidebar
    render_sidebar()
    
    # Render current page
    page = st.session_state.page
    
    if page == 'Dashboard':
        render_dashboard()
    elif page == 'Review Analyzer':
        render_analyzer()
    elif page == 'Review Data':
        render_data()
    elif page == 'Analytics':
        render_analytics()
    elif page == 'About Project':
        render_about()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()

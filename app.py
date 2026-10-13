"""
Amazon Review Insight Pro Analyzer - Main Application
A professional, multi-user sentiment analysis and review authenticity verification platform.
Featuring top navigation bar, homepage Amazon URL analyzer, real-time product dashboards,
and user-specific analysis history.
"""

import streamlit as st
import pandas as pd
import json
import io
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Import database and authentication functions
from database.database import (
    init_db, register_user, authenticate_user, get_user_by_id, reset_user_password,
    insert_review, insert_reviews, get_reviews, delete_review,
    clear_all, get_products, get_review_count, get_user_history, delete_history_item,
    get_user_product_summary, delete_product_reviews
)

# Import NLP services
from services.sentiment import analyze_sentiment
from services.review_analyzer import calculate_suspicion_score, get_all_rule_descriptions
from services.data_processor import (
    parse_uploaded_file, validate_csv, clean_dataframe,
    limit_reviews, process_reviews_batch, load_sample_csv, MAX_REVIEWS
)
from services.review_fetcher import (
    fetch_reviews_from_url, extract_amazon_details, DEMO_PRODUCTS
)

# Import UI helpers and styling
from utils.helpers import (
    inject_custom_css, metric_card, sentiment_badge, status_badge,
    info_box, empty_state, display_suspicion_indicators,
    display_rating_stars, render_amazon_link_button, get_color_palette, COLORS
)

# Page configuration - Set sidebar collapsed to enable top navigation bar
st.set_page_config(
    page_title="Amazon Review Insight Pro Analyzer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database schema & migrations
init_db()

# Apply custom dark CSS styling & Poppins font
inject_custom_css()

# Session State Initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'Dashboard'
if 'sample_review_text' not in st.session_state:
    st.session_state.sample_review_text = ""
if 'active_product_url' not in st.session_state:
    st.session_state.active_product_url = ""
if 'home_product_url' not in st.session_state:
    st.session_state.home_product_url = ""
if 'active_dashboard_product' not in st.session_state:
    st.session_state.active_dashboard_product = None


# Load spaCy NLP model safely with fallback
@st.cache_resource
def load_spacy_model():
    """Load spaCy model with graceful fallback if model is not installed."""
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:
        return None

nlp_model = load_spacy_model()


# =====================================================================
# Authentication Views (Login & Registration)
# =====================================================================

def render_auth_page():
    """
    Render a professional login and registration page with a sleek dark theme,
    Poppins typography, input validation, and secure password authentication.
    """
    col_center = st.columns([1, 2, 1])[1]
    
    with col_center:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 28px;">
                <div style="font-size: 44px; margin-bottom: 8px;">🛡️</div>
                <h1 style="color: #F8FAFC; font-size: 28px; font-weight: 700; margin: 0 0 6px 0;">
                    Amazon Review Insight Pro
                </h1>
                <div style="color: #6366F1; font-weight: 600; font-size: 15px; letter-spacing: 0.5px;">
                    ANALYZER PLATFORM
                </div>
                <p style="color: #94A3B8; font-size: 14px; margin-top: 8px;">
                    Secure, intelligent sentiment analysis & review authenticity verification
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔐 Sign In", "📝 Create Account", "🔑 Reset Password"])
        
        # TAB 1: SIGN IN
        with auth_tab1:
            st.markdown("##### Welcome Back")
            st.caption("Sign in to access your private reviews, uploaded datasets, and analysis history.")
            
            with st.form("login_form", clear_on_submit=False):
                login_ident = st.text_input("Username or Email", placeholder="e.g., analyst_user or user@example.com")
                login_pwd = st.text_input("Password", type="password", placeholder="Enter your password")
                login_submit = st.form_submit_button("Sign In to Analyzer", use_container_width=True)
                
                if login_submit:
                    if not login_ident.strip() or not login_pwd:
                        st.error("Please provide both your username/email and password.")
                    else:
                        success, message, user_data = authenticate_user(login_ident, login_pwd)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user = user_data
                            st.session_state.page = 'Dashboard'
                            st.success("Authentication successful! Loading dashboard...")
                            st.rerun()
                        else:
                            st.error(message)
            
            # Quick Demo Login Helper for seamless evaluation
            st.markdown("---")
            col_demo1, col_demo2 = st.columns(2)
            with col_demo1:
                if st.button("🔑 Try as Demo User 1", use_container_width=True):
                    register_user("demo_analyst", "demo1@reviewinsight.local", "Password123!")
                    _, _, u_data = authenticate_user("demo_analyst", "Password123!")
                    if u_data:
                        st.session_state.authenticated = True
                        st.session_state.user = u_data
                        st.rerun()
            with col_demo2:
                if st.button("👤 Try as Demo User 2", use_container_width=True):
                    register_user("test_evaluator", "demo2@reviewinsight.local", "Password123!")
                    _, _, u_data = authenticate_user("test_evaluator", "Password123!")
                    if u_data:
                        st.session_state.authenticated = True
                        st.session_state.user = u_data
                        st.rerun()
        
        # TAB 2: CREATE ACCOUNT
        with auth_tab2:
            st.markdown("##### New User Registration")
            st.caption("Create a separate account. All your data, uploads, and history remain strictly private.")
            
            with st.form("register_form", clear_on_submit=False):
                reg_username = st.text_input("Username", placeholder="e.g., alex_insights (alphanumeric, min 3 chars)")
                reg_email = st.text_input("Email Address", placeholder="e.g., alex@company.com")
                reg_pwd = st.text_input("Password", type="password", placeholder="At least 6 characters")
                reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                reg_submit = st.form_submit_button("Create My Account", use_container_width=True)
                
                if reg_submit:
                    if reg_pwd != reg_confirm:
                        st.error("Passwords do not match. Please re-enter your password.")
                    else:
                        success, message, new_user_id = register_user(reg_username, reg_email, reg_pwd)
                        if success:
                            st.success(message)
                            info_box("Account registered successfully! Please click the 'Sign In' tab to log in.", "success")
                        else:
                            st.error(message)

        # TAB 3: RESET PASSWORD
        with auth_tab3:
            st.markdown("##### Reset Account Password")
            st.caption("Forgot your password or want to update it? Enter your username or email and your new password.")
            
            with st.form("reset_pwd_form", clear_on_submit=False):
                reset_ident = st.text_input("Username or Email Address", placeholder="e.g., swetha20 or swetha@gmail.com")
                reset_new_pwd = st.text_input("New Password", type="password", placeholder="At least 6 characters")
                reset_confirm_pwd = st.text_input("Confirm New Password", type="password", placeholder="Re-enter new password")
                reset_submit = st.form_submit_button("Update Password", use_container_width=True)
                
                if reset_submit:
                    if reset_new_pwd != reset_confirm_pwd:
                        st.error("New passwords do not match. Please re-enter.")
                    else:
                        success, message = reset_user_password(reset_ident, reset_new_pwd)
                        if success:
                            st.success(message)
                            info_box("Your password has been updated. Switch to the 'Sign In' tab to log in.", "success")
                        else:
                            st.error(message)


# =====================================================================
# Top Navigation Bar (Requirement 1: Move sidebar menus to top bar)
# =====================================================================

def render_top_navbar():
    """
    Render modern, responsive top navigation bar replacing sidebar menu.
    Displays project branding, page navigation controls, user badge, and logout.
    """
    user = st.session_state.user
    
    # Header row with Logo, Brand, and User Account Badge
    nav_header_html = f"""
    <div class="top-nav-container">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 28px;">🛡️</span>
                <div>
                    <div style="font-weight: 700; font-size: 18px; color: #F8FAFC; line-height: 1.2;">
                        Amazon Review Insight Pro
                    </div>
                    <div style="font-size: 11px; color: #6366F1; font-weight: 600; letter-spacing: 0.5px;">
                        ANALYZER PLATFORM
                    </div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="padding: 6px 14px; background: rgba(30, 41, 59, 0.7); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.08); font-size: 13px; color: #F8FAFC;">
                    👤 <strong>{user['username']}</strong>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(nav_header_html, unsafe_allow_html=True)
    
    # Segmented navigation menu and Sign Out button
    nav_col, logout_col = st.columns([10, 2])
    
    nav_items = [
        "📈 Dashboard",
        "🔍 Review Analyzer",
        "📋 Review Data",
        "📜 Analysis History",
        "📊 Advanced Analytics",
        "ℹ️ About"
    ]
    
    page_map = {
        'Dashboard': "📈 Dashboard",
        'Review Analyzer': "🔍 Review Analyzer",
        'Review Data': "📋 Review Data",
        'Analysis History': "📜 Analysis History",
        'Advanced Analytics': "📊 Advanced Analytics",
        'About Project': "ℹ️ About"
    }
    current_selection = page_map.get(st.session_state.page, "📈 Dashboard")
    
    with nav_col:
        selected_nav = st.segmented_control(
            "Navigation Menu",
            options=nav_items,
            default=current_selection,
            label_visibility="collapsed",
            key="top_navbar_segmented"
        )
        
        reverse_map = {
            "📈 Dashboard": 'Dashboard',
            "🔍 Review Analyzer": 'Review Analyzer',
            "📋 Review Data": 'Review Data',
            "📜 Analysis History": 'Analysis History',
            "📊 Advanced Analytics": 'Advanced Analytics',
            "ℹ️ About": 'About Project'
        }
        if selected_nav and reverse_map.get(selected_nav) != st.session_state.page:
            st.session_state.page = reverse_map[selected_nav]
            st.rerun()
            
    with logout_col:
        if st.button("🚪 Sign Out", key="top_logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.page = 'Dashboard'
            st.rerun()


# =====================================================================
# Page 1: Homepage & Dashboard (Requirements 2, 3, 4, 5)
# =====================================================================

def render_dashboard():
    """
    Render homepage with:
    1. Amazon Product Review Analyzer at the top
    2. Amazon URL input and Analyze Reviews button
    3. Live dashboard with charts, sentiment analysis, and review statistics
    4. Analysis History section showing products analyzed by the logged-in user
    """
    user = st.session_state.user
    user_id = user['id']
    
    # -------------------------------------------------------------
    # HERO SECTION: Amazon Product Review Analyzer at Top (Req 2 & 3)
    # -------------------------------------------------------------
    hero_html = """
    <div class="hero-analyzer-card">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
            <span style="font-size: 32px;">🛒</span>
            <div>
                <h1 style="color: #F8FAFC; margin: 0; font-size: 26px; font-weight: 700; line-height: 1.2;">
                    Amazon Product Review Analyzer
                </h1>
                <div style="color: #818CF8; font-size: 13px; font-weight: 600; margin-top: 2px;">
                    INTELLIGENT SENTIMENT & AUTHENTICITY INTELLIGENCE
                </div>
            </div>
        </div>
        <p style="color: #94A3B8; font-size: 14px; margin: 12px 0 0 0; line-height: 1.5;">
            Paste any Amazon product link below to analyze genuine customer feedback,
            evaluate sentiment polarity, and detect suspicious review patterns.
        </p>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)
    
    # URL Input & Analyze Action (Requirement 3)
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        current_input_val = st.session_state.get('home_product_url', '')
        home_url = st.text_input(
            "Amazon Product URL",
            value=current_input_val,
            placeholder="Paste Amazon product URL (e.g., https://www.amazon.com/dp/B0863TXGM3 or https://www.amazon.in/dp/B07PR1CL3S)",
            label_visibility="collapsed",
            key="home_url_input"
        )
    with col_btn:
        analyze_clicked = st.button("🚀 Analyze Reviews", key="home_analyze_btn", use_container_width=True, type="primary")
    
    # Real-time URL validation and View Product link
    url_details = extract_amazon_details(home_url) if home_url.strip() else None
    
    if home_url.strip() and url_details:
        if url_details["is_valid"]:
            col_v1, col_v2 = st.columns([3, 1])
            with col_v1:
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.25);">
                        <span style="color: #34D399; font-weight: 600; font-size: 13px;">✓ Valid Amazon URL</span>
                        <span style="color: #94A3B8; font-size: 12px;">ASIN: <code>{url_details['asin']}</code> | Domain: {url_details['domain']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_v2:
                render_amazon_link_button(url_details["canonical_url"], "View Product on Amazon")
        else:
            st.warning("⚠️ The URL entered does not contain a recognizable 10-character Amazon ASIN.")
            
    # Quick-select Demo Products row for easy testing
    st.markdown("<div style='color: #94A3B8; font-size: 12px; font-weight: 600; margin: 10px 0 6px 0;'>💡 QUICK SELECT DEMO PRODUCTS:</div>", unsafe_allow_html=True)
    demo_cols = st.columns(4)
    demo_presets = [
        ("boAt Rockerz 450", "https://www.amazon.in/dp/B07PR1CL3S"),
        ("Sony WH-1000XM4", "https://www.amazon.com/dp/B0863TXGM3"),
        ("JBL Tune 510BT", "https://www.amazon.com/dp/B08WM3LMJF"),
        ("UltraSonic Earbuds", "https://www.amazon.com/dp/B0BDHWDR12")
    ]
    for idx, (p_name, p_url) in enumerate(demo_presets):
        with demo_cols[idx]:
            if st.button(f"🎧 {p_name}", key=f"demo_btn_{idx}", use_container_width=True):
                st.session_state.home_product_url = p_url
                # Trigger analysis directly
                with st.spinner(f"Analyzing reviews for {p_name}..."):
                    success, msg, revs, meta = fetch_reviews_from_url(p_url)
                    if success and revs:
                        df_s = pd.DataFrame(revs)
                        df_c = clean_dataframe(df_s)
                        processed = process_reviews_batch(df_c, analyze_sentiment, calculate_suspicion_score)
                        insert_reviews(user_id, processed, source_name=f"Amazon URL ({meta.get('asin', p_name)})", source_type="url")
                        st.session_state.active_dashboard_product = meta.get('product_name', p_name)
                        st.success(f"✓ Analyzed reviews for {p_name}!")
                        st.rerun()
                        
    # Handle manual Analyze Reviews button click (Requirement 4)
    if analyze_clicked:
        if not home_url.strip():
            st.error("Please enter an Amazon product URL to analyze.")
        elif not url_details or not url_details["is_valid"]:
            st.error("Please provide a valid Amazon product URL with a 10-character ASIN.")
        else:
            with st.spinner("Connecting to Amazon and analyzing customer reviews..."):
                success, msg, revs, meta = fetch_reviews_from_url(home_url)
                if success and revs:
                    df_s = pd.DataFrame(revs)
                    df_c = clean_dataframe(df_s)
                    processed = process_reviews_batch(df_c, analyze_sentiment, calculate_suspicion_score)
                    inserted_cnt = insert_reviews(
                        user_id,
                        processed,
                        source_name=f"Amazon URL ({meta.get('asin', 'Product')})",
                        source_type="url"
                    )
                    st.session_state.active_dashboard_product = meta.get('product_name', 'Amazon Product')
                    st.success(f"🎉 Successfully analyzed and stored {inserted_cnt} reviews for '{st.session_state.active_dashboard_product}'!")
                    st.rerun()
                else:
                    info_box(msg, "warning")
    
    st.markdown("---")
    
    # -------------------------------------------------------------
    # DASHBOARD SECTION: Charts, Sentiment, Statistics (Requirement 4)
    # -------------------------------------------------------------
    all_reviews = get_reviews(user_id)
    products = get_products(user_id)
    
    if not all_reviews:
        empty_state(
            "No reviews analyzed in your account yet",
            "Enter an Amazon product link above or select a verified demo product to generate your review dashboard and analytics.",
            None,
            None
        )
    else:
        # Product selector filter
        col_title, col_sel = st.columns([3, 2])
        with col_title:
            st.markdown("### 📈 Analysis Dashboard")
            st.caption("Detailed sentiment metrics, customer ratings, and authenticity breakdown.")
        with col_sel:
            default_index = 0
            # If an active product was just analyzed, set it as default
            active_prod = st.session_state.get('active_dashboard_product')
            prod_options = ["All Products"] + products
            if active_prod and active_prod in prod_options:
                default_index = prod_options.index(active_prod)
                
            selected_product = st.selectbox(
                "Active Product Scope",
                prod_options,
                index=default_index,
                key="home_dashboard_product_filter"
            )
        
        # Filter dataset
        if selected_product != "All Products":
            reviews = [r for r in all_reviews if r['product_name'] == selected_product]
        else:
            reviews = all_reviews
            
        df = pd.DataFrame(reviews)
        total = len(df)
        valid_ratings = df['rating'].dropna()
        avg_rating = valid_ratings.mean() if not valid_ratings.empty else 0.0
        
        positive = len(df[df['sentiment'] == 'Positive'])
        negative = len(df[df['sentiment'] == 'Negative'])
        neutral = len(df[df['sentiment'] == 'Neutral'])
        genuine = len(df[df['classification'] == 'Genuine-looking'])
        suspicious = len(df[df['classification'] == 'Suspicious'])
        
        pos_pct = (positive / total * 100) if total > 0 else 0
        neg_pct = (negative / total * 100) if total > 0 else 0
        gen_pct = (genuine / total * 100) if total > 0 else 0
        sus_pct = (suspicious / total * 100) if total > 0 else 0
        
        # 6 Metric Cards
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("Total Analyzed Reviews", f"{total:,}", f"Scope: {selected_product}", "💬", "primary")
        with c2:
            metric_card("Average Rating", f"{avg_rating:.2f} / 5.0", display_rating_stars(avg_rating), "⭐", "warning")
        with c3:
            metric_card("Positive Feedback", f"{positive:,}", f"{pos_pct:.1f}% positive tone", "😊", "success")
            
        c4, c5, c6 = st.columns(3)
        with c4:
            metric_card("Negative Feedback", f"{negative:,}", f"{neg_pct:.1f}% critical tone", "😞", "error")
        with c5:
            metric_card("Genuine Reviews", f"{genuine:,}", f"{gen_pct:.1f}% authenticity score", "🛡️", "info")
        with c6:
            metric_card("Suspicious Reviews", f"{suspicious:,}", f"{sus_pct:.1f}% triggered 3+ heuristics", "⚠️", "suspicious")
        
        # Executive Review Synthesis
        if total > 0:
            if pos_pct >= 60:
                consensus = "Predominantly Positive. Customers praise quality, performance, and overall value."
            elif neg_pct >= 40:
                consensus = "Predominantly Negative. Critical reviews express dissatisfaction with functionality or durability."
            else:
                consensus = "Balanced / Mixed Sentiment. Opinions are evenly distributed across praise and concerns."
            
            authenticity_note = (
                f"Authenticity is high ({gen_pct:.1f}% genuine-looking reviews)."
                if sus_pct <= 20
                else f"Caution advised: {sus_pct:.1f}% of reviews triggered repetitive phrasing or suspicious patterns."
            )
            
            summary_text = (
                f"**Executive Review Synthesis:** {consensus} "
                f"Out of {total} analyzed reviews for '{selected_product}', the mean rating is {avg_rating:.1f}/5.0. "
                f"{authenticity_note}"
            )
            info_box(summary_text, "info")
        
        # Visualizations (Plotly Dark Mode)
        palette = get_color_palette()
        
        st.markdown("#### 📊 Sentiment & Authenticity Visualizations")
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("##### Sentiment Distribution")
            sentiment_counts = df['sentiment'].value_counts()
            fig_sent = px.pie(
                values=sentiment_counts.values,
                names=sentiment_counts.index,
                color=sentiment_counts.index,
                color_discrete_map={
                    'Positive': palette['positive'],
                    'Negative': palette['negative'],
                    'Neutral': palette['neutral']
                },
                hole=0.45
            )
            fig_sent.update_layout(
                paper_bgcolor=palette['paper_bgcolor'],
                plot_bgcolor=palette['plot_bgcolor'],
                font=dict(family="Poppins", color=palette['font_color']),
                margin=dict(l=10, r=10, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_sent, use_container_width=True)
        
        with col_chart2:
            st.markdown("##### Rating Breakdown")
            rating_df = df[df['rating'].notna()].copy()
            if not rating_df.empty:
                rating_counts = rating_df['rating'].value_counts().sort_index()
                fig_rate = px.bar(
                    x=[f"{r} Star" for r in rating_counts.index],
                    y=rating_counts.values,
                    labels={'x': 'Rating', 'y': 'Review Count'},
                    color=rating_counts.values,
                    color_continuous_scale=[palette['primary'], palette['positive']]
                )
                fig_rate.update_layout(
                    paper_bgcolor=palette['paper_bgcolor'],
                    plot_bgcolor=palette['plot_bgcolor'],
                    font=dict(family="Poppins", color=palette['font_color']),
                    margin=dict(l=10, r=10, t=20, b=20),
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_rate, use_container_width=True)
            else:
                info_box("No numeric star ratings available for this product.", "info")
                
        col_chart3, col_chart4 = st.columns(2)
        
        with col_chart3:
            st.markdown("##### Genuine vs Suspicious Proportion")
            class_counts = df['classification'].value_counts()
            fig_class = px.pie(
                values=class_counts.values,
                names=class_counts.index,
                color=class_counts.index,
                color_discrete_map={
                    'Genuine-looking': palette['genuine'],
                    'Suspicious': palette['suspicious']
                },
                hole=0.45
            )
            fig_class.update_layout(
                paper_bgcolor=palette['paper_bgcolor'],
                plot_bgcolor=palette['plot_bgcolor'],
                font=dict(family="Poppins", color=palette['font_color']),
                margin=dict(l=10, r=10, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_class, use_container_width=True)
        
        with col_chart4:
            st.markdown("##### Suspicion Score Distribution (0-7 Rules)")
            score_counts = df['suspicion_score'].value_counts().sort_index()
            fig_score = px.bar(
                x=[f"Score {s}" for s in score_counts.index],
                y=score_counts.values,
                labels={'x': 'Suspicion Score', 'y': 'Review Count'},
                color_discrete_sequence=[palette['suspicious']]
            )
            fig_score.update_layout(
                paper_bgcolor=palette['paper_bgcolor'],
                plot_bgcolor=palette['plot_bgcolor'],
                font=dict(family="Poppins", color=palette['font_color']),
                margin=dict(l=10, r=10, t=20, b=20)
            )
            st.plotly_chart(fig_score, use_container_width=True)

        # Export Suite
        st.markdown("---")
        st.markdown("#### 📥 Export Analysis Data & Reports")
        
        exp_col1, exp_col2, exp_col3 = st.columns(3)
        with exp_col1:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 Export Dataset (CSV)",
                data=csv_data,
                file_name=f"amazon_reviews_{selected_product.replace(' ', '_').lower()}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with exp_col2:
            report_json = {
                "project": "Amazon Review Insight Pro Analyzer",
                "user": user['username'],
                "product_analyzed": selected_product,
                "export_timestamp": datetime.now().isoformat(),
                "metrics": {
                    "total_reviews": total,
                    "average_rating": round(avg_rating, 2),
                    "positive_reviews": positive,
                    "negative_reviews": negative,
                    "neutral_reviews": neutral,
                    "genuine_reviews": genuine,
                    "suspicious_reviews": suspicious,
                    "authenticity_ratio_percent": round(gen_pct, 1)
                },
                "reviews_sample": reviews[:20]
            }
            json_data = json.dumps(report_json, indent=2).encode('utf-8')
            st.download_button(
                label="📦 Export Summary Report (JSON)",
                data=json_data,
                file_name=f"review_analysis_{selected_product.replace(' ', '_').lower()}.json",
                mime="application/json",
                use_container_width=True
            )
        with exp_col3:
            md_report = f"""# Amazon Review Insight Pro Analyzer - Executive Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
User Account: {user['username']}
Product: {selected_product}

## Executive Summary
- Total Reviews Analyzed: {total}
- Average Rating: {avg_rating:.2f} / 5.0
- Positive Sentiment: {positive} ({pos_pct:.1f}%)
- Negative Sentiment: {negative} ({neg_pct:.1f}%)
- Neutral Sentiment: {neutral}
- Genuine-Looking Reviews: {genuine} ({gen_pct:.1f}%)
- Suspicious Reviews: {suspicious} ({sus_pct:.1f}%)

## Assessment
{consensus}
{authenticity_note}
"""
            st.download_button(
                label="📝 Export Executive Summary (Markdown)",
                data=md_report.encode('utf-8'),
                file_name=f"executive_summary_{selected_product.replace(' ', '_').lower()}.md",
                mime="text/markdown",
                use_container_width=True
            )

    # -------------------------------------------------------------
    # SECTION: Analysis History for Logged-In User (Requirement 5)
    # -------------------------------------------------------------
    st.markdown("---")
    st.markdown(
        f"""
        <div style="margin-top: 10px; margin-bottom: 16px;">
            <h3 style="color: #F8FAFC; margin: 0; font-size: 22px; font-weight: 700;">
                📜 Analysis History ({user['username']})
            </h3>
            <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 13px;">
                Products analyzed by your account. Click 'View Analysis' on any product to load its dashboard instantly.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    product_summaries = get_user_product_summary(user_id)
    
    if not product_summaries:
        info_box("No products in your analysis history yet. Analyze an Amazon product URL above to begin.", "info")
    else:
        for idx, prod in enumerate(product_summaries):
            p_name = prod['product_name']
            total_r = prod['total_reviews']
            avg_r = prod['avg_rating'] if prod['avg_rating'] else 0.0
            pos_c = prod['positive_count'] or 0
            neg_c = prod['negative_count'] or 0
            gen_c = prod['genuine_count'] or 0
            sus_c = prod['suspicious_count'] or 0
            last_ts = prod['last_analyzed'] or "Recently"
            if "T" in str(last_ts):
                last_ts = str(last_ts).split("T")[0]
                
            gen_rate = (gen_c / total_r * 100) if total_r > 0 else 0
            
            # Card for each product in history
            col_info, col_actions = st.columns([8, 3])
            with col_info:
                st.markdown(
                    f"""
                    <div class="history-product-card">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <span style="font-weight: 700; color: #F8FAFC; font-size: 15px;">📦 {p_name}</span>
                            <span style="color: #94A3B8; font-size: 12px;">Analyzed: {last_ts}</span>
                        </div>
                        <div style="display: flex; gap: 16px; margin-top: 8px; font-size: 13px; color: #CBD5E1; flex-wrap: wrap;">
                            <span>💬 <strong>{total_r}</strong> reviews</span>
                            <span>⭐ <strong>{avg_r:.1f}</strong> rating</span>
                            <span>😊 <span style="color: #34D399;">{pos_c}</span> positive</span>
                            <span>😞 <span style="color: #F87171;">{neg_c}</span> negative</span>
                            <span>🛡️ <span style="color: #22D3EE;">{gen_rate:.0f}%</span> genuine</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_actions:
                col_btn_view, col_btn_del = st.columns([2, 1])
                with col_btn_view:
                    if st.button("📊 View Analysis", key=f"hist_view_{idx}", use_container_width=True):
                        st.session_state.active_dashboard_product = p_name
                        st.session_state.page = 'Dashboard'
                        st.rerun()
                with col_btn_del:
                    if st.button("🗑️", key=f"hist_del_{idx}", help=f"Delete {p_name} data", use_container_width=True):
                        delete_product_reviews(user_id, p_name)
                        if st.session_state.get('active_dashboard_product') == p_name:
                            st.session_state.active_dashboard_product = None
                        st.success(f"Deleted {p_name}")
                        st.rerun()


# =====================================================================
# Page 2: Dedicated Review Analyzer (Single + File Upload + Amazon URL)
# =====================================================================

def render_analyzer():
    """
    Render Review Analyzer with 3 dedicated analysis tools:
    1. Single Review Analyzer
    2. File Upload (CSV & Excel with validation, preview & errors)
    3. Amazon Product URL Analyzer (with exact product links & honest handling)
    """
    user = st.session_state.user
    user_id = user['id']
    
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #F8FAFC; margin: 0; font-size: 26px; font-weight: 700;">🔍 Review Analyzer</h1>
            <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 14px;">
                Inspect individual reviews, upload batch datasets, or evaluate Amazon product pages
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    tab_single, tab_upload, tab_amazon = st.tabs([
        "✍️ Single Review Analyzer",
        "📂 Upload Dataset (CSV / Excel)",
        "🛒 Amazon Product URL & Demos"
    ])
    
    # -------------------------------------------------------------
    # TAB 1: SINGLE REVIEW ANALYZER
    # -------------------------------------------------------------
    with tab_single:
        st.markdown("##### Analyze Individual Customer Review")
        st.caption("Evaluate sentiment polarity, subjectivity, and 7 heuristic suspicion indicators.")
        
        default_text = st.session_state.sample_review_text
        single_text = st.text_area(
            "Review Content",
            value=default_text,
            height=140,
            placeholder="Type or paste any customer review here..."
        )
        
        col_p1, col_p2 = st.columns([3, 1])
        with col_p1:
            prod_name_input = st.text_input("Product Name (Optional)", placeholder="e.g., UltraSonic Earbuds Pro")
        with col_p2:
            st.write("")
            st.write("")
            save_single = st.checkbox("Save to my account", value=True)
            
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn1:
            analyze_single_clicked = st.button("🚀 Analyze Review", use_container_width=True, type="primary")
        with col_btn2:
            if st.button("💡 Load Sample Review", use_container_width=True):
                st.session_state.sample_review_text = (
                    "Absolute game changer! The audio clarity is phenomenal and the battery easily lasts all day. Highly recommended! Five stars!"
                )
                st.rerun()
        with col_btn3:
            if st.button("🧹 Clear Input", use_container_width=True):
                st.session_state.sample_review_text = ""
                st.rerun()
                
        if analyze_single_clicked:
            if not single_text.strip():
                st.error("Please enter review text to analyze.")
            else:
                with st.spinner("Executing sentiment & suspicion algorithms..."):
                    sentiment_res = analyze_sentiment(single_text)
                    existing_user_revs = [r['review_text'] for r in get_reviews(user_id)]
                    suspicion_res = calculate_suspicion_score(single_text, existing_user_revs)
                    
                    st.success("Analysis Complete!")
                    
                    res_col1, res_col2 = st.columns(2)
                    with res_col1:
                        st.markdown(
                            f"""
                            <div class="metric-card-dark">
                                <div style="color: #94A3B8; font-size: 13px;">SENTIMENT RESULTS</div>
                                <div style="margin: 8px 0;">{sentiment_badge(sentiment_res['sentiment'])}</div>
                                <div style="color: #E2E8F0; font-size: 14px;"><strong>Polarity:</strong> {sentiment_res['polarity']} (-1 to +1)</div>
                                <div style="color: #E2E8F0; font-size: 14px;"><strong>Subjectivity:</strong> {sentiment_res['subjectivity']} (0 to 1)</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    with res_col2:
                        st.markdown(
                            f"""
                            <div class="metric-card-dark">
                                <div style="color: #94A3B8; font-size: 13px;">AUTHENTICITY RESULTS</div>
                                <div style="margin: 8px 0;">{status_badge(suspicion_res['classification'])}</div>
                                <div style="color: #E2E8F0; font-size: 14px;"><strong>Suspicion Score:</strong> {suspicion_res['suspicion_score']} / 7 rules</div>
                                <div style="color: #94A3B8; font-size: 12px; margin-top: 4px;">Classification: {suspicion_res['classification']}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    all_rules = get_all_rule_descriptions()
                    display_suspicion_indicators(suspicion_res['triggered_rules'], all_rules)
                    
                    if save_single:
                        p_name = prod_name_input.strip() if prod_name_input.strip() else "Manual Analysis"
                        r_data = {
                            'product_name': p_name,
                            'review_text': single_text,
                            'rating': None,
                            'sentiment': sentiment_res['sentiment'],
                            'polarity': sentiment_res['polarity'],
                            'subjectivity': sentiment_res['subjectivity'],
                            'suspicion_score': suspicion_res['suspicion_score'],
                            'classification': suspicion_res['classification']
                        }
                        insert_review(user_id, r_data)
                        st.success(f"Saved to your account under '{p_name}'. Viewable in Dashboard.")
                        
    # -------------------------------------------------------------
    # TAB 2: FILE UPLOAD (CSV & EXCEL)
    # -------------------------------------------------------------
    with tab_upload:
        st.markdown("##### Upload Review Dataset")
        st.markdown(
            """
            <div style="background: rgba(30, 41, 59, 0.4); padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 16px;">
                <div style="color: #F8FAFC; font-weight: 600; font-size: 14px; margin-bottom: 6px;">Supported Formats & Column Specifications:</div>
                <div style="color: #94A3B8; font-size: 13px; line-height: 1.6;">
                    • <strong>Supported Extensions:</strong> <code>.CSV</code>, <code>.XLSX</code>, <code>.XLS</code><br>
                    • <strong>Required Column:</strong> <code>review_text</code> (or aliases: <code>review</code>, <code>text</code>, <code>comment</code>)<br>
                    • <strong>Optional Columns:</strong> <code>rating</code> (1.0 to 5.0), <code>product_name</code><br>
                    • <strong>Batch Processing Limit:</strong> Up to 100 reviews per upload for fast NLP computation
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        uploaded_file = st.file_uploader(
            "Select review data file to upload",
            type=['csv', 'xlsx', 'xls'],
            help="Upload your customer reviews CSV or Excel spreadsheet"
        )
        
        if uploaded_file:
            parse_success, parse_msg, raw_df = parse_uploaded_file(uploaded_file)
            
            if not parse_success:
                st.error(f"❌ {parse_msg}")
            else:
                is_valid, validation_err = validate_csv(raw_df)
                
                if not is_valid:
                    st.error(f"❌ Validation Failed: {validation_err}")
                else:
                    st.success(f"✓ File parsed successfully: Found {len(raw_df)} rows and {len(raw_df.columns)} columns.")
                    
                    st.markdown("###### Preview of Uploaded Data (First 5 Rows)")
                    st.dataframe(raw_df.head(), use_container_width=True)
                    
                    df_cleaned = clean_dataframe(raw_df)
                    df_limited, was_limited = limit_reviews(df_cleaned, max_limit=MAX_REVIEWS)
                    
                    if was_limited:
                        st.warning(f"⚠️ Note: Dataset contains {len(df_cleaned)} valid reviews. Processing the first {MAX_REVIEWS} reviews to maintain optimum system performance.")
                    
                    col_pname, col_action = st.columns([2, 1])
                    with col_pname:
                        custom_batch_product = st.text_input(
                            "Override Product Name (Leave blank to use file values)",
                            placeholder="e.g., Sony WH-1000XM4"
                        )
                    with col_action:
                        st.write("")
                        st.write("")
                        analyze_batch_clicked = st.button("🚀 Analyze & Save to Account", use_container_width=True, type="primary")
                        
                    if analyze_batch_clicked:
                        if custom_batch_product.strip():
                            df_limited['product_name'] = custom_batch_product.strip()
                            
                        with st.spinner(f"Analyzing {len(df_limited)} reviews with NLP & Heuristics..."):
                            processed_list = process_reviews_batch(
                                df_limited,
                                analyze_sentiment,
                                calculate_suspicion_score
                            )
                            
                            if processed_list:
                                inserted_count = insert_reviews(
                                    user_id,
                                    processed_list,
                                    source_name=uploaded_file.name,
                                    source_type="csv" if uploaded_file.name.endswith(".csv") else "excel"
                                )
                                st.session_state.active_dashboard_product = df_limited['product_name'].iloc[0]
                                st.success(f"🎉 Successfully analyzed and stored {inserted_count} reviews in your private account!")
                                info_box("Data is ready. Click 'Dashboard' in top navigation to view full analysis.", "success")
                            else:
                                st.error("No valid reviews could be extracted after text cleaning.")
                                
        st.markdown("---")
        st.markdown("###### Need a template or test data?")
        col_samp1, col_samp2 = st.columns([1, 2])
        with col_samp1:
            sample_df = load_sample_csv()
            if not sample_df.empty:
                sample_csv_bytes = sample_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download sample_reviews.csv",
                    data=sample_csv_bytes,
                    file_name="sample_reviews.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    # -------------------------------------------------------------
    # TAB 3: AMAZON PRODUCT URL & DEMOS
    # -------------------------------------------------------------
    with tab_amazon:
        st.markdown("##### Analyze Amazon Product from URL")
        st.caption("Input any Amazon product link or select a verified demo product below.")
        
        st.markdown("###### 🌟 Curated Demo Products")
        demo_cols = st.columns(2)
        for idx, demo in enumerate(DEMO_PRODUCTS):
            with demo_cols[idx % 2]:
                st.markdown(
                    f"""
                    <div class="demo-card">
                        <div style="font-weight: 600; color: #F8FAFC; font-size: 14px; margin-bottom: 4px;">{demo['name']}</div>
                        <div style="font-size: 12px; color: #94A3B8;">Marketplace: {demo['marketplace']} | ASIN: <code>{demo['asin']}</code></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                col_d_use, col_d_view = st.columns(2)
                with col_d_use:
                    if st.button(f"Analyze Product", key=f"use_demo_{idx}", use_container_width=True):
                        st.session_state.home_product_url = demo['url']
                        with st.spinner("Analyzing demo product..."):
                            success, msg, revs, meta = fetch_reviews_from_url(demo['url'])
                            if success and revs:
                                df_s = pd.DataFrame(revs)
                                df_c = clean_dataframe(df_s)
                                processed = process_reviews_batch(df_c, analyze_sentiment, calculate_suspicion_score)
                                insert_reviews(user_id, processed, source_name=f"Amazon URL ({demo['asin']})", source_type="url")
                                st.session_state.active_dashboard_product = meta.get('product_name', demo['name'])
                                st.session_state.page = 'Dashboard'
                                st.rerun()
                with col_d_view:
                    render_amazon_link_button(demo['url'], "View on Amazon")
        
        st.markdown("---")
        st.markdown("###### 🔗 Enter Custom Amazon Product URL")
        
        custom_url_val = st.text_input(
            "Amazon Product Link",
            value=st.session_state.get('active_product_url', ''),
            placeholder="e.g., https://www.amazon.com/dp/B0863TXGM3 or https://www.amazon.in/dp/B07PR1CL3S",
            key="tab_custom_url"
        )
        
        c_details = extract_amazon_details(custom_url_val) if custom_url_val.strip() else None
        if custom_url_val.strip() and c_details:
            if c_details["is_valid"]:
                col_cu1, col_cu2 = st.columns([3, 1])
                with col_cu1:
                    st.markdown(
                        f"""
                        <div style="padding: 8px 12px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.25);">
                            <span style="color: #34D399; font-weight: 600; font-size: 13px;">✓ Valid Amazon URL</span>
                            <span style="color: #94A3B8; font-size: 12px;">ASIN: <code>{c_details['asin']}</code></span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col_cu2:
                    render_amazon_link_button(c_details["canonical_url"], "View on Amazon")
                    
        if st.button("🚀 Fetch & Analyze Live Reviews", key="tab_fetch_btn", use_container_width=True, type="primary"):
            if not custom_url_val.strip():
                st.error("Please enter an Amazon product URL.")
            elif not c_details or not c_details["is_valid"]:
                st.error("Please enter a valid Amazon URL with an ASIN.")
            else:
                with st.spinner("Connecting to Amazon and analyzing customer reviews..."):
                    success, msg, revs, meta = fetch_reviews_from_url(custom_url_val)
                    if success and revs:
                        df_s = pd.DataFrame(revs)
                        df_c = clean_dataframe(df_s)
                        processed = process_reviews_batch(df_c, analyze_sentiment, calculate_suspicion_score)
                        insert_reviews(user_id, processed, source_name=f"Amazon URL ({meta.get('asin', 'Product')})", source_type="url")
                        st.session_state.active_dashboard_product = meta.get('product_name', 'Amazon Product')
                        st.session_state.page = 'Dashboard'
                        st.success(f"✓ Analyzed reviews for {st.session_state.active_dashboard_product}!")
                        st.rerun()
                    else:
                        info_box(msg, "warning")


# =====================================================================
# Page 3: Review Data Management
# =====================================================================

def render_data():
    """Render interactive review data explorer, search, filter, and deletion."""
    user = st.session_state.user
    user_id = user['id']
    
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #F8FAFC; margin: 0; font-size: 26px; font-weight: 700;">📋 Review Data Management</h1>
            <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 14px;">
                Browse, search, filter, and manage your private review records
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    all_reviews = get_reviews(user_id)
    
    if not all_reviews:
        empty_state(
            "No reviews in your database",
            "Upload a dataset or analyze reviews to populate your records.",
            "Go to Review Analyzer",
            lambda: setattr(st.session_state, 'page', 'Review Analyzer')
        )
        return
        
    df = pd.DataFrame(all_reviews)
    
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        search_kw = st.text_input("🔍 Search Reviews", placeholder="Keyword, product name...")
    with col_f2:
        prod_filter = st.selectbox("Product", ["All Products"] + get_products(user_id))
    with col_f3:
        sent_filter = st.selectbox("Sentiment", ["All Sentiments", "Positive", "Negative", "Neutral"])
    with col_f4:
        class_filter = st.selectbox("Classification", ["All Classifications", "Genuine-looking", "Suspicious"])
        
    filtered_df = df.copy()
    if search_kw.strip():
        kw = search_kw.strip().lower()
        filtered_df = filtered_df[
            filtered_df['review_text'].str.lower().str.contains(kw, na=False) |
            filtered_df['product_name'].str.lower().str.contains(kw, na=False)
        ]
        
    if prod_filter != "All Products":
        filtered_df = filtered_df[filtered_df['product_name'] == prod_filter]
        
    if sent_filter != "All Sentiments":
        filtered_df = filtered_df[filtered_df['sentiment'] == sent_filter]
        
    if class_filter != "All Classifications":
        filtered_df = filtered_df[filtered_df['classification'] == class_filter]
        
    st.caption(f"Showing {len(filtered_df)} of {len(df)} total reviews in your account.")
    
    if not filtered_df.empty:
        display_df = filtered_df[[
            'id', 'product_name', 'review_text', 'rating', 'sentiment',
            'classification', 'suspicion_score', 'created_at'
        ]].copy()
        
        display_df['sentiment'] = display_df['sentiment'].apply(sentiment_badge)
        display_df['classification'] = display_df['classification'].apply(status_badge)
        display_df['rating'] = display_df['rating'].apply(display_rating_stars)
        
        st.dataframe(display_df, use_container_width=True, height=420)
        
        col_down, _ = st.columns([1, 2])
        with col_down:
            down_csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Filtered Results (CSV)",
                data=down_csv,
                file_name="filtered_amazon_reviews.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("No reviews match the current search filters.")
        
    st.markdown("---")
    st.markdown("##### 🗑️ Manage Your Review Records")
    
    del_col1, del_col2 = st.columns(2)
    with del_col1:
        st.markdown("###### Delete Specific Review")
        del_id = st.number_input("Enter Review ID", min_value=1, step=1)
        if st.button("Delete Review by ID", use_container_width=True):
            if delete_review(user_id, int(del_id)):
                st.success(f"Review #{del_id} deleted successfully.")
                st.rerun()
            else:
                st.error(f"Review #{del_id} not found in your account.")
                
    with del_col2:
        st.markdown("###### Reset Account Data")
        if st.button("⚠️ Clear All My Reviews & History", use_container_width=True):
            if st.session_state.get('confirm_user_clear', False):
                clear_all(user_id)
                st.session_state.confirm_user_clear = False
                st.session_state.active_dashboard_product = None
                st.success("All your reviews and history have been cleared.")
                st.rerun()
            else:
                st.session_state.confirm_user_clear = True
                st.warning("Click again to confirm deletion of all your stored reviews.")


# =====================================================================
# Page 4: User Analysis History (Requirements 5)
# =====================================================================

def render_history():
    """
    Render comprehensive Analysis History showing products analyzed
    by the logged-in user, performance statistics, and batch logs.
    """
    user = st.session_state.user
    user_id = user['id']
    
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="color: #F8FAFC; margin: 0; font-size: 26px; font-weight: 700;">📜 Analysis History</h1>
            <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 14px;">
                Complete record of all Amazon products and datasets analyzed by <strong>{user['username']}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    product_summaries = get_user_product_summary(user_id)
    history_items = get_user_history(user_id)
    
    if not product_summaries and not history_items:
        empty_state(
            "No analysis history yet",
            "When you analyze Amazon product URLs or upload review datasets, your records will appear here.",
            "Analyze a Product",
            lambda: setattr(st.session_state, 'page', 'Dashboard')
        )
        return
        
    tab_h_prods, tab_h_logs = st.tabs(["📦 Analyzed Products Summary", "📋 Raw Upload Logs"])
    
    with tab_h_prods:
        st.markdown("##### Products Analyzed in Your Account")
        st.caption("Click 'View Dashboard' to load a product's full analytics suite.")
        
        if not product_summaries:
            st.info("No products analyzed yet.")
        else:
            for idx, prod in enumerate(product_summaries):
                p_name = prod['product_name']
                total_r = prod['total_reviews']
                avg_r = prod['avg_rating'] if prod['avg_rating'] else 0.0
                pos_c = prod['positive_count'] or 0
                neg_c = prod['negative_count'] or 0
                gen_c = prod['genuine_count'] or 0
                last_ts = prod['last_analyzed'] or "Recently"
                if "T" in str(last_ts):
                    last_ts = str(last_ts).split("T")[0]
                    
                gen_pct = (gen_c / total_r * 100) if total_r > 0 else 0
                
                col_card, col_action = st.columns([8, 3])
                with col_card:
                    st.markdown(
                        f"""
                        <div class="history-product-card">
                            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                                <span style="font-weight: 700; color: #F8FAFC; font-size: 15px;">📦 {p_name}</span>
                                <span style="color: #94A3B8; font-size: 12px;">Analyzed: {last_ts}</span>
                            </div>
                            <div style="display: flex; gap: 16px; margin-top: 8px; font-size: 13px; color: #CBD5E1; flex-wrap: wrap;">
                                <span>💬 <strong>{total_r}</strong> reviews</span>
                                <span>⭐ <strong>{avg_r:.1f}</strong> rating</span>
                                <span>😊 <span style="color: #34D399;">{pos_c}</span> positive</span>
                                <span>😞 <span style="color: #F87171;">{neg_c}</span> negative</span>
                                <span>🛡️ <span style="color: #22D3EE;">{gen_pct:.0f}%</span> genuine</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col_action:
                    col_b1, col_b2 = st.columns([2, 1])
                    with col_b1:
                        if st.button("📊 View Dashboard", key=f"hist_p_view_{idx}", use_container_width=True):
                            st.session_state.active_dashboard_product = p_name
                            st.session_state.page = 'Dashboard'
                            st.rerun()
                    with col_b2:
                        if st.button("🗑️", key=f"hist_p_del_{idx}", help=f"Delete {p_name} data", use_container_width=True):
                            delete_product_reviews(user_id, p_name)
                            st.success(f"Deleted {p_name}")
                            st.rerun()
                            
    with tab_h_logs:
        st.markdown("##### Batch Analysis & Upload Logs")
        if not history_items:
            st.info("No raw upload batches recorded.")
        else:
            hist_df = pd.DataFrame(history_items)
            disp_hist = hist_df[['id', 'source_name', 'source_type', 'product_name', 'total_reviews', 'created_at']].copy()
            disp_hist.columns = ['ID', 'Source Name', 'Type', 'Products Analyzed', 'Total Reviews', 'Timestamp']
            st.dataframe(disp_hist, use_container_width=True)
            
            st.markdown("###### Remove Upload Log Entry")
            col_hl, _ = st.columns([1, 2])
            with col_hl:
                h_id = st.number_input("Log Entry ID to Remove", min_value=1, step=1)
                if st.button("Delete Log Entry", use_container_width=True):
                    if delete_history_item(user_id, int(h_id)):
                        st.success(f"Log entry #{h_id} deleted.")
                        st.rerun()
                    else:
                        st.error(f"Entry #{h_id} not found.")


# =====================================================================
# Page 5: Advanced Analytics
# =====================================================================

def render_analytics():
    """Render advanced statistical distributions, NLP keyword extraction, and suspicious patterns."""
    user = st.session_state.user
    user_id = user['id']
    
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #F8FAFC; margin: 0; font-size: 26px; font-weight: 700;">📊 Advanced NLP Analytics</h1>
            <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 14px;">
                Keyword frequency extraction, sentiment polarity distributions, and pattern correlations
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    all_reviews = get_reviews(user_id)
    if not all_reviews:
        empty_state(
            "No reviews available for advanced analysis",
            "Analyze reviews first to view NLP metrics and keyword distributions.",
            "Analyze a Product",
            lambda: setattr(st.session_state, 'page', 'Dashboard')
        )
        return
        
    df = pd.DataFrame(all_reviews)
    palette = get_color_palette()
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Avg Polarity", f"{df['polarity'].mean():.3f}", help="Scale: -1.0 (Negative) to +1.0 (Positive)")
    with col_m2:
        st.metric("Avg Subjectivity", f"{df['subjectivity'].mean():.3f}", help="Scale: 0.0 (Objective) to 1.0 (Subjective)")
    with col_m3:
        st.metric("Avg Suspicion Score", f"{df['suspicion_score'].mean():.2f} / 7")
    with col_m4:
        sus_rate = (df['classification'] == 'Suspicious').mean() * 100
        st.metric("Suspicious Ratio", f"{sus_rate:.1f}%")
        
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown("##### Sentiment Polarity Histogram")
        fig_pol = px.histogram(df, x='polarity', nbins=24, color_discrete_sequence=[palette['primary']])
        fig_pol.update_layout(
            paper_bgcolor=palette['paper_bgcolor'],
            plot_bgcolor=palette['plot_bgcolor'],
            font=dict(family="Poppins", color=palette['font_color'])
        )
        st.plotly_chart(fig_pol, use_container_width=True)
        
    with col_h2:
        st.markdown("##### Subjectivity Distribution")
        fig_sub = px.histogram(df, x='subjectivity', nbins=24, color_discrete_sequence=[palette['genuine']])
        fig_sub.update_layout(
            paper_bgcolor=palette['paper_bgcolor'],
            plot_bgcolor=palette['plot_bgcolor'],
            font=dict(family="Poppins", color=palette['font_color'])
        )
        st.plotly_chart(fig_sub, use_container_width=True)
        
    st.markdown("---")
    st.markdown("#### 🔤 Keyword & Phrase Frequency Extraction")
    
    if nlp_model is not None:
        pos_texts = df[df['sentiment'] == 'Positive']['review_text'].dropna().tolist()
        neg_texts = df[df['sentiment'] == 'Negative']['review_text'].dropna().tolist()
        
        def extract_top_tokens(texts, top_n=10):
            if not texts:
                return []
            combined = " ".join(texts[:50])
            doc = nlp_model(combined)
            tokens = [
                token.text.lower() for token in doc
                if (token.pos_ in ['NOUN', 'ADJ'] and
                    not token.is_stop and
                    not token.is_punct and
                    len(token.text) > 2)
            ]
            from collections import Counter
            return Counter(tokens).most_common(top_n)
            
        col_k1, col_k2 = st.columns(2)
        with col_k1:
            st.markdown("###### Top Positive Praise Keywords")
            pos_keywords = extract_top_tokens(pos_texts)
            if pos_keywords:
                k_df = pd.DataFrame(pos_keywords, columns=['Keyword', 'Mentions'])
                fig_k_pos = px.bar(k_df, x='Mentions', y='Keyword', orientation='h', color_discrete_sequence=[palette['positive']])
                fig_k_pos.update_layout(
                    paper_bgcolor=palette['paper_bgcolor'],
                    plot_bgcolor=palette['plot_bgcolor'],
                    font=dict(family="Poppins", color=palette['font_color'])
                )
                st.plotly_chart(fig_k_pos, use_container_width=True)
            else:
                st.info("No positive reviews available for keyword extraction.")
                
        with col_k2:
            st.markdown("###### Top Negative Concern Keywords")
            neg_keywords = extract_top_tokens(neg_texts)
            if neg_keywords:
                k_df_neg = pd.DataFrame(neg_keywords, columns=['Keyword', 'Mentions'])
                fig_k_neg = px.bar(k_df_neg, x='Mentions', y='Keyword', orientation='h', color_discrete_sequence=[palette['negative']])
                fig_k_neg.update_layout(
                    paper_bgcolor=palette['paper_bgcolor'],
                    plot_bgcolor=palette['plot_bgcolor'],
                    font=dict(family="Poppins", color=palette['font_color'])
                )
                st.plotly_chart(fig_k_neg, use_container_width=True)
            else:
                st.info("No negative reviews available for keyword extraction.")
    else:
        info_box("Natural Language Processing (spaCy) model is running in lightweight mode. Full entity extraction is active when en_core_web_sm is present.", "info")
        
    st.markdown("---")
    st.markdown("#### ⚠️ Reviews Triggering Highest Suspicion Heuristics")
    high_suspicion = df[df['classification'] == 'Suspicious'].sort_values('suspicion_score', ascending=False).head(5)
    
    if not high_suspicion.empty:
        for _, row in high_suspicion.iterrows():
            with st.expander(f"Suspicion Score {row['suspicion_score']}/7 — {row['product_name']}"):
                st.markdown(f"**Review Content:** {row['review_text']}")
                st.markdown(f"**Sentiment:** {sentiment_badge(row['sentiment'])} &nbsp;|&nbsp; **Rating:** {display_rating_stars(row['rating'])}", unsafe_allow_html=True)
    else:
        st.success("✓ No suspicious reviews detected in your current dataset.")


# =====================================================================
# Page 6: About Project & Documentation
# =====================================================================

def render_about():
    """Render comprehensive project documentation."""
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #F8FAFC; margin: 0; font-size: 26px; font-weight: 700;">ℹ️ About Amazon Review Insight Pro Analyzer</h1>
            <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 14px;">
                Architecture, heuristic rules, data authenticity guarantees, and deployment readiness
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown(
            """
            <div class="dark-card">
                <h3 style="color: #F8FAFC; font-size: 18px; margin-top: 0;">🎯 Project Mission</h3>
                <p style="color: #94A3B8; font-size: 14px; line-height: 1.6;">
                    <strong>Amazon Review Insight Pro Analyzer</strong> is an enterprise-grade platform 
                    engineered to analyze consumer review corpora, measure multi-dimensional sentiment polarity, 
                    and detect anomalous or suspicious review patterns using a 7-factor heuristic detection framework.
                </p>
                <h4 style="color: #F8FAFC; font-size: 15px; margin-top: 16px;">🛡️ Data Authenticity Standard</h4>
                <p style="color: #94A3B8; font-size: 14px; line-height: 1.6;">
                    Our platform strictly forbids simulated, mock, or fake reviews. When analyzing Amazon listings,
                    if automated scraping is challenged by anti-bot verification, the platform reports honestly
                    and provides direct product links for manual import rather than inventing fabricated metrics.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_a2:
        st.markdown(
            """
            <div class="dark-card">
                <h3 style="color: #F8FAFC; font-size: 18px; margin-top: 0;">🛠️ Technical Architecture</h3>
                <ul style="color: #94A3B8; font-size: 14px; line-height: 1.7; padding-left: 20px; margin: 0;">
                    <li><strong>Framework:</strong> Python 3.10+ & Streamlit</li>
                    <li><strong>Security:</strong> PBKDF2-HMAC-SHA256 password hashing with unique salt</li>
                    <li><strong>Data Isolation:</strong> Relational SQLite with strict user-scoped foreign keys</li>
                    <li><strong>Sentiment Engine:</strong> TextBlob polarity and subjectivity analysis</li>
                    <li><strong>NLP Tokenization:</strong> spaCy English model for linguistic extraction</li>
                    <li><strong>Visualizations:</strong> Interactive Plotly Dark theme suite</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown("#### 🔍 The 7 Heuristic Suspicion Rules")
    st.markdown(
        """
        The authenticity detector evaluates every review against 7 independent linguistic indicators:
        
        1. **Very Short Review (< 5 words):** Extremely terse feedback often indicates automated bot activity.
        2. **Excessive Repeated Words (30%+):** Repetitive token spam frequently found in incentivized reviews.
        3. **Excessive Capitalization (> 50% uppercase):** Over-capitalization used to artificially grab visual attention.
        4. **Excessive Exclamation Marks (3+):** Over-punctuated enthusiasm commonly seen in promotional campaigns.
        5. **Repeated Promotional Phrases:** Keywords such as 'must buy', 'best product ever', 'act now'.
        6. **Hyperbolic Extreme Language:** Overuse of extreme superlatives like 'phenomenal', 'horrible', 'perfect'.
        7. **Corpus Duplicate Similarity (85%+ ratio):** High cross-review similarity indicating coordinated campaign copy-paste.
        
        **Classification Scoring:**
        - **0 to 2 Rules Triggered:** Classified as <code>Genuine-looking</code>.
        - **3 or More Rules Triggered:** Classified as <code>Suspicious</code>.
        """
    )


# =====================================================================
# Main Application Router
# =====================================================================

def main():
    """Main routing controller enforcing session authentication and page selection."""
    if not st.session_state.authenticated or st.session_state.user is None:
        render_auth_page()
    else:
        # Render modern top navigation bar (Requirement 1)
        render_top_navbar()
        
        current_page = st.session_state.page
        if current_page == 'Dashboard':
            render_dashboard()
        elif current_page == 'Review Analyzer':
            render_analyzer()
        elif current_page == 'Review Data':
            render_data()
        elif current_page == 'Analysis History':
            render_history()
        elif current_page == 'Advanced Analytics':
            render_analytics()
        elif current_page == 'About Project':
            render_about()
        else:
            render_dashboard()


if __name__ == "__main__":
    main()

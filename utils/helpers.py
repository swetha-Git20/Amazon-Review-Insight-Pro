"""
Helper functions and UI components for Amazon Review Insight Pro Analyzer
Provides dark theme styling, Poppins typography, and modern UI components.
"""

import streamlit as st
import html
from typing import Optional, List, Dict


# Dark Theme Color Palette
COLORS = {
    'primary': '#6366F1',
    'primary_light': '#818CF8',
    'primary_dark': '#4F46E5',
    'success': '#10B981',
    'warning': '#F59E0B',
    'error': '#EF4444',
    'info': '#06B6D4',
    'suspicious': '#F97316',
    'background': '#0B0F19',
    'surface': '#131B2E',
    'surface_lighter': '#1E293B',
    'text_primary': '#F8FAFC',
    'text_secondary': '#94A3B8',
    'text_muted': '#64748B',
    'border': 'rgba(255, 255, 255, 0.08)',
    'border_accent': 'rgba(99, 102, 241, 0.3)'
}


def inject_custom_css():
    """
    Inject custom CSS to apply Poppins font, premium dark aesthetic,
    and suppress unwanted keyboard hints / headers.
    """
    css = """
    <style>
    /* Import Poppins Font from Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
    
    /* Apply Poppins to all elements */
    html, body, [class*="css"], .stMarkdown, p, span, button, input, textarea, label, div, h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Hide unwanted Streamlit UI elements */
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; display: none !important; }
    header { visibility: hidden !important; }
    .stDeployButton { display: none !important; }
    
    /* Move navigation to Top Bar: Hide default Streamlit sidebar */
    [data-testid="stSidebar"], section[data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
    }
    
    /* Optimize main content layout */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1240px !important;
    }
    
    /* Top Navbar Styling */
    .top-nav-container {
        background: linear-gradient(135deg, rgba(19, 27, 46, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 14px 22px;
        margin-bottom: 22px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35);
    }
    
    /* Hero Analyzer Card Styling */
    .hero-analyzer-card {
        background: radial-gradient(circle at top right, rgba(99, 102, 241, 0.18) 0%, rgba(19, 27, 46, 0.9) 65%);
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 18px;
        padding: 28px 32px;
        margin-bottom: 26px;
        box-shadow: 0 12px 36px -10px rgba(0, 0, 0, 0.55);
    }
    
    /* History Card Styling */
    .history-product-card {
        background: rgba(19, 27, 46, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 12px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .history-product-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    /* Suppress unnecessary keyboard hints (e.g. "Press Ctrl+Enter") */
    [data-testid="InputInstructions"] {
        display: none !important;
        visibility: hidden !important;
    }
    div[class*="InputInstructions"] {
        display: none !important;
    }
    
    /* Dark Theme Surface Containers */
    .dark-card {
        background: linear-gradient(145deg, #131B2E 0%, #0F172A 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }
    
    .dark-card:hover {
        border-color: rgba(99, 102, 241, 0.25);
    }
    
    /* Metric Card Styling */
    .metric-card-dark {
        background: linear-gradient(145deg, rgba(19, 27, 46, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 14px;
        transition: transform 0.2s ease, border-color 0.2s ease;
        box-shadow: 0 4px 14px 0 rgba(0, 0, 0, 0.25);
    }
    
    .metric-card-dark:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    /* Sentiment and Status Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    
    .badge-positive {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .badge-negative {
        background-color: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .badge-neutral {
        background-color: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .badge-genuine {
        background-color: rgba(6, 182, 212, 0.15);
        color: #22D3EE;
        border: 1px solid rgba(6, 182, 212, 0.3);
    }
    
    .badge-suspicious {
        background-color: rgba(249, 115, 22, 0.15);
        color: #FB923C;
        border: 1px solid rgba(249, 115, 22, 0.3);
    }
    
    /* Callout & Notification Boxes */
    .box-container {
        padding: 16px 20px;
        border-radius: 12px;
        margin: 16px 0;
        font-size: 14px;
        line-height: 1.5;
    }
    
    .info-box-dark {
        background-color: rgba(6, 182, 212, 0.1);
        border-left: 4px solid #06B6D4;
        color: #E2E8F0;
    }
    
    .success-box-dark {
        background-color: rgba(16, 185, 129, 0.1);
        border-left: 4px solid #10B981;
        color: #E2E8F0;
    }
    
    .warning-box-dark {
        background-color: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #F59E0B;
        color: #E2E8F0;
    }
    
    .error-box-dark {
        background-color: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #EF4444;
        color: #E2E8F0;
    }
    
    /* Empty State Styling */
    .empty-state-dark {
        text-align: center;
        padding: 48px 24px;
        background: linear-gradient(145deg, #131B2E 0%, #0F172A 100%);
        border-radius: 16px;
        border: 1px dashed rgba(255, 255, 255, 0.15);
        margin: 24px 0;
    }
    
    /* Button enhancements */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
    }
    
    /* Amazon Product Link Button */
    .amazon-link-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, #FF9900 0%, #E67A00 100%);
        color: #111827 !important;
        font-weight: 700;
        font-size: 14px;
        padding: 10px 20px;
        border-radius: 10px;
        text-decoration: none !important;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(255, 153, 0, 0.35);
        margin-top: 8px;
    }
    
    .amazon-link-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(255, 153, 0, 0.5);
        color: #000000 !important;
    }
    
    /* File Uploader styling & Filename visibility */
    [data-testid="stFileUploader"] {
        background: rgba(19, 27, 46, 0.6) !important;
        border: 1px dashed rgba(99, 102, 241, 0.4) !important;
        border-radius: 14px !important;
        padding: 16px !important;
    }
    [data-testid="stFileUploaderFileName"], .uploadedFileName, [data-testid="stFileUploaderFile"] div {
        color: #F8FAFC !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    [data-testid="stFileUploaderFile"] {
        background: rgba(30, 41, 59, 0.9) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        padding: 8px 12px !important;
    }
    [data-testid="stFileUploaderFile"] small {
        color: #94A3B8 !important;
    }
    
    /* Password input eye toggle button */
    .eye-toggle-btn button {
        height: 42px !important;
        font-size: 18px !important;
        padding: 0 10px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
    }
    .eye-toggle-btn button:hover {
        background: rgba(99, 102, 241, 0.3) !important;
        border-color: #6366F1 !important;
    }

    /* About section and Documentation Cards */
    .about-card {
        background: linear-gradient(145deg, #131B2E 0%, #0F172A 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }
    .about-card h3, .about-card h4, .about-card h5 {
        color: #F8FAFC !important;
    }
    .about-card p, .about-card li {
        color: #E2E8F0 !important;
        font-size: 14px !important;
        line-height: 1.65 !important;
    }
    
    /* Demo Product Card */
    .demo-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def metric_card(label: str, value: str, subtext: Optional[str] = None, icon: Optional[str] = None, color_type: str = 'primary'):
    """
    Render a responsive dark-themed metric card.
    """
    border_color_map = {
        'primary': 'rgba(99, 102, 241, 0.4)',
        'success': 'rgba(16, 185, 129, 0.4)',
        'warning': 'rgba(245, 158, 11, 0.4)',
        'error': 'rgba(239, 68, 68, 0.4)',
        'info': 'rgba(6, 182, 212, 0.4)',
        'suspicious': 'rgba(249, 115, 22, 0.4)'
    }
    
    border_color = border_color_map.get(color_type, 'rgba(255, 255, 255, 0.08)')
    icon_str = f"<span style='font-size: 22px; margin-right: 8px;'>{icon}</span>" if icon else ""
    subtext_str = f"<div style='color: #94A3B8; font-size: 12px; margin-top: 6px;'>{html.escape(subtext)}</div>" if subtext else ""
    
    card_html = f"""
    <div class="metric-card-dark" style="border-left: 4px solid {border_color};">
        <div style="color: #94A3B8; font-size: 13px; font-weight: 500;">{html.escape(label)}</div>
        <div style="color: #F8FAFC; font-size: 24px; font-weight: 700; margin-top: 4px; display: flex; align-items: center;">
            {icon_str}{html.escape(value)}
        </div>
        {subtext_str}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def sentiment_badge(sentiment: str) -> str:
    """Generate HTML badge for review sentiment."""
    badge_map = {
        'Positive': 'badge-positive',
        'Negative': 'badge-negative',
        'Neutral': 'badge-neutral'
    }
    css_class = badge_map.get(sentiment, 'badge-neutral')
    return f'<span class="badge {css_class}">{html.escape(str(sentiment))}</span>'


def recommendation_badge(rec_string: str) -> str:
    """Generate HTML badge for My Recommendation column."""
    if not rec_string:
        return ""
    rec_str = str(rec_string)
    if rec_str.startswith("Not Recommended"):
        badge_html = '<span class="badge badge-negative">❌ Not Recommended</span>'
        detail = rec_str.replace("Not Recommended", "", 1).lstrip(" —-:")
    elif rec_str.startswith("Recommended"):
        badge_html = '<span class="badge badge-positive">✅ Recommended</span>'
        detail = rec_str.replace("Recommended", "", 1).lstrip(" —-:")
    else:
        badge_html = '<span class="badge badge-neutral">⚖️ Mixed</span>'
        detail = rec_str.replace("Mixed", "", 1).lstrip(" —-:")
    if detail:
        return f'{badge_html} <span style="color: #CBD5E1; font-size: 12px;">{html.escape(detail)}</span>'
    return badge_html


def status_badge(status: str) -> str:
    """Generate HTML badge for Genuine vs Suspicious classification."""
    css_class = 'badge-genuine' if status == 'Genuine-looking' else 'badge-suspicious'
    return f'<span class="badge {css_class}">{html.escape(str(status))}</span>'


def info_box(message: str, box_type: str = 'info'):
    """Display modern dark callout notification box."""
    type_class = f"{box_type}-box-dark"
    html_content = f"""
    <div class="box-container {type_class}">
        {html.escape(message)}
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)


def empty_state(title: str, message: str, button_text: Optional[str] = None, button_callback = None):
    """Render a clean empty state card."""
    html_content = f"""
    <div class="empty-state-dark">
        <div style="font-size: 42px; margin-bottom: 12px;">📊</div>
        <h3 style="color: #F8FAFC; margin: 0 0 8px 0; font-size: 18px; font-weight: 600;">{html.escape(title)}</h3>
        <p style="color: #94A3B8; margin: 0 0 16px 0; font-size: 14px; max-width: 480px; margin-left: auto; margin-right: auto;">
            {html.escape(message)}
        </p>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)
    if button_text and button_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(button_text, use_container_width=True):
                button_callback()


def display_suspicion_indicators(triggered_rules: List[str], all_rules: List[str]):
    """Display breakdown of 7 heuristic rules in a stylish dark list."""
    st.markdown("#### 🛡️ Suspicion Heuristic Breakdown")
    
    for rule in all_rules:
        is_triggered = rule in triggered_rules
        icon = "⚠️" if is_triggered else "✓"
        color = "#EF4444" if is_triggered else "#10B981"
        bg = "rgba(239, 68, 68, 0.1)" if is_triggered else "rgba(16, 185, 129, 0.05)"
        status_text = "Triggered" if is_triggered else "Passed"
        
        card_html = f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; margin-bottom: 6px; border-radius: 8px; background: {bg}; border: 1px solid rgba(255, 255, 255, 0.05);">
            <span style="color: #E2E8F0; font-size: 13px;">{html.escape(rule)}</span>
            <span style="color: {color}; font-weight: 600; font-size: 12px;">{icon} {status_text}</span>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)


def display_rating_stars(rating: Optional[float]) -> str:
    """Format numeric rating into star icons."""
    if rating is None or rating == "":
        return "N/A"
    try:
        r = float(rating)
        full = int(r)
        half = "½" if (r - full) >= 0.5 else ""
        return "★" * full + half + f" ({r:.1f})"
    except Exception:
        return str(rating)


def render_amazon_link_button(url: str, label: str = "View Product on Amazon"):
    """
    Render a prominent button that opens the exact product page in a new browser tab.
    Guarantees target='_blank' and rel='noopener noreferrer'.
    """
    if not url:
        return
    btn_html = f"""
    <div style="margin: 12px 0;">
        <a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer" class="amazon-link-btn">
            <span>🛒</span>
            <span>{html.escape(label)}</span>
            <span style="font-size: 12px; opacity: 0.8;">↗</span>
        </a>
    </div>
    """
    st.markdown(btn_html, unsafe_allow_html=True)


def get_color_palette() -> Dict[str, str]:
    """Return dark-mode color palette for Plotly charts."""
    return {
        'positive': '#10B981',
        'negative': '#EF4444',
        'neutral': '#F59E0B',
        'genuine': '#06B6D4',
        'suspicious': '#F97316',
        'primary': '#6366F1',
        'paper_bgcolor': '#131B2E',
        'plot_bgcolor': '#131B2E',
        'font_color': '#F8FAFC',
        'grid_color': 'rgba(255, 255, 255, 0.08)'
    }

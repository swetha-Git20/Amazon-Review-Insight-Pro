"""
Helper functions and UI components for Amazon Review Insight Pro
Provides reusable UI components and shared CSS styling.
"""

import streamlit as st
from typing import Optional


# Color palette from Stitch design
COLORS = {
    'primary': '#4F46E5',
    'primary_hover': '#4338CA',
    'secondary': '#4e45d5',
    'success': '#16A34A',
    'warning': '#F59E0B',
    'error': '#DC2626',
    'info': '#0EA5E9',
    'suspicious': '#F97316',
    'background': '#F5F7FB',
    'surface': '#FFFFFF',
    'text_primary': '#111827',
    'text_secondary': '#6B7280',
    'border': '#E5E7EB'
}


def inject_custom_css():
    """
    Inject custom CSS to match the Stitch design.
    
    Why: Apply consistent styling across the application that Streamlit doesn't provide by default.
    
    Input: None
    
    Output: None (injects CSS via st.markdown)
    """
    css = """
    <style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');
    
    /* Apply Inter font to all text */
    * {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Custom card styling */
    .custom-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    /* Metric card styling */
    .metric-card {
        background-color: #F5F2FF;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #E5E7EB;
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .badge-positive {
        background-color: #DCFCE7;
        color: #16A34A;
    }
    
    .badge-negative {
        background-color: #FEE2E2;
        color: #DC2626;
    }
    
    .badge-neutral {
        background-color: #FEF3C7;
        color: #F59E0B;
    }
    
    .badge-genuine {
        background-color: #E0F2FE;
        color: #0EA5E9;
    }
    
    .badge-suspicious {
        background-color: #FED7AA;
        color: #F97316;
    }
    
    /* Info box styling */
    .info-box {
        background-color: #F0ECF9;
        border-left: 4px solid #4F46E5;
        padding: 16px;
        border-radius: 8px;
        margin: 16px 0;
    }
    
    /* Success box styling */
    .success-box {
        background-color: #DCFCE7;
        border-left: 4px solid #16A34A;
        padding: 16px;
        border-radius: 8px;
        margin: 16px 0;
    }
    
    /* Error box styling */
    .error-box {
        background-color: #FEE2E2;
        border-left: 4px solid #DC2626;
        padding: 16px;
        border-radius: 8px;
        margin: 16px 0;
    }
    
    /* Warning box styling */
    .warning-box {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 16px;
        border-radius: 8px;
        margin: 16px 0;
    }
    
    /* Empty state styling */
    .empty-state {
        text-align: center;
        padding: 48px 24px;
        background-color: #F0ECF9;
        border-radius: 16px;
        border: 1px solid #E5E7EB;
    }
    
    /* Button styling override */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #FFFFFF;
    }
    
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .metric-card {
            padding: 12px;
        }
        
        .custom-card {
            padding: 16px;
        }
    }
    
    /* Table container for horizontal scroll */
    .table-container {
        overflow-x: auto;
        border-radius: 12px;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background-color: #4F46E5;
    }
    
    /* Hide streamlit footer */
    footer {
        visibility: hidden;
    }
    
    /* Hide streamlit header menu */
    #MainMenu {
        visibility: hidden;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def metric_card(label: str, value: str, subtext: Optional[str] = None, icon: Optional[str] = None, color: str = 'primary'):
    """
    Display a metric card with label, value, and optional subtext.
    
    Why: Consistent metric display matching the Stitch design.
    
    Input: label (str) - Metric label
           value (str) - Metric value
           subtext (Optional[str]) - Additional context text
           icon (Optional[str]) - Emoji icon
           color (str) - Color theme
    
    Output: None (displays in Streamlit)
    """
    bg_color = COLORS.get(f'{color}_bg', '#F5F2FF')
    text_color = COLORS.get(color, COLORS['primary'])
    
    icon_html = f"<span style='font-size: 24px; margin-right: 8px;'>{icon}</span>" if icon else ""
    subtext_html = f"<p style='color: {COLORS['text_secondary']}; font-size: 12px; margin: 4px 0 0 0;'>{subtext}</p>" if subtext else ""
    
    html = f"""
    <div class="metric-card" style="background-color: {bg_color};">
        <div style='display: flex; align-items: center; justify-content: space-between;'>
            <div>
                <p style='color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 600; margin: 0;'>{label}</p>
                <p style='color: {COLORS['text_primary']}; font-size: 24px; font-weight: 700; margin: 8px 0 0 0;'>{icon_html}{value}</p>
                {subtext_html}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def sentiment_badge(sentiment: str) -> str:
    """
    Generate HTML for a sentiment badge.
    
    Why: Consistent sentiment display with color coding.
    
    Input: sentiment (str) - 'Positive', 'Negative', or 'Neutral'
    
    Output: str - HTML badge string
    """
    badge_class = {
        'Positive': 'badge-positive',
        'Negative': 'badge-negative',
        'Neutral': 'badge-neutral'
    }.get(sentiment, 'badge-neutral')
    
    return f'<span class="badge {badge_class}">{sentiment}</span>'


def status_badge(status: str) -> str:
    """
    Generate HTML for a status badge (Genuine/Suspicious).
    
    Why: Consistent status display with color coding.
    
    Input: status (str) - 'Genuine-looking' or 'Suspicious'
    
    Output: str - HTML badge string
    """
    badge_class = {
        'Genuine-looking': 'badge-genuine',
        'Suspicious': 'badge-suspicious'
    }.get(status, 'badge-genuine')
    
    return f'<span class="badge {badge_class}">{status}</span>'


def info_box(message: str, box_type: str = 'info'):
    """
    Display an info box with message.
    
    Why: Consistent informational/warning/error display.
    
    Input: message (str) - Message to display
           box_type (str) - 'info', 'success', 'error', or 'warning'
    
    Output: None (displays in Streamlit)
    """
    box_class = {
        'info': 'info-box',
        'success': 'success-box',
        'error': 'error-box',
        'warning': 'warning-box'
    }.get(box_type, 'info-box')
    
    html = f'<div class="{box_class}"><p style="margin: 0; color: {COLORS["text_primary"]};">{message}</p></div>'
    st.markdown(html, unsafe_allow_html=True)


def empty_state(title: str, message: str, button_text: str, button_callback):
    """
    Display an empty state with title, message, and action button.
    
    Why: Consistent empty state design when no data is available.
    
    Input: title (str) - Empty state title
           message (str) - Descriptive message
           button_text (str) - Button label
           button_callback - Function to call on button click
    
    Output: None (displays in Streamlit)
    """
    html = f"""
    <div class="empty-state">
        <span style="font-size: 48px; margin-bottom: 16px;">📂</span>
        <h3 style="color: {COLORS['text_primary']}; margin: 0 0 8px 0;">{title}</h3>
        <p style="color: {COLORS['text_secondary']}; margin: 0 0 24px 0;">{message}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    
    if st.button(button_text, key=f"empty_state_{button_text}"):
        button_callback()


def display_suspicion_indicators(triggered_rules: list, all_rules: list):
    """
    Display suspicion indicators with checkmarks for triggered rules.
    
    Why: Show which heuristic rules were triggered for transparency.
    
    Input: triggered_rules (list) - List of triggered rule names
           all_rules (list) - List of all possible rule names
    
    Output: None (displays in Streamlit)
    """
    st.markdown("### Suspicious Indicators")
    
    for rule in all_rules:
        is_triggered = rule in triggered_rules
        icon = "❌" if is_triggered else "✅"
        color = "#DC2626" if is_triggered else "#16A34A"
        font_weight = "bold" if is_triggered else "normal"
        
        html = f"""
        <div style='display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #E5E7EB;'>
            <span style='color: {COLORS["text_secondary"]};'>{rule}</span>
            <span style='color: {color}; font-weight: {font_weight};'>{icon}</span>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)


def display_rating_stars(rating: float) -> str:
    """
    Generate HTML for star rating display.
    
    Why: Visual representation of numeric ratings.
    
    Input: rating (float) - Rating value (1-5)
    
    Output: str - HTML star rating string
    """
    full_stars = int(rating)
    has_half = rating - full_stars >= 0.5
    
    stars = "⭐" * full_stars
    if has_half:
        stars += "✨"  # Using sparkle for half star
    
    return stars


def get_color_palette():
    """
    Return the color palette for Plotly charts.
    
    Why: Consistent chart colors matching the design system.
    
    Input: None
    
    Output: dict - Color palette dictionary
    """
    return {
        'positive': '#16A34A',
        'negative': '#DC2626',
        'neutral': '#F59E0B',
        'genuine': '#0EA5E9',
        'suspicious': '#F97316',
        'primary': '#4F46E5',
        'background': '#FFFFFF'
    }

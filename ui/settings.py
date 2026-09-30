import streamlit as st
from config import CATEGORIES, APP_VERSION

def render_settings_page():
    """Render Settings tab."""
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h2 style="color: #38bdf8;">⚙️ APPLICATION SETTINGS</h2>
            <p style="color: #94a3b8;">Customize detection sensitivity, AI models, and local rules.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### AI & Detection Engine")
    st.selectbox(
        "Detection Model",
        ["PaddleOCR + BERT NER + Rule Engine (Recommended)", "Regex Only (Fast)", "Qualcomm AI Hub Backend (Auto-Detect)"]
    )
    
    st.slider("Detection Sensitivity Threshold", min_value=0.5, max_value=1.0, value=0.75, step=0.05)

    st.markdown("### Active Sensitive Categories")
    for cat_key, cat_info in CATEGORIES.items():
        st.checkbox(f"{cat_info['title']} ({cat_info['severity']})", value=True, key=f"set_cat_{cat_key}")

    st.markdown("---")
    st.markdown(f"**SnapGuard Version:** `{APP_VERSION}`")
    st.markdown("**Platform:** Optimized for Snapdragon-powered HP PCs & Windows/macOS On-Device AI.")

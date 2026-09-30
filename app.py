import streamlit as st
import os

st.set_page_config(
    page_title="SnapGuard - Private AI Protection",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from ui.dashboard import render_dashboard
from ui.scan import render_scan_page
from ui.results import render_results_page
from ui.history import render_history_page
from ui.privacy import render_privacy_page
from ui.settings import render_settings_page

# Session State Initialization
if "current_nav" not in st.session_state:
    st.session_state["current_nav"] = "🏠 Dashboard"

if "latest_scan_result" not in st.session_state:
    st.session_state["latest_scan_result"] = None

# Sidebar Navigation
st.sidebar.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <h2 style="color: #38bdf8; margin: 0;">🔐 SNAPGUARD</h2>
        <p style="color: #94a3b8; font-size: 12px;">Private AI Protection for Your PC</p>
    </div>
""", unsafe_allow_html=True)

nav_selection = st.sidebar.radio(
    "Navigation",
    ["🏠 Dashboard", "📄 Scan File", "🛡️ Analysis Results", "📜 History", "🔒 Privacy Center", "⚙️ Settings"],
    index=["🏠 Dashboard", "📄 Scan File", "🛡️ Analysis Results", "📜 History", "🔒 Privacy Center", "⚙️ Settings"].index(st.session_state["current_nav"])
)

st.session_state["current_nav"] = nav_selection

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚡ AI Status")
st.sidebar.markdown("Inference: `🟢 On-Device Local`")
st.sidebar.markdown("Qualcomm Hub: `Ready`")
st.sidebar.markdown("Privacy: `100% Private`")

def navigate_to_scan():
    st.session_state["current_nav"] = "📄 Scan File"
    st.rerun()

def navigate_to_results(result):
    st.session_state["latest_scan_result"] = result
    st.session_state["current_nav"] = "🛡️ Analysis Results"
    st.rerun()

# Router
if nav_selection == "🏠 Dashboard":
    render_dashboard(on_navigate_scan_cb=navigate_to_scan)
elif nav_selection == "📄 Scan File":
    render_scan_page(on_scan_complete_cb=navigate_to_results)
elif nav_selection == "🛡️ Analysis Results":
    render_results_page(st.session_state.get("latest_scan_result"))
elif nav_selection == "📜 History":
    render_history_page()
elif nav_selection == "🔒 Privacy Center":
    render_privacy_page()
elif nav_selection == "⚙️ Settings":
    render_settings_page()

import streamlit as st
from services.hardware import get_hardware_info

def render_privacy_page():
    """Render Privacy Center and Local AI Processing configuration."""
    hw_info = get_hardware_info()

    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h2 style="color: #38bdf8;">🔒 PRIVACY CENTER</h2>
            <p style="color: #94a3b8;">Transparent controls & guarantees regarding local AI execution and file security.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="glass-card">
            <h3 style="color: #f8fafc; font-size: 18px; margin-bottom: 15px;">PRIVACY DASHBOARD & GUARANTEES</h3>
    """, unsafe_allow_html=True)

    p1, p2 = st.columns(2)
    with p1:
        st.markdown("**Local Processing:** 🟢 `ON` (Enabled)")
        st.markdown("**Cloud Processing:** 🔴 `OFF` (Disabled)")
        st.markdown("**Files Uploaded Externally:** `NO` (All scans run 100% on-device)")
    with p2:
        st.markdown("**Stored File Contents:** `NO` (Only metadata saved in local SQLite)")
        st.markdown("**Network Telemetry:** `DISABLED` (Zero external network requests)")
        st.markdown(f"**Hardware Acceleration:** `{hw_info['acceleration']}`")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### How SnapGuard Protects Your Data")
    st.markdown("""
    - **100% On-Device Inference:** Text extraction, OCR, and NER classification run strictly on your local CPU or Snapdragon NPU.
    - **No Cloud Uploads:** Your sensitive files, documents, and credentials never leave your PC.
    - **Non-Destructive Redaction:** SnapGuard creates a new protected copy (`filename_PROTECTED`) and never overwrites your original file.
    - **Sanitized Metadata:** Scan logs store only file names, timestamp, risk levels, and item counts in local SQLite (`snapguard.db`).
    """)

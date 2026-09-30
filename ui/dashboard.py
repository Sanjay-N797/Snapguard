import streamlit as st
from database.database import get_stats
from services.hardware import get_hardware_info

def render_dashboard(on_navigate_scan_cb=None):
    """Render main landing dashboard."""
    stats = get_stats()
    hw_info = get_hardware_info()

    st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <h1 style="color: #38bdf8; margin-bottom: 5px;">🔐 SNAPGUARD</h1>
            <p style="color: #94a3b8; font-size: 18px; font-weight: 500;">Private AI Protection for Your PC</p>
            <p style="color: #64748b; font-size: 14px;">Detect sensitive information before it gets exposed.</p>
        </div>
    """, unsafe_allow_html=True)

    # Main Card Drop zone / CTA
    st.markdown("""
        <div class="glass-card" style="text-align: center; border: 2px dashed rgba(56, 189, 248, 0.4); padding: 40px 20px;">
            <div style="font-size: 48px; margin-bottom: 10px;">🛡️</div>
            <h2 style="color: #f8fafc; font-size: 22px; margin-bottom: 8px;">PROTECT YOUR DATA</h2>
            <p style="color: #94a3b8; font-size: 15px; margin-bottom: 20px;">
                Scan PDF documents, images, or code files for secret keys, passwords, IDs, and financial credentials.
            </p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("📄 START NEW SCAN NOW", use_container_width=True, type="primary"):
            if on_navigate_scan_cb:
                on_navigate_scan_cb()

    st.markdown("<br>", unsafe_allow_html=True)

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-number">{stats['scans_today']}</div>
                <div class="metric-label">Scans Today</div>
            </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-number" style="color: #f87171;">{stats['risks_found']}</div>
                <div class="metric-label">Risks Found</div>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-number" style="color: #4ade80;">{stats['files_protected']}</div>
                <div class="metric-label">Files Protected</div>
            </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-number" style="font-size: 20px; color: #a78bfa;">{hw_info['ai_mode']}</div>
                <div class="metric-label">Local AI Status</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Hardware & Snapdragon AI Panel
    st.markdown("""
        <div class="glass-card">
            <h3 style="color: #38bdf8; font-size: 18px; margin-bottom: 15px;">⚡ DEVICE AI & HARDWARE ACCELERATION</h3>
    """, unsafe_allow_html=True)

    h1, h2 = st.columns(2)
    with h1:
        st.markdown(f"**Processor:** {hw_info['processor']}")
        st.markdown(f"**AI Model:** {hw_info['ai_model']}")
        st.markdown(f"**Inference:** `{hw_info['inference']}`")
    with h2:
        st.markdown(f"**Acceleration Status:** `{hw_info['acceleration']}`")
        st.markdown(f"**Qualcomm AI Hub Backend:** {'🟢 Active & Compatible' if hw_info['qualcomm_ai_hub_ready'] else '⚪ Unavailable'}")
        if hw_info['is_snapdragon']:
            st.success("⚡ Qualcomm Snapdragon NPU Detected")
        else:
            st.info("ℹ️ Local CPU/ARM Acceleration Active")

    st.markdown("</div>", unsafe_allow_html=True)

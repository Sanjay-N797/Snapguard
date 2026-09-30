import streamlit as st
import os
from services.scanner import get_scanner

def render_scan_page(on_scan_complete_cb=None):
    """Render file upload & live scanning page."""
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h2 style="color: #38bdf8;">📄 SCAN FILE / CAMERA</h2>
            <p style="color: #94a3b8;">Select a file or take a live camera photo to analyze sensitive data locally.</p>
        </div>
    """, unsafe_allow_html=True)

    input_mode = st.radio(
        "Select Scan Mode",
        ["📄 Upload Document/Image", "📷 Camera Capture", "⚡ Instant Competition Demo Sample"],
        horizontal=True
    )

    file_name = None
    file_bytes = None

    if input_mode == "📄 Upload Document/Image":
        uploaded_file = st.file_uploader(
            "Choose a file to analyze",
            type=["pdf", "png", "jpg", "jpeg", "webp", "txt", "docx"],
            help="Supported: PDF, PNG, JPG, WEBP, TXT, DOCX"
        )
        if uploaded_file is not None:
            file_name = uploaded_file.name
            file_bytes = uploaded_file.getvalue()

    elif input_mode == "📷 Camera Capture":
        st.markdown("##### 📷 Live Camera Capture")
        col_cam1, col_cam2 = st.columns([3, 1])
        with col_cam1:
            camera_img = st.camera_input("Take a photo of document, ID, or screen")
        with col_cam2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Retake / Reset Camera", use_container_width=True):
                st.session_state.pop("camera_img", None)
                st.rerun()

        if camera_img is not None:
            file_name = "camera_snapshot.png"
            file_bytes = camera_img.getvalue()

    elif input_mode == "⚡ Instant Competition Demo Sample":
        st.info("💡 Instantly scan a sample confidential document with synthetic API keys, emails, SSN, and credit cards.")
        sample_choice = st.selectbox(
            "Select Demo Sample File",
            ["sample_confidential_document.pdf", "sample_id_card.png", "sample_credentials.txt"]
        )
        sample_path = os.path.join("data", "sample_docs", sample_choice)
        if os.path.exists(sample_path):
            if st.button("🚀 SCAN DEMO SAMPLE NOW", type="primary"):
                with open(sample_path, "rb") as f:
                    file_bytes = f.read()
                file_name = sample_choice

    if file_bytes is not None and file_name is not None:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**Selected Target:** `{file_name}` ({round(len(file_bytes)/1024, 1)} KB)")

        if st.button("🔍 START PRIVACY ANALYSIS", type="primary", use_container_width=True):
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            def update_progress(val, text):
                progress_bar.progress(val)
                status_text.markdown(f"**STATUS:** `{text}`")

            scanner = get_scanner()
            try:
                result = scanner.scan_file(file_name, file_bytes, progress_callback=update_progress)
                st.session_state["latest_scan_result"] = result
                st.success("✅ Analysis & Redaction completed successfully!")
                if on_scan_complete_cb:
                    on_scan_complete_cb(result)
            except Exception as e:
                st.error(f"❌ Scan Error: Unable to process target ({e})")

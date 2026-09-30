import streamlit as st
import os
import mimetypes
from config import SEVERITY_LEVELS
from services.redactor import get_redactor

def render_results_page(scan_result):
    """Render full security analysis results, OCR text, preview, and redaction suite."""
    if not scan_result:
        st.warning("No active scan result available. Please perform a file or camera scan first.")
        return

    filename = scan_result["filename"]
    risk_info = scan_result["risk_analysis"]
    score = risk_info["security_score"]
    risk_level = risk_info["risk_level"]
    findings = scan_result["findings"]
    full_text = scan_result.get("full_text", "")
    ocr_confidence = scan_result.get("ocr_confidence", 0.0)
    redact_res = scan_result.get("redaction_result", {})

    sev_meta = SEVERITY_LEVELS.get(risk_level, SEVERITY_LEVELS["MEDIUM"])

    # Header & Security Score
    st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 20px; border-radius: 12px; border-left: 4px solid #38bdf8; margin-bottom: 15px;">
            <span style="font-size: 20px; font-weight: 700; color: #38bdf8;">SCAN COMPLETE ✓</span>
        </div>
    """, unsafe_allow_html=True)

    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown(f"<h2 style='color: #38bdf8; margin-top: 0;'>🛡️ ANALYSIS: {filename}</h2>", unsafe_allow_html=True)
        st.markdown(f"**Scan Duration:** `{scan_result['processing_time']} sec` | **Items Found:** `{len(findings)}` | **Format:** `{scan_result['file_type'].upper()}`")
    with c_head2:
        score_color = "#4ade80" if score > 80 else ("#facc15" if score > 50 else "#f87171")
        st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.8); border: 2px solid {score_color}; border-radius: 16px; padding: 12px; text-align: center;">
                <div style="font-size: 11px; color: #94a3b8; letter-spacing: 1px;">SECURITY SCORE</div>
                <div style="font-size: 28px; font-weight: 800; color: {score_color};">{score} / 100</div>
                <div style="font-size: 12px; font-weight: 600; color: {sev_meta['color']};">{sev_meta['icon']} {risk_level}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info(f"💡 {risk_info['summary']}")

    # Tabs for Detailed Breakdown & Verification
    tab_overview, tab_findings, tab_preview, tab_redact, tab_before_after = st.tabs([
        "📋 Scan Summary & OCR",
        "🔍 Detected Risks",
        "🖼 Document Preview",
        "⚡ Redact & Download",
        "🔄 Before / After View"
    ])

    # 1. OCR TEXT & OVERVIEW TAB
    with tab_overview:
        st.markdown("### 📝 Extracted OCR Text")
        if ocr_confidence > 0:
            st.caption(f"Average OCR Confidence: `{round(ocr_confidence * 100, 1)}%`")
        
        if full_text and full_text.strip() and "No readable text detected" not in full_text:
            st.code(full_text, language="text")
        else:
            st.warning("⚠️ No readable text detected in this image/capture.")
            st.markdown("""
                *Possible reasons:*
                - Image is out of focus, blurry, or low lighting.
                - Document contains handwritten text (PaddleOCR targets printed text).
                - Text region is extremely small or obstructed.
            """)

    # 2. DETECTED RISKS TAB
    with tab_findings:
        st.markdown("### DETECTED RISKS")
        filter_option = st.radio("Filter Severity", ["All", "Critical", "High", "Medium"], horizontal=True)

        filtered_findings = findings
        if filter_option == "Critical":
            filtered_findings = [f for f in findings if f["severity"] == "CRITICAL"]
        elif filter_option == "High":
            filtered_findings = [f for f in findings if f["severity"] == "HIGH"]
        elif filter_option == "Medium":
            filtered_findings = [f for f in findings if f["severity"] == "MEDIUM"]

        if not filtered_findings:
            st.success("No sensitive risks match the selected filter criteria.")
        else:
            for item in filtered_findings:
                s_meta = SEVERITY_LEVELS.get(item["severity"], SEVERITY_LEVELS["MEDIUM"])
                with st.container():
                    st.markdown(f"""
                        <div class="glass-card" style="border-left: 5px solid {s_meta['color']}; margin-bottom: 12px; padding: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: 700; font-size: 15px; color: #f8fafc;">
                                    {s_meta['icon']} {item['title']}
                                </span>
                                <span style="background: {s_meta['badge_bg']}; color: {s_meta['color']}; font-weight: 600; font-size: 11px; padding: 2px 8px; border-radius: 4px;">
                                    {item['severity']} • Conf: {item['confidence']} • Page {item['page']}
                                </span>
                            </div>
                            <div style="margin-top: 6px; font-family: monospace; color: #38bdf8; font-size: 14px;">
                                Match: {item['masked_value']}
                            </div>
                            <div style="margin-top: 4px; font-size: 12px; color: #94a3b8;">
                                <strong>Why Sensitive:</strong> {item['explanation']}
                            </div>
                            <div style="margin-top: 2px; font-size: 12px; color: #4ade80;">
                                <strong>Recommended Action:</strong> {item['recommendation']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    # 3. DOCUMENT PREVIEW TAB
    with tab_preview:
        st.markdown("### 🖼 Document Preview & Visual Overlays")
        if scan_result.get("preview_image") is not None:
            st.image(scan_result["preview_image"], caption="Page 1 with Interactive Bounding Box Overlays", use_column_width=True)
        elif scan_result.get("pages"):
            st.markdown("**Page 1 Text Content:**")
            st.code(scan_result["pages"][0]["text"][:2000], language="text")
        else:
            st.info("No visual preview image available for this document.")

    # 4. REDACT & DOWNLOAD TAB
    with tab_redact:
        st.markdown("### 🛡️ PROTECTED FILE & DOWNLOAD")
        st.markdown("""
            Redacting replaces or blacks out sensitive credentials and outputs a safe protected file.  
            *SnapGuard never overwrites your original file.*
        """)

        redactor = get_redactor()

        col_red1, col_red2 = st.columns(2)
        with col_red1:
            if st.button("████ REDACT ALL SENSITIVE ITEMS", type="primary", use_container_width=True):
                new_redact_res = redactor.redact_document(
                    original_filename=filename,
                    file_type=scan_result["file_type"],
                    file_bytes=scan_result["file_bytes"],
                    scan_result=scan_result
                )
                scan_result["redaction_result"] = new_redact_res
                st.session_state["latest_scan_result"] = scan_result

        with col_red2:
            if st.button("🛡️ RE-GENERATE SAFE COPY", use_container_width=True):
                new_redact_res = redactor.redact_document(
                    original_filename=filename,
                    file_type=scan_result["file_type"],
                    file_bytes=scan_result["file_bytes"],
                    scan_result=scan_result
                )
                scan_result["redaction_result"] = new_redact_res
                st.session_state["latest_scan_result"] = scan_result

        st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)

        current_redact = scan_result.get("redaction_result", {})
        is_valid = current_redact.get("is_valid", False)
        protected_filename = current_redact.get("protected_filename", "")
        protected_path = current_redact.get("protected_path", "")

        if is_valid and protected_path and os.path.exists(protected_path):
            file_size_kb = round(os.path.getsize(protected_path) / 1024, 1)
            st.success(f"✅ Protected File Ready: `{protected_filename}` ({file_size_kb} KB)")

            mime_type, _ = mimetypes.guess_type(protected_path)
            if not mime_type:
                mime_type = "application/octet-stream"

            with open(protected_path, "rb") as file_data:
                st.download_button(
                    label=f"⬇️ DOWNLOAD {protected_filename}",
                    data=file_data,
                    file_name=protected_filename,
                    mime=mime_type,
                    use_container_width=True,
                    key="btn_download_protected_file"
                )
        else:
            err_msg = current_redact.get("error", "Unknown error")
            st.error(f"❌ Protected file could not be generated. Please try again. ({err_msg})")

    # 5. BEFORE / AFTER TAB
    with tab_before_after:
        st.markdown("### 🔄 BEFORE / AFTER REDACTION COMPARISON")
        b1, b2 = st.columns(2)
        with b1:
            st.markdown("#### BEFORE (Original Data)")
            if findings:
                sample_items = "\n".join([f"{item['title']}: {item['value']}" for item in findings[:5]])
                st.code(sample_items, language="text")
            else:
                st.code("No sensitive data found.", language="text")
        with b2:
            st.markdown("#### AFTER (Protected Redacted Copy)")
            if findings:
                redacted_sample = "\n".join([f"{item['title']}: ████████████" for item in findings[:5]])
                st.code(redacted_sample, language="text")
                st.success(f"🛡️ {len(findings)} items protected successfully")
            else:
                st.code("Document remains unaltered.", language="text")

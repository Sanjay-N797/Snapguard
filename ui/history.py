import streamlit as st
import pandas as pd
from database.database import get_history, delete_history

def render_history_page():
    """Render local scan history table and controls."""
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h2 style="color: #38bdf8;">📜 LOCAL SCAN HISTORY</h2>
            <p style="color: #94a3b8;">Review local scan metadata recorded on this PC. No sensitive raw contents are stored.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ DELETE HISTORY", type="secondary", use_container_width=True):
            delete_history()
            st.success("History log deleted successfully.")
            st.rerun()

    history_records = get_history(limit=50)

    if not history_records:
        st.info("No scan history recorded yet. Perform a scan to view history.")
        return

    df = pd.DataFrame(history_records)
    # Reorder and format display columns
    df_display = df[["id", "timestamp", "filename", "file_type", "risk_level", "security_score", "findings_count", "processing_time"]]
    df_display.columns = ["ID", "Timestamp", "Filename", "Type", "Risk Level", "Score", "Findings", "Duration (s)"]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

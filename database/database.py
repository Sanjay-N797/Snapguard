import sqlite3
import datetime
from config import DB_PATH

def init_db():
    """Initialize SQLite database schema for SnapGuard."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            file_type TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            security_score INTEGER NOT NULL,
            findings_count INTEGER NOT NULL,
            protected_filename TEXT,
            processing_time REAL,
            findings_summary TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS privacy_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_scan(filename, file_type, risk_level, security_score, findings_count, protected_filename="", processing_time=0.0, findings_summary=""):
    """Record a scan entry into local SQLite DB."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO scans (filename, timestamp, file_type, risk_level, security_score, findings_count, protected_filename, processing_time, findings_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (filename, timestamp, file_type, risk_level, security_score, findings_count, protected_filename, processing_time, findings_summary))
    
    scan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return scan_id

def get_history(limit=50):
    """Retrieve historical scan metadata."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM scans ORDER BY id DESC LIMIT ?', (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def delete_history():
    """Clear all scan metadata from history."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scans')
    cursor.execute('DELETE FROM privacy_logs')
    conn.commit()
    conn.close()
    return True

def get_stats():
    """Get aggregate dashboard statistics."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("SELECT COUNT(*) FROM scans WHERE timestamp LIKE ?", (f"{today_str}%",))
    scans_today = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(findings_count) FROM scans")
    res = cursor.fetchone()[0]
    risks_found = res if res else 0
    
    cursor.execute("SELECT COUNT(*) FROM scans WHERE protected_filename IS NOT NULL AND protected_filename != ''")
    files_protected = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scans")
    total_scans = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "scans_today": scans_today,
        "risks_found": risks_found,
        "files_protected": files_protected,
        "total_scans": total_scans
    }

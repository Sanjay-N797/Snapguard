# 🔐 SNAPGUARD: Private AI Protection for Your PC

> **Mission:** Privacy-focused, on-device AI application optimized for Snapdragon-powered HP PCs to detect, highlight, and redact sensitive information before sharing files.

---

## 1. Project Overview
SnapGuard is an on-device AI security application designed to protect sensitive personal and corporate data. It scans images, scanned documents, code files, and PDFs for secrets such as API keys, passwords, credit card numbers, identity documents, and confidential context, providing one-click redaction and generating safe shareable copies.

## 2. Problem
Users frequently share screenshots, PDFs, and code snippets online or with public AI tools without realizing that sensitive credentials (API tokens, private keys, passwords, SSNs, credit card numbers) are embedded in the text or image pixels. Once exposed, these secrets cause devastating breaches and financial loss.

## 3. Solution
SnapGuard provides an **instant, 100% local, on-device AI scanner** that runs directly on your PC's CPU/Snapdragon NPU. It analyzes files using a hybrid deterministic rule engine + Local Transformer NER classifier + PaddleOCR, calculates a real-time Security Score (0-100), highlights risks, and redacts them safely without touching your original file.

## 4. Key Features
- **Multi-Format Ingestion:** Ingest PNG, JPG, JPEG, WEBP, PDF, TXT, DOCX files or capture via Live Camera.
- **PaddleOCR Text Extraction:** High-accuracy local OCR for scanned documents and image text coordinates.
- **Hybrid Sensitive Detection:** Deterministic rules for high-confidence secrets (OpenAI, AWS, JWT, SSN, Credit Cards) + Local BERT NER for contextual classification.
- **Dynamic Security Scoring:** Dynamic 0–100 Security Score based on detected severity penalties (Critical: -25, High: -15, Medium: -5).
- **Visual Bounding Boxes & Text Highlighting:** Displays interactive overlays on image pixels and PDF page text.
- **One-Click Redaction & Safe Share:** Redacts all or selected findings (`████████████` / solid black pixel boxes) and outputs `filename_PROTECTED.ext`. Never overwrites original files.
- **BEFORE vs AFTER Comparison:** Visual side-by-side comparison of original secrets vs protected content.
- **Snapdragon / Device AI Status:** Real hardware detection interface displaying ARM, Apple Silicon, or Qualcomm Snapdragon NPU status.
- **Privacy Center:** Transparent zero-cloud guarantees, local SQLite audit history, and one-click history wipe.

## 5. Architecture
```text
snapguard/
├── app.py                      # Main Streamlit application entrypoint & tab router
├── config.py                   # Global configuration, regex rules, severities & scoring metrics
├── requirements.txt            # Python dependencies
├── README.md                   # Full documentation
├── .gitignore                  # Git ignore definitions
│
├── models/                     # AI & Detection Model Layer
│   ├── __init__.py
│   ├── detector.py             # Unified detection orchestrator (Rules + NER)
│   ├── ocr.py                  # PaddleOCR / EasyOCR / Fallback interface
│   ├── classifier.py           # Local HuggingFace Transformer NER (dslim/bert-base-NER)
│   └── local_llm.py            # Local LLM adapter & deterministic risk explainer
│
├── services/                   # Core Processing Services
│   ├── __init__.py
│   ├── scanner.py              # 4-Step scan workflow orchestrator
│   ├── risk_engine.py          # Dynamic 0-100 Security Scoring & Risk calculator
│   ├── redactor.py             # Safe PyMuPDF/PIL/Text one-click redaction engine
│   ├── document_processor.py   # PDF layout, TXT, and DOCX text extractor
│   ├── image_processor.py      # Bounding box drawer & pixel overlay engine
│   └── hardware.py             # Snapdragon ARM / NPU & Hardware detection
│
├── database/                   # Data Layer
│   ├── __init__.py
│   └── database.py             # Local SQLite DB (snapguard.db) for scan metadata & history
│
├── ui/                         # Streamlit UI Components
│   ├── __init__.py
│   ├── dashboard.py            # Main landing dashboard, stats, & CTA
│   ├── scan.py                 # File upload, camera capture, & progress animation
│   ├── results.py              # Security score, findings cards, preview, & redaction
│   ├── history.py              # Local scan audit table & history wipe button
│   ├── privacy.py              # Privacy Center transparency & toggles
│   └── settings.py             # AI threshold, category filters, & options
│
├── data/
│   └── sample_docs/            # Built-in synthetic test sample documents
├── outputs/                    # Export directory for redacted protected files
└── assets/
    └── style.css               # Dark professional security CSS theme
```

## 6. AI Models
- **Local Contextual NER:** `dslim/bert-base-NER` (compact transformer) or local entity pattern classifier.
- **Local Explanation Adapter:** `models/local_llm.py` provides plain-language explanations for why items are flagged and recommends actions. Supports local Ollama endpoint or deterministic rule-based fallback.

## 7. OCR Engine
- **PaddleOCR Engine:** `models/ocr.py` uses PaddleOCR for bounding box extraction `[x1, y1, x2, y2]` and text line extraction. Includes EasyOCR / PyMuPDF fallback for maximum platform compatibility.

## 8. Detection Engine
- **Deterministic Rules (High Confidence):**
  - **API Keys:** AWS (`AKIA...`), OpenAI (`sk-...`), GitHub (`ghp_...`), Bearer tokens, Generic Key assignments (`api_key = ...`).
  - **Passwords:** Plaintext password patterns (`password = ...`, `db_pass: ...`).
  - **JWT Tokens:** Session tokens (`eyJ...`).
  - **Financial:** Credit/Debit card Primary Account Numbers (PAN).
  - **Identity:** Social Security Numbers (SSN), Passport numbers.
  - **Network:** IPv4 addresses, URLs with embedded credentials (`http://user:pass@host`).
- **Severities:**
  - 🔴 **CRITICAL:** Passwords, API Keys, JWT Tokens, Private Keys (-25 score penalty).
  - 🟠 **HIGH:** SSN, Credit Cards, Identity Docs (-15 score penalty).
  - 🟡 **MEDIUM:** Phone Numbers, Email Addresses, IP Addresses (-5 score penalty).

## 9. Privacy Design
- **100% On-Device:** All AI inference, OCR, and redactions execute locally.
- **Zero Cloud Uploads:** No file contents leave your computer.
- **Non-Destructive:** Outputs `filename_PROTECTED.ext` in `outputs/`.
- **Sanitized Metadata:** SQLite database stores only scan metrics (filename, score, timestamp, count).

## 10. Local AI & Performance
Runs efficiently on standard CPUs and ARM processors, using low-overhead inference models.

## 11. Snapdragon Optimization
Designed specifically for ARM64 and Snapdragon-powered PCs. Detects hardware platform via `services/hardware.py` and reports execution status transparently.

## 12. Qualcomm AI Hub Integration Path
`models/detector.py`, `models/ocr.py`, `models/classifier.py`, and `models/local_llm.py` implement modular object interfaces. When Qualcomm AI Hub ONNX / QNN Execution Providers are present on target Snapdragon PCs, these interfaces map directly to Qualcomm NPU models without breaking UI contracts.

## 13. Installation

1. Clone or navigate to the repository:
   ```bash
   cd snapguard
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 14. Model Setup
Models download automatically on first execution via HuggingFace / PaddleOCR local caches.

## 15. Running Instructions
Start the SnapGuard Streamlit application:
```bash
streamlit run app.py
```
Then open your browser to `http://localhost:8501`.

## 16. Demo Instructions (2-Minute Competition Demo)
1. **Open Application:** Launch `streamlit run app.py`.
2. **Navigate to Scan:** Click **📄 SCAN FILE**.
3. **Select Instant Demo Sample:** Choose **⚡ Instant Competition Demo Sample** and click **🚀 SCAN DEMO SAMPLE NOW** or upload `data/sample_docs/sample_confidential_document.pdf`.
4. **View Live Analysis:** Observe 4-step progress: OCR -> Rule Engine -> Context NER -> Risk Scoring.
5. **Inspect Security Score:** Review dynamic Security Score (e.g. `20 / 100`) and 🔴 CRITICAL risk badge.
6. **Review Findings:** Filter findings by Critical, High, Medium to inspect flagged API keys, SSN, and passwords.
7. **One-Click Redact:** Click **████ REDACT ALL SENSITIVE ITEMS** or **🛡️ CREATE SAFE SHARE COPY**.
8. **BEFORE vs AFTER:** Switch to **🔄 Before / After View** tab to see original vs redacted comparison.
9. **Download Protected File:** Click **⬇️ DOWNLOAD sample_confidential_document_PROTECTED.pdf**.
10. **Verify Privacy & AI Status:** Click **🔒 Privacy Center** to display On-Device execution guarantees and Snapdragon hardware panel.

## 17. Limitations
- PDF redaction quality on scanned documents depends on OCR coordinate alignment.
- Local LLM explanation richness depends on local memory resources.

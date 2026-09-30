import os
import time
import io
from PIL import Image
from services.ocr_service import get_ocr_service
from models.detector import get_detector
from services.document_processor import get_document_processor
from services.image_processor import get_image_processor
from services.risk_engine import get_risk_engine
from services.redactor import get_redactor
from database.database import save_scan

class ScanWorkflowOrchestrator:
    """
    Orchestrates the full 4-step scan pipeline:
    OCR/Extraction -> Sensitive Detection -> Context Classification -> Risk & Redaction.
    """
    def scan_file(self, file_name, file_bytes, progress_callback=None):
        """
        Execute full scan on uploaded file or camera image bytes.
        """
        start_time = time.time()
        ext = os.path.splitext(file_name)[1].lower()

        # Step 1: OCR / Document Text Extraction
        if progress_callback:
            progress_callback(0.20, "1. Extracting text & running PaddleOCR with preprocessing...")

        ocr_service = get_ocr_service()
        doc_processor = get_document_processor()
        img_processor = get_image_processor()
        detector = get_detector()
        risk_engine = get_risk_engine()
        redactor = get_redactor()

        pages = []
        full_text = ""
        ocr_results = []
        avg_confidence = 0.0

        is_image = ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"] or not ext

        if is_image:
            pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            ocr_text, ocr_results, avg_confidence = ocr_service.extract_text_with_boxes(file_bytes)
            full_text = ocr_text
            pages.append({
                "page_num": 1,
                "text": ocr_text,
                "image": pil_img,
                "width": pil_img.width,
                "height": pil_img.height
            })
            file_kind = "image"
        else:
            doc_data = doc_processor.extract_document(file_bytes, file_name)
            pages = doc_data["pages"]
            full_text = doc_data["full_text"]
            file_kind = doc_data["file_type"]

            ocr_confidences = []
            for page in pages:
                if not page["text"] or len(page["text"].strip()) < 15:
                    if page.get("image") is not None:
                        ocr_text, p_ocr_res, p_conf = ocr_service.extract_text_with_boxes(page["image"])
                        page["text"] = ocr_text
                        ocr_results.extend(p_ocr_res)
                        if p_conf > 0:
                            ocr_confidences.append(p_conf)
                        if ocr_text and "No readable text detected" not in ocr_text:
                            full_text += f"\n{ocr_text}"

            if ocr_confidences:
                import numpy as np
                avg_confidence = round(float(np.mean(ocr_confidences)), 4)

        # Step 2 & 3: Sensitive Data Detection & Classification
        if progress_callback:
            progress_callback(0.55, "2. Running Rule Engine & Contextual NER Classifier...")

        all_findings = []
        for page in pages:
            page_text = page["text"]
            page_num = page["page_num"]
            p_findings = detector.detect_in_text(page_text, page_number=page_num)
            all_findings.extend(p_findings)

        # Step 4: Risk Scoring & Security Assessment
        if progress_callback:
            progress_callback(0.80, "3. Calculating Security Score & Generating Protected Output...")

        risk_analysis = risk_engine.calculate_risk(all_findings)
        processing_time = round(time.time() - start_time, 2)

        # Generate visual bounding box overlays for preview
        preview_image = None
        if pages and pages[0].get("image") is not None:
            preview_image = img_processor.draw_bounding_boxes(pages[0]["image"], ocr_results, all_findings)

        # Draft partial result structure for redactor (omit raw binary bytes from JSON dict)
        scan_result_draft = {
            "filename": file_name,
            "file_type": file_kind,
            "full_text": full_text,
            "pages": pages,
            "ocr_results": ocr_results,
            "ocr_confidence": avg_confidence,
            "findings": all_findings,
            "risk_analysis": risk_analysis,
            "processing_time": processing_time,
            "preview_image": preview_image
        }

        # Auto-generate protected redacted file
        redact_res = redactor.redact_document(
            original_filename=file_name,
            file_type=file_kind,
            file_bytes=file_bytes,
            scan_result=scan_result_draft
        )

        if progress_callback:
            progress_callback(1.0, "4. Scan complete!")

        # Record scan entry into local SQLite DB
        findings_summary = f"{risk_analysis['findings_count']} items found ({risk_analysis['counts_by_severity']})"
        scan_id = save_scan(
            filename=file_name,
            file_type=file_kind,
            risk_level=risk_analysis["risk_level"],
            security_score=risk_analysis["security_score"],
            findings_count=risk_analysis["findings_count"],
            protected_filename=redact_res.get("protected_filename", ""),
            processing_time=processing_time,
            findings_summary=findings_summary
        )

        scan_result_draft["scan_id"] = scan_id
        scan_result_draft["redaction_result"] = redact_res

        return scan_result_draft

_scanner_instance = None

def get_scanner():
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = ScanWorkflowOrchestrator()
    return _scanner_instance

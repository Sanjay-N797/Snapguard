import os
import io
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
from config import OUTPUTS_DIR
from services.image_processor import get_image_processor

class RedactorService:
    """
    Safe One-Click Redaction Engine.
    Redacts sensitive items from PDFs, Images, and Text files.
    NEVER overwrites the original file — outputs filename_PROTECTED.ext in outputs/.
    """
    def redact_document(self, original_filename, file_type, file_bytes, scan_result, selected_finding_ids=None):
        """
        Execute redaction and return structured dictionary:
        {
            'is_valid': bool,
            'protected_filename': str,
            'protected_path': str,
            'error': str
        }
        """
        base_name, ext = os.path.splitext(original_filename)
        if not ext:
            ext = ".png" if file_type == "image" else ".txt"

        safe_base = "".join(c for c in base_name if c.isalnum() or c in ("-", "_", " "))
        if not safe_base:
            safe_base = "file"

        protected_filename = f"{safe_base}_PROTECTED{ext}"
        protected_path = os.path.join(OUTPUTS_DIR, protected_filename)

        findings = scan_result.get("findings", [])
        if selected_finding_ids is not None:
            active_findings = [f for f in findings if f["id"] in selected_finding_ids]
        else:
            active_findings = [f for f in findings if f.get("selected", True)]

        try:
            if file_type == "pdf":
                self._redact_pdf(file_bytes, protected_path, active_findings)
            elif file_type in ["image", "png", "jpg", "jpeg", "webp"]:
                self._redact_image(file_bytes, protected_path, scan_result.get("ocr_results", []), active_findings)
            elif file_type in ["txt", "docx"]:
                self._redact_text(scan_result.get("full_text", ""), protected_path, active_findings)
            else:
                self._redact_text(scan_result.get("full_text", ""), protected_path, active_findings)

            # Verification of output file
            is_valid, err_msg = self.verify_protected_file(protected_path, file_type, active_findings)

            if is_valid:
                return {
                    "is_valid": True,
                    "protected_filename": protected_filename,
                    "protected_path": protected_path,
                    "error": None
                }
            else:
                return {
                    "is_valid": False,
                    "protected_filename": protected_filename,
                    "protected_path": protected_path,
                    "error": err_msg
                }

        except Exception as e:
            print(f"[SnapGuard Redactor] Error during redaction: {e}")
            return {
                "is_valid": False,
                "protected_filename": protected_filename,
                "protected_path": protected_path,
                "error": str(e)
            }

    def _redact_pdf(self, file_bytes, output_path, findings):
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        for finding in findings:
            target_val = finding["value"]
            page_num = finding.get("page", 1)
            if page_num <= len(doc):
                page = doc[page_num - 1]
                # Search exact text occurrences on page
                text_instances = page.search_for(target_val)
                for rect in text_instances:
                    page.add_redact_annot(rect, fill=(0, 0, 0))

        # Apply redactions across all pages
        for page in doc:
            page.apply_redactions()

        doc.save(output_path)
        doc.close()
        return output_path

    def _redact_image(self, file_bytes, output_path, ocr_results, findings):
        pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        img_processor = get_image_processor()
        redacted_img = img_processor.redact_image_boxes(pil_img, ocr_results, findings)

        # Save preserving image extension format
        ext = os.path.splitext(output_path)[1].lower()
        if ext in [".jpg", ".jpeg"]:
            redacted_img.save(output_path, format="JPEG", quality=95)
        elif ext == ".webp":
            redacted_img.save(output_path, format="WEBP")
        else:
            redacted_img.save(output_path, format="PNG")
        return output_path

    def _redact_text(self, text_content, output_path, findings):
        redacted_text = text_content
        for finding in findings:
            val = finding["value"]
            mask_str = "█" * max(8, len(val))
            redacted_text = redacted_text.replace(val, mask_str)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(redacted_text)
        return output_path

    def verify_protected_file(self, protected_path, file_type, active_findings):
        """
        Verify that protected output file exists, is non-empty, and valid.
        """
        if not os.path.exists(protected_path):
            return False, "Output file does not exist."

        file_size = os.path.getsize(protected_path)
        if file_size == 0:
            return False, "Output file is empty (0 bytes)."

        if file_type == "pdf":
            try:
                doc = fitz.open(protected_path)
                page_count = len(doc)
                doc.close()
                if page_count == 0:
                    return False, "Generated PDF has 0 pages."
            except Exception as e:
                return False, f"Invalid PDF output: {e}"

        elif file_type in ["image", "png", "jpg", "jpeg", "webp"]:
            try:
                img = Image.open(protected_path)
                img.verify()
            except Exception as e:
                return False, f"Invalid Image output: {e}"

        elif file_type in ["txt", "docx"]:
            try:
                with open(protected_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for finding in active_findings:
                    val = finding["value"]
                    if val in content and len(val) > 3:
                        return False, f"Sensitive text '{val}' still present in redacted output."
            except Exception as e:
                return False, f"Failed to read text output: {e}"

        return True, None

_redactor_instance = None

def get_redactor():
    global _redactor_instance
    if _redactor_instance is None:
        _redactor_instance = RedactorService()
    return _redactor_instance

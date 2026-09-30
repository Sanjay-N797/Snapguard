import os
import fitz  # PyMuPDF
from PIL import Image
import io

class DocumentProcessor:
    """
    Document Processor for PDF, TXT, and DOCX files.
    Preserves page numbers, extracts embedded text, and renders page images for OCR.
    """
    def extract_document(self, file_path_or_bytes, file_name):
        """
        Process a document input and return structured page text and render page images.
        Returns:
        {
            'file_type': 'pdf'|'txt'|'docx',
            'pages': [{'page_num': int, 'text': str, 'image': PIL.Image, 'rects': list}],
            'full_text': str
        }
        """
        ext = os.path.splitext(file_name)[1].lower()

        if ext == ".pdf":
            return self._process_pdf(file_path_or_bytes)
        elif ext in [".txt", ".log", ".csv", ".env"]:
            return self._process_txt(file_path_or_bytes)
        elif ext in [".docx", ".doc"]:
            return self._process_docx(file_path_or_bytes)
        else:
            raise ValueError(f"Unsupported document format: {ext}")

    def _process_pdf(self, file_input):
        if isinstance(file_input, str):
            doc = fitz.open(file_input)
        elif isinstance(file_input, bytes):
            doc = fitz.open(stream=file_input, filetype="pdf")
        else:
            file_bytes = file_input.read()
            doc = fitz.open(stream=file_bytes, filetype="pdf")

        pages = []
        full_text_list = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1
            text = page.get_text()

            # Render page image (150 DPI) for OCR and preview bounding boxes
            pix = page.get_pixmap(dpi=150)
            img_data = pix.tobytes("png")
            pil_img = Image.open(io.BytesIO(img_data)).convert("RGB")

            pages.append({
                "page_num": page_num,
                "text": text,
                "image": pil_img,
                "width": page.rect.width,
                "height": page.rect.height
            })
            if text and text.strip():
                full_text_list.append(f"--- Page {page_num} ---\n{text}")

        doc.close()
        full_text = "\n\n".join(full_text_list)

        return {
            "file_type": "pdf",
            "pages": pages,
            "full_text": full_text
        }

    def _process_txt(self, file_input):
        if isinstance(file_input, str):
            with open(file_input, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        elif isinstance(file_input, bytes):
            content = file_input.decode("utf-8", errors="ignore")
        else:
            content = file_input.getvalue().decode("utf-8", errors="ignore")

        return {
            "file_type": "txt",
            "pages": [{
                "page_num": 1,
                "text": content,
                "image": None,
                "width": 800,
                "height": 1000
            }],
            "full_text": content
        }

    def _process_docx(self, file_input):
        try:
            import docx
            if isinstance(file_input, str):
                doc = docx.Document(file_input)
            else:
                doc = docx.Document(file_input)
            
            text_lines = [para.text for para in doc.paragraphs if para.text]
            full_text = "\n".join(text_lines)
            
            return {
                "file_type": "docx",
                "pages": [{
                    "page_num": 1,
                    "text": full_text,
                    "image": None,
                    "width": 800,
                    "height": 1000
                }],
                "full_text": full_text
            }
        except Exception as e:
            print(f"[SnapGuard DocumentProcessor] DOCX processing note: {e}")
            return self._process_txt(file_input)

_doc_processor_instance = None

def get_document_processor():
    global _doc_processor_instance
    if _doc_processor_instance is None:
        _doc_processor_instance = DocumentProcessor()
    return _doc_processor_instance

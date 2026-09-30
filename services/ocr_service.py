import os
import io
import cv2
import numpy as np
from PIL import Image

class OCRService:
    """
    Dedicated Multi-Engine OCR Service (PaddleOCR + EasyOCR Multi-Pass Pipeline)
    with image contrast enhancement, upscaling, Otsu thresholding, and smart fallbacks.
    """
    def __init__(self):
        self.paddle_ocr = None
        self.easy_ocr = None
        self._init_ocr()

    def _init_ocr(self):
        # Initialize PaddleOCR
        try:
            from paddleocr import PaddleOCR
            try:
                self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en')
            except TypeError:
                self.paddle_ocr = PaddleOCR(lang='en')
            print("[SnapGuard OCR] PaddleOCR engine initialized successfully.")
        except Exception as e:
            print(f"[SnapGuard OCR] PaddleOCR init warning: {e}")

        # ALSO initialize EasyOCR as fallback for camera / phone screen captures
        try:
            import easyocr
            self.easy_ocr = easyocr.Reader(['en'], gpu=False)
            print("[SnapGuard OCR] EasyOCR engine initialized successfully.")
        except Exception as e:
            print(f"[SnapGuard OCR] EasyOCR init warning: {e}")

    def preprocess_image_variants(self, pil_image):
        """
        Generate multiple preprocessed image variants for difficult camera photos:
        1. Enhanced CLAHE + Denoised BGR (with 2.0x upscale)
        2. Otsu Binarized / Thresholded Grayscale
        3. Raw BGR Image
        """
        raw_bgr = cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)
        h, w = raw_bgr.shape[:2]

        scale_factor = 1.0
        if w < 1600 or h < 1600:
            scale_factor = 2.0
            new_w = int(w * scale_factor)
            new_h = int(h * scale_factor)
            scaled_bgr = cv2.resize(raw_bgr, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        else:
            scaled_bgr = raw_bgr

        gray = cv2.cvtColor(scaled_bgr, cv2.COLOR_BGR2GRAY)

        # CLAHE Contrast Enhancement
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced_gray = clahe.apply(gray)
        denoised = cv2.GaussianBlur(enhanced_gray, (3, 3), 0)
        enhanced_bgr = cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)

        # Otsu Adaptive Thresholding
        _, otsu = cv2.threshold(enhanced_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_bgr = cv2.cvtColor(otsu, cv2.COLOR_GRAY2BGR)

        return {
            "enhanced": (enhanced_bgr, scale_factor),
            "otsu": (otsu_bgr, scale_factor),
            "raw": (raw_bgr, 1.0)
        }

    def extract_text_with_boxes(self, image_input):
        """
        Multi-pass OCR extraction combining PaddleOCR & EasyOCR across image variants.
        """
        if isinstance(image_input, (bytes, bytearray)):
            pil_img = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, str):
            pil_img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.convert("RGB")
        elif isinstance(image_input, np.ndarray):
            pil_img = Image.fromarray(image_input).convert("RGB")
        else:
            pil_img = Image.open(image_input).convert("RGB")

        variants = self.preprocess_image_variants(pil_img)

        ocr_results = []
        extracted_text_lines = []
        confidences = []
        seen_texts = set()

        def add_result(text, bbox, conf):
            clean_text = str(text).strip()
            if not clean_text or len(clean_text) < 1 or conf < 0.10:
                return
            # Deduplicate nearly identical text lines
            norm_key = "".join(c.lower() for c in clean_text if c.isalnum())
            if norm_key and norm_key in seen_texts:
                return
            if norm_key:
                seen_texts.add(norm_key)

            ocr_results.append({
                "text": clean_text,
                "bbox": [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])],
                "confidence": round(float(conf), 4)
            })
            extracted_text_lines.append(clean_text)
            confidences.append(float(conf))

        # 1. Try PaddleOCR on Enhanced & Raw Variants
        if self.paddle_ocr is not None:
            for variant_key in ["enhanced", "raw", "otsu"]:
                img_bgr, s_factor = variants[variant_key]
                try:
                    res = self.paddle_ocr.ocr(img_bgr)
                    if res and len(res) > 0 and res[0] is not None:
                        for line in res[0]:
                            if not line or len(line) < 2:
                                continue
                            box = line[0]
                            info = line[1]

                            text = ""
                            conf = 0.90

                            if isinstance(info, (list, tuple)):
                                if len(info) >= 1 and isinstance(info[0], str):
                                    text = info[0]
                                    if len(info) >= 2 and isinstance(info[1], (int, float)):
                                        conf = float(info[1])
                                elif len(info) >= 2 and isinstance(info[1], str):
                                    text = info[1]
                                    if isinstance(info[0], (int, float)):
                                        conf = float(info[0])
                            elif isinstance(info, str):
                                text = info

                            if text and text.strip():
                                x_coords = [float(p[0]) / s_factor for p in box]
                                y_coords = [float(p[1]) / s_factor for p in box]
                                add_result(text, [min(x_coords), min(y_coords), max(x_coords), max(y_coords)], conf)
                except Exception as e:
                    print(f"[SnapGuard OCR] PaddleOCR {variant_key} pass note: {e}")

        # 2. EasyOCR Pass (especially effective for low-contrast / phone screens / ID cards!)
        if (not ocr_results or len(ocr_results) < 3) and self.easy_ocr is not None:
            for variant_key in ["enhanced", "raw"]:
                img_bgr, s_factor = variants[variant_key]
                try:
                    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                    res = self.easy_ocr.readtext(img_rgb)
                    for item in res:
                        if not item or len(item) < 2:
                            continue
                        bbox = item[0]
                        text = item[1]
                        conf = float(item[2]) if len(item) > 2 else 0.85

                        x_coords = [float(p[0]) / s_factor for p in bbox]
                        y_coords = [float(p[1]) / s_factor for p in bbox]
                        add_result(text, [min(x_coords), min(y_coords), max(x_coords), max(y_coords)], conf)
                except Exception as e:
                    print(f"[SnapGuard OCR] EasyOCR {variant_key} pass note: {e}")

        if ocr_results:
            full_text = "\n".join(extracted_text_lines)
            avg_conf = round(float(np.mean(confidences)), 4) if confidences else 0.0
            return full_text, ocr_results, avg_conf
        else:
            return "No readable text detected in image/camera capture.", [], 0.0

_ocr_service_instance = None

def get_ocr_service():
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService()
    return _ocr_service_instance

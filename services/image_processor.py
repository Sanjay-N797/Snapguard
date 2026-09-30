import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from config import SEVERITY_LEVELS

class ImageProcessor:
    """
    Image processing service for loading images, rendering visual bounding box overlays,
    and creating redacted pixel images over sensitive text regions.
    """
    def draw_bounding_boxes(self, pil_image, ocr_results, findings):
        """
        Draw visual bounding boxes and labels on image corresponding to detected sensitive text.
        """
        if pil_image is None:
            return None

        img_copy = pil_image.copy()
        draw = ImageDraw.Draw(img_copy, "RGBA")

        # Map findings to OCR bounding boxes by string matching
        for finding in findings:
            val = finding["value"].lower().strip()
            severity = finding.get("severity", "MEDIUM")
            category_title = finding.get("title", "Sensitive Item")

            color_hex = SEVERITY_LEVELS.get(severity, {}).get("color", "#ff4d4f")
            rgb_color = self._hex_to_rgb(color_hex)
            overlay_color = (rgb_color[0], rgb_color[1], rgb_color[2], 60)
            outline_color = (rgb_color[0], rgb_color[1], rgb_color[2], 255)

            for item in ocr_results:
                ocr_text = item["text"].lower().strip()
                bbox = item.get("bbox")

                if not bbox or len(bbox) < 4:
                    continue

                # Check if finding value is in OCR text or vice versa or sub-parts
                if val in ocr_text or ocr_text in val or any(part in ocr_text for part in val.split() if len(part) > 3):
                    x1, y1, x2, y2 = bbox
                    pad = 4
                    rect_coords = [max(0, x1 - pad), max(0, y1 - pad), x2 + pad, y2 + pad]

                    # Draw filled rectangle with transparency
                    draw.rectangle(rect_coords, fill=overlay_color, outline=outline_color, width=3)

                    # Draw category badge label
                    label_text = f" {severity}: {category_title} "
                    badge_height = 20
                    draw.rectangle([rect_coords[0], max(0, rect_coords[1] - badge_height), rect_coords[0] + len(label_text) * 7, rect_coords[1]], fill=outline_color)
                    draw.text((rect_coords[0] + 2, max(0, rect_coords[1] - (badge_height - 2))), label_text, fill=(255, 255, 255, 255))

        return img_copy

    def redact_image_boxes(self, pil_image, ocr_results, findings):
        """
        Create a clean redacted version of an image by drawing solid black rectangles
        over all detected sensitive bounding box regions.
        """
        if pil_image is None:
            return None

        redacted_img = pil_image.copy().convert("RGB")
        draw = ImageDraw.Draw(redacted_img)

        for finding in findings:
            val = finding["value"].lower().strip()
            for item in ocr_results:
                ocr_text = item["text"].lower().strip()
                bbox = item.get("bbox")

                if not bbox or len(bbox) < 4:
                    continue

                if val in ocr_text or ocr_text in val or any(part in ocr_text for part in val.split() if len(part) > 3):
                    x1, y1, x2, y2 = bbox
                    pad = 4
                    rect_coords = [max(0, x1 - pad), max(0, y1 - pad), x2 + pad, y2 + pad]
                    draw.rectangle(rect_coords, fill=(0, 0, 0))

        return redacted_img

    def _hex_to_rgb(self, hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

_image_processor_instance = None

def get_image_processor():
    global _image_processor_instance
    if _image_processor_instance is None:
        _image_processor_instance = ImageProcessor()
    return _image_processor_instance

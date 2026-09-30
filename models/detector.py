import re
from config import REGEX_PATTERNS, CATEGORIES, SEVERITY_LEVELS
from models.classifier import get_classifier
from models.local_llm import get_local_llm

class SensitiveDataDetector:
    """
    Unified Sensitive Data Detection Engine.
    Combines deterministic regex rule evaluation + local NER contextual classification.
    """
    def __init__(self):
        self.classifier = get_classifier()
        self.local_llm = get_local_llm()

    def detect_in_text(self, text, page_number=1):
        """
        Scan a string for sensitive information.
        Returns a list of finding objects:
        [{
            'id': str,
            'category': str,
            'title': str,
            'severity': 'CRITICAL'|'HIGH'|'MEDIUM',
            'value': str,
            'masked_value': str,
            'confidence': 'High'|'Medium'|'Low',
            'page': int,
            'explanation': str,
            'recommendation': str,
            'start': int,
            'end': int
        }]
        """
        if not text or not isinstance(text, str):
            return []

        raw_findings = []
        item_id_counter = 1

        # 1. Deterministic Regex Evaluation
        for rule in REGEX_PATTERNS:
            cat_key = rule["category"]
            pattern = rule["pattern"]
            conf = rule["confidence"]
            rule_label = rule["label"]
            cat_info = CATEGORIES.get(cat_key, {})
            severity = cat_info.get("severity", "MEDIUM")

            try:
                for match in re.finditer(pattern, text):
                    matched_val = match.group(0).strip()
                    if not matched_val or len(matched_val) < 3:
                        continue

                    # Mask sensitive value for secure storage/logging
                    masked = self._mask_value(matched_val, cat_key)

                    explanation_obj = self.local_llm.explain_finding(cat_key, matched_val)

                    raw_findings.append({
                        "id": f"det_{page_number}_{item_id_counter}",
                        "category": cat_key,
                        "title": cat_info.get("title", rule_label),
                        "severity": severity,
                        "value": matched_val,
                        "masked_value": masked,
                        "confidence": conf,
                        "page": page_number,
                        "explanation": explanation_obj["explanation"],
                        "recommendation": explanation_obj["recommendation"],
                        "start": match.start(),
                        "end": match.end(),
                        "selected": True
                    })
                    item_id_counter += 1
            except Exception as e:
                print(f"[SnapGuard Detector] Regex match error for pattern {rule_label}: {e}")

        # 2. Contextual NER Classification
        ner_entities = self.classifier.classify_text(text)
        for ent in ner_entities:
            cat_key = ent["category"]
            matched_val = ent["text"]
            cat_info = CATEGORIES.get(cat_key, {})
            severity = cat_info.get("severity", "HIGH")
            masked = self._mask_value(matched_val, cat_key)
            explanation_obj = self.local_llm.explain_finding(cat_key, matched_val)

            raw_findings.append({
                "id": f"det_{page_number}_{item_id_counter}",
                "category": cat_key,
                "title": cat_info.get("title", ent["label"]),
                "severity": severity,
                "value": matched_val,
                "masked_value": masked,
                "confidence": ent["confidence"],
                "page": page_number,
                "explanation": explanation_obj["explanation"],
                "recommendation": explanation_obj["recommendation"],
                "start": ent["start"],
                "end": ent["end"],
                "selected": True
            })
            item_id_counter += 1

        # 3. Deduplicate overlapping matches
        deduped = self._deduplicate_findings(raw_findings)
        return deduped

    def _mask_value(self, val, category):
        if not val:
            return ""
        if category in ["password", "api_key", "jwt_token", "private_key"]:
            if len(val) <= 8:
                return "********"
            return val[:3] + "..." + val[-3:]
        elif category == "email":
            parts = val.split("@")
            if len(parts) == 2:
                name = parts[0]
                domain = parts[1]
                masked_name = name[0] + "***" if len(name) > 1 else "*"
                return f"{masked_name}@{domain}"
            return val[0] + "***"
        elif category == "credit_card":
            clean_digits = re.sub(r'\D', '', val)
            if len(clean_digits) >= 12:
                return f"****-****-****-{clean_digits[-4:]}"
            return "****-****-****-****"
        elif category == "phone":
            return val[:3] + "***" + val[-2:]
        elif category == "identity_number":
            return "***-**-" + val[-4:] if len(val) >= 4 else "***-**-****"
        else:
            return val[:2] + "..." + val[-2:] if len(val) > 4 else "████"

    def _deduplicate_findings(self, findings):
        seen_values = set()
        unique_list = []
        for item in findings:
            val = item["value"].strip()
            key = f"{item['page']}_{item['category']}_{val}"
            if key not in seen_values:
                seen_values.add(key)
                unique_list.append(item)
        return unique_list

_detector_instance = None

def get_detector():
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SensitiveDataDetector()
    return _detector_instance

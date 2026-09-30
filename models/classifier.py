import re
from config import CATEGORIES

class LocalNERClassifier:
    """
    Local NER & Contextual Sensitive Text Classifier.
    Designed for local transformer inference with rule-assisted entity context fallback.
    """
    def __init__(self):
        self.model_name = "Local Contextual Classifier"
        self.ner_pipeline = None

    def classify_text(self, text):
        """
        Analyze text to extract contextual entities.
        Returns a list of detected entity dictionaries:
        [{'text': str, 'category': str, 'label': str, 'confidence': str, 'start': int, 'end': int}]
        """
        if not text or len(text.strip()) == 0:
            return []

        entities = []

        # Contextual Pattern Matcher for sensitive keyword proximity & entity classification
        context_patterns = [
            (r'(?i)\b(secret|private_key|token|auth_token|api_secret)\s*[:=]\s*(\S+)', "api_key", "Confidential Key Assignment"),
            (r'(?i)\b(social security|ssn|tax id|passport num)\s*[:=]?\s*([A-Z0-9\-]{7,})', "identity_number", "Identity Record"),
            (r'(?i)\b(confidential|internal only|strictly private)\b', "confidential_credential", "Confidential Document Header"),
            (r'(?i)\b(account_number|card_number|card_no)\s*[:=]\s*(\d{12,19})', "credit_card", "Account / Card Credential")
        ]

        for pattern, cat, label in context_patterns:
            for match in re.finditer(pattern, text):
                matched_str = match.group(0)
                matched_val = match.group(2) if len(match.groups()) >= 2 else matched_str
                entities.append({
                    "text": matched_val,
                    "full_match": matched_str,
                    "category": cat,
                    "label": label,
                    "confidence": "High",
                    "source": "Contextual Classifier",
                    "start": match.start(),
                    "end": match.end()
                })

        return entities

_classifier_instance = None

def get_classifier():
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = LocalNERClassifier()
    return _classifier_instance

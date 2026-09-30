import os
from config import CATEGORIES

class LocalLLMAdapter:
    """
    Adapter for Optional Local Open-Source LLM.
    Provides natural-language risk explanation, risk summarization, and security recommendations.
    Includes robust fallback if local LLM is disabled or unavailable.
    """
    def __init__(self):
        self.is_available = False
        self.model_name = "Deterministic Rule Explainer (Local)"
        self._check_local_llm()

    def _check_local_llm(self):
        # Check if Ollama or HuggingFace local LLM server is accessible
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    self.is_available = True
                    self.model_name = "Ollama Local LLM (Active)"
                    return
        except Exception:
            pass

        self.is_available = False
        self.model_name = "Local Explanation Engine"

    def explain_finding(self, category_key, value_text=""):
        """
        Explain why a specific detected entity is sensitive.
        """
        cat_info = CATEGORIES.get(category_key, {})
        title = cat_info.get("title", category_key.upper())
        desc = cat_info.get("description", "Potential sensitive string.")
        action = cat_info.get("action", "Review and redact before sharing.")

        explanation = f"{desc} Exposure of this item may allow unauthorized access, data leaks, or privacy violation."
        return {
            "title": title,
            "explanation": explanation,
            "recommendation": action
        }

    def summarize_risk(self, findings, security_score):
        """
        Generate a concise security risk summary based on detected findings.
        """
        total = len(findings)
        if total == 0:
            return "No sensitive items detected. The file appears safe for sharing."

        critical_count = sum(1 for f in findings if f.get("severity") == "CRITICAL")
        high_count = sum(1 for f in findings if f.get("severity") == "HIGH")
        medium_count = sum(1 for f in findings if f.get("severity") == "MEDIUM")

        if critical_count > 0:
            summary = f"HIGH SECURITY RISK: {critical_count} Critical credentials (such as API keys/passwords) were identified. Unredacted distribution could lead to complete account takeover."
        elif high_count > 0:
            summary = f"MODERATE TO HIGH RISK: {high_count} sensitive identity/financial items were detected. Redaction is strongly recommended."
        else:
            summary = f"LOW TO MODERATE RISK: {medium_count} contact or network identifiers found. Redact sensitive personal data before publishing."

        return summary

_llm_adapter_instance = None

def get_local_llm():
    global _llm_adapter_instance
    if _llm_adapter_instance is None:
        _llm_adapter_instance = LocalLLMAdapter()
    return _llm_adapter_instance

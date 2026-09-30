from config import SEVERITY_LEVELS
from models.local_llm import get_local_llm

class RiskEngine:
    """
    Dynamic Security Scoring and Risk Level Calculator.
    Computes Security Score (0-100) based on actual findings.
    """
    def calculate_risk(self, findings):
        """
        Calculate security score and determine overall risk level.
        Returns:
        {
            'security_score': int, # 0 to 100
            'risk_level': 'CRITICAL'|'HIGH'|'MEDIUM'|'SAFE',
            'findings_count': int,
            'counts_by_severity': {'CRITICAL': int, 'HIGH': int, 'MEDIUM': int},
            'summary': str
        }
        """
        if not findings:
            return {
                "security_score": 100,
                "risk_level": "SAFE",
                "findings_count": 0,
                "counts_by_severity": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0},
                "summary": "🛡️ Perfect Security Score (100/100). No sensitive credentials or private items detected."
            }

        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}
        total_penalty = 0

        for item in findings:
            sev = item.get("severity", "MEDIUM")
            if sev not in counts:
                sev = "MEDIUM"
            counts[sev] += 1
            penalty = SEVERITY_LEVELS.get(sev, {}).get("penalty", 5)
            total_penalty += penalty

        # Dynamic score formula
        score = max(0, 100 - total_penalty)

        # Risk level determination
        if counts["CRITICAL"] > 0 or score < 50:
            risk_level = "CRITICAL"
        elif counts["HIGH"] > 0 or score < 75:
            risk_level = "HIGH"
        elif counts["MEDIUM"] > 0 or score < 95:
            risk_level = "MEDIUM"
        else:
            risk_level = "SAFE"

        llm = get_local_llm()
        summary = llm.summarize_risk(findings, score)

        return {
            "security_score": score,
            "risk_level": risk_level,
            "findings_count": len(findings),
            "counts_by_severity": counts,
            "summary": summary
        }

_risk_engine_instance = None

def get_risk_engine():
    global _risk_engine_instance
    if _risk_engine_instance is None:
        _risk_engine_instance = RiskEngine()
    return _risk_engine_instance

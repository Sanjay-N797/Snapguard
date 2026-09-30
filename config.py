import os
import re

APP_NAME = "SnapGuard"
APP_TAGLINE = "Private AI Protection for Your PC"
APP_VERSION = "1.0.0"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DB_PATH = os.path.join(BASE_DIR, "database", "snapguard.db")

for path in [DATA_DIR, OUTPUTS_DIR, ASSETS_DIR, os.path.dirname(DB_PATH)]:
    os.makedirs(path, exist_ok=True)

SEVERITY_LEVELS = {
    "CRITICAL": {
        "label": "CRITICAL",
        "icon": "🔴",
        "color": "#ff4d4f",
        "badge_bg": "rgba(255, 77, 79, 0.15)",
        "penalty": 25,
        "description": "Exposes credentials or financial/auth tokens with extreme risk of compromise."
    },
    "HIGH": {
        "label": "HIGH",
        "icon": "🟠",
        "color": "#ffa940",
        "badge_bg": "rgba(255, 169, 64, 0.15)",
        "penalty": 15,
        "description": "Exposes personal identification or confidential credentials."
    },
    "MEDIUM": {
        "label": "MEDIUM",
        "icon": "🟡",
        "color": "#ffec3d",
        "badge_bg": "rgba(255, 236, 61, 0.15)",
        "penalty": 5,
        "description": "Exposes contact info or internal network details."
    }
}

CATEGORIES = {
    "api_key": {
        "title": "API Key / Access Token",
        "severity": "CRITICAL",
        "description": "Authentication credential for cloud services or APIs.",
        "action": "Revoke and redact immediately before sharing."
    },
    "password": {
        "title": "Password / Secret",
        "severity": "CRITICAL",
        "description": "Plaintext secret or password string.",
        "action": "Redact string and change password."
    },
    "jwt_token": {
        "title": "JWT Auth Token",
        "severity": "CRITICAL",
        "description": "JSON Web Token containing session or authorization state.",
        "action": "Redact token immediately."
    },
    "private_key": {
        "title": "Private Cryptographic Key",
        "severity": "CRITICAL",
        "description": "RSA/SSH/PEM private key header or body.",
        "action": "Redact and verify key security."
    },
    "credit_card": {
        "title": "Credit / Debit Card Number",
        "severity": "HIGH",
        "description": "Payment card primary account number (PAN).",
        "action": "Mask card number before distribution."
    },
    "identity_number": {
        "title": "National ID / SSN",
        "severity": "HIGH",
        "description": "Social Security Number, Passport, or Tax ID.",
        "action": "Redact government identity number."
    },
    "confidential_credential": {
        "title": "Confidential Credential",
        "severity": "HIGH",
        "description": "Internal username, keypair, or connection string.",
        "action": "Redact credential from document."
    },
    "email": {
        "title": "Email Address",
        "severity": "MEDIUM",
        "description": "Personal or business email address.",
        "action": "Mask to prevent spam and phishing targets."
    },
    "phone": {
        "title": "Phone Number",
        "severity": "MEDIUM",
        "description": "Direct contact phone number.",
        "action": "Mask phone number."
    },
    "ip_address": {
        "title": "IP Address",
        "severity": "MEDIUM",
        "description": "Internal or external IPv4 address.",
        "action": "Redact network address."
    },
    "url_credentials": {
        "title": "URL with Embedded Credentials",
        "severity": "CRITICAL",
        "description": "Web URL containing username and password parameters.",
        "action": "Strip credentials from URL."
    }
}

REGEX_PATTERNS = [
    {
        "category": "email",
        "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        "confidence": "High",
        "label": "Email Address"
    },
    {
        "category": "phone",
        "pattern": r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        "confidence": "High",
        "label": "Phone Number"
    },
    {
        "category": "credit_card",
        "pattern": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b',
        "confidence": "High",
        "label": "Credit/Debit Card"
    },
    {
        "category": "api_key",
        "pattern": r'\b(?:sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|sq0atp-[0-9A-Za-z\-_]{22}|key-[0-9a-zA-Z]{32}|AIzaSy[0-9A-Za-z\-_]{35})\b',
        "confidence": "High",
        "label": "API Key (Provider Specific)"
    },
    {
        "category": "api_key",
        "pattern": r'(?i)\b(?:api[_\-]?key|secret[_\-]?key|access[_\-]?token|auth[_\-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{16,})["\']?',
        "confidence": "High",
        "label": "API / Auth Key Assignment"
    },
    {
        "category": "password",
        "pattern": r'(?i)\b(?:password|passwd|pwd|db_pass)\s*[:=]\s*["\']?([^\s"\']{6,})["\']?',
        "confidence": "High",
        "label": "Password String"
    },
    {
        "category": "jwt_token",
        "pattern": r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b',
        "confidence": "High",
        "label": "JWT Auth Token"
    },
    {
        "category": "private_key",
        "pattern": r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
        "confidence": "High",
        "label": "Private Key Block"
    },
    {
        "category": "ip_address",
        "pattern": r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        "confidence": "Medium",
        "label": "IPv4 Address"
    },
    {
        "category": "url_credentials",
        "pattern": r'https?://[A-Za-z0-9_]+:[^@\s]+@[A-Za-z0-9.-]+',
        "confidence": "High",
        "label": "URL Credentials"
    },
    {
        "category": "identity_number",
        "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
        "confidence": "High",
        "label": "Social Security Number (SSN)"
    }
]

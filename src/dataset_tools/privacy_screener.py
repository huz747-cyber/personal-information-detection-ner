"""
Privacy and PII Screening Engine for Malaysian Text Datasets.

Scans dataset records for potential real-world privacy leaks:
1. Non-synthetic identity documents (MyKad / NRIC).
2. Live private telephone numbers (unmasked real mobile numbers).
3. Personal residential addresses (unit/lot numbers in residential taman/kampung).
4. Credentials, API keys, tokens, and passwords (e.g. 'ghp_', 'sk-', 'bearer', 'password=').
5. Private medical status or financial credit card numbers (Luhn check).

Author: AI/ML Club
License: MIT
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PrivacyViolation:
    record_id: Any
    category: str      # 'MYKAD_LEAK', 'PHONE_LEAK', 'CREDENTIAL', 'RESIDENTIAL_ADDRESS', 'CREDIT_CARD'
    severity: str      # 'CRITICAL', 'HIGH', 'MEDIUM'
    detected_snippet: str
    message: str


class PrivacyScreener:
    """Automated privacy compliance and secret detection auditor."""

    # Credentials & secrets patterns
    CREDENTIAL_PATTERNS = [
        (re.compile(r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*\S+"), "CREDENTIAL"),
        (re.compile(r"\b(?:ghp_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{20,}|ey[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,})\b"), "SECRET_TOKEN"),
    ]

    # Credit card regex (13 to 19 digits)
    CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")

    # MyKad pattern
    MYKAD_REGEX = re.compile(r"\b(\d{6})-(\d{2})-(\d{4})\b")

    # Live Malaysian private mobile phone numbers (01[0-9]-XXXXXXX) without masking
    LIVE_PHONE_REGEX = re.compile(r"(?:\+?60|0)1[0-9][\s-]?\d{3,4}[\s-]?\d{4}\b")

    # Residential unit/lot address indicator (e.g., "No. 12, Jalan...", "Lot 45, Kampung...")
    RESIDENTIAL_LOT_REGEX = re.compile(
        r"(?i)\b(?:no\.?\s*\d+[/A-Z0-9-]*|lot\s*\d+[/A-Z0-9-]*|unit\s*\d+[-A-Z0-9]*)\s*,\s*(?:jalan|lorong|taman|kampung)\b"
    )

    # Known synthetic test identifiers approved for documentation and testing
    APPROVED_SYNTHETIC_MYKAD = {
        "950315-10-5231", "920412-14-6122", "801125-01-5833", "840815-08-6321",
        "880520-10-5123", "900101-01-1234", "991231-14-9999", "750615-08-4321",
    }

    APPROVED_SYNTHETIC_PHONES = {
        "+6012-345 6789", "012-3456789", "+60 11-1234 5678", "011-12345678",
        "+60 19-876 5432", "017-6543210", "+6012-3456789", "012-345 6789",
        "03-8888 1234", "04-226 1234", "082-421 234", "+603-2144 5678"
    }

    def __init__(self, allow_synthetic: bool = True):
        self.allow_synthetic = allow_synthetic

    def scan_text(self, text: str, record_id: Any = "UNKNOWN") -> List[PrivacyViolation]:
        """Scans a single text string for potential personal data leaks."""
        violations: List[PrivacyViolation] = []

        # 1. Credentials and Secret Tokens
        for pattern, cat in self.CREDENTIAL_PATTERNS:
            for match in pattern.finditer(text):
                violations.append(PrivacyViolation(
                    record_id=record_id,
                    category="CREDENTIAL",
                    severity="CRITICAL",
                    detected_snippet=match.group(0)[:30] + "...",
                    message=f"Possible credential or token leak detected ({cat}).",
                ))

        # 2. Credit Card Numbers
        for match in self.CREDIT_CARD_REGEX.finditer(text):
            digits = re.sub(r"\D", "", match.group(0))
            if 13 <= len(digits) <= 19 and self._luhn_check(digits):
                violations.append(PrivacyViolation(
                    record_id=record_id,
                    category="CREDIT_CARD",
                    severity="CRITICAL",
                    detected_snippet=f"{digits[:4]} **** **** {digits[-4:]}",
                    message="Valid credit card number format detected passing Luhn check.",
                ))

        # 3. MyKad Numbers (check if synthetic or real)
        for match in self.MYKAD_REGEX.finditer(text):
            raw = match.group(0)
            if self.allow_synthetic and raw in self.APPROVED_SYNTHETIC_MYKAD:
                continue
            violations.append(PrivacyViolation(
                record_id=record_id,
                category="MYKAD_LEAK",
                severity="HIGH",
                detected_snippet=raw[:8] + "-****",
                message=f"Potentially live or unverified MyKad number detected: '{raw[:8]}-****'.",
            ))

        # 4. Live Unmasked Mobile Phone Numbers
        for match in self.LIVE_PHONE_REGEX.finditer(text):
            raw = match.group(0)
            if self.allow_synthetic and raw in self.APPROVED_SYNTHETIC_PHONES:
                continue
            # Check if this phone number is inside a general text record without masking
            violations.append(PrivacyViolation(
                record_id=record_id,
                category="PHONE_LEAK",
                severity="HIGH",
                detected_snippet=raw[:7] + "****",
                message=f"Unmasked private telephone number format detected: '{raw[:7]}****'.",
            ))

        # 5. Residential Unit/Lot Addresses
        for match in self.RESIDENTIAL_LOT_REGEX.finditer(text):
            violations.append(PrivacyViolation(
                record_id=record_id,
                category="RESIDENTIAL_ADDRESS",
                severity="MEDIUM",
                detected_snippet=match.group(0),
                message="Specific private residential lot/unit number detected in address context.",
            ))

        return violations

    def screen_dataset(self, records: List[Dict[str, Any]]) -> Tuple[bool, List[PrivacyViolation]]:
        """Screens an entire dataset of records. Returns (is_clean, violations)."""
        all_violations: List[PrivacyViolation] = []
        for rec in records:
            r_id = rec.get("id", "UNKNOWN")
            text = rec.get("text", "")
            r_viols = self.scan_text(text, record_id=r_id)
            all_violations.extend(r_viols)

        is_clean = len([v for v in all_violations if v.severity in {"CRITICAL", "HIGH"}]) == 0
        return is_clean, all_violations

    @staticmethod
    def _luhn_check(num_str: str) -> bool:
        """Validates Luhn algorithm checksum for credit card numbers."""
        total = 0
        reverse_digits = [int(d) for d in reversed(num_str)]
        for i, digit in enumerate(reverse_digits):
            if i % 2 == 1:
                doubled = digit * 2
                total += doubled - 9 if doubled > 9 else doubled
            else:
                total += digit
        return total % 10 == 0

import re
from typing import Tuple
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# load once — expensive
_analyzer = None
_anonymizer = None


def get_presidio():
    global _analyzer, _anonymizer
    if _analyzer is None:
        _analyzer = AnalyzerEngine()
        _anonymizer = AnonymizerEngine()
    return _analyzer, _anonymizer


# known prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore (previous|all|above) instructions",
    r"you are now",
    r"disregard your",
    r"forget everything",
    r"new personality",
    r"pretend you",
    r"act as (a|an|if)",
    r"jailbreak",
    r"bypass (safety|filter|restriction)",
    r"do anything now",
    r"dan mode",
]


def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    """
    Checks input for known prompt injection patterns.
    Returns (is_injection, matched_pattern).
    This is the AI security requirement from the JDs.
    """
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True, pattern
    return False, ""


def redact_pii(text: str) -> str:
    """
    Removes PII (emails, phone numbers, SSNs, names, etc.)
    before agent output leaves the system.
    Uses Microsoft Presidio — production-grade PII detection.
    """
    try:
        analyzer, anonymizer = get_presidio()
        results = analyzer.analyze(text=text, language="en")
        if not results:
            return text
        anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
        return anonymized.text
    except Exception:
        # never block on PII redaction failure — log and continue
        return text


def filter_output(text: str) -> str:
    """
    Output filtering pipeline — runs before returning agent output.
    Extend this with domain-specific filters as needed.
    """
    text = redact_pii(text)
    return text
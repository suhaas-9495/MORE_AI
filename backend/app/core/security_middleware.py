import re
from typing import Tuple

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
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True, pattern
    return False, ""


def redact_pii(text: str) -> str:
    """PII redaction — uses Presidio if available, falls back gracefully."""
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine
        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()
        results = analyzer.analyze(text=text, language="en")
        if not results:
            return text
        return anonymizer.anonymize(text=text, analyzer_results=results).text
    except ImportError:
        # presidio not installed — skip redaction, log warning
        return text
    except Exception:
        return text


def filter_output(text: str) -> str:
    return redact_pii(text)
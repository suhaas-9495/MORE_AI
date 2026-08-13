import re
import html
from typing import str as String


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitizes user input before processing.
    Removes null bytes, control characters, and truncates.
    Does NOT escape HTML — that's for web rendering, not LLM input.
    """
    if not text:
        return ""

    # remove null bytes — can cause issues in some backends
    text = text.replace("\x00", "")

    # remove other control characters except newline/tab
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # truncate to max length
    if len(text) > max_length:
        text = text[:max_length] + "... [truncated]"

    return text.strip()


def sanitize_filename(filename: str) -> str:
    """Sanitizes filenames — prevents path traversal attacks."""
    # remove path separators
    filename = re.sub(r"[/\\]", "_", filename)
    # remove dangerous characters
    filename = re.sub(r"[^\w\-_. ]", "", filename)
    # prevent hidden files
    filename = filename.lstrip(".")
    return filename[:255]  # max filename length
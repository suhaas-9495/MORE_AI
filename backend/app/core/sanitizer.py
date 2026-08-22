import re


def sanitize_input(text: str, max_length: int = 10000) -> str:
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    if len(text) > max_length:
        text = text[:max_length] + "... [truncated]"
    return text.strip()


def sanitize_filename(filename: str) -> str:
    filename = re.sub(r"[/\\]", "_", filename)
    filename = re.sub(r"[^\w\-_. ]", "", filename)
    filename = filename.lstrip(".")
    return filename[:255]
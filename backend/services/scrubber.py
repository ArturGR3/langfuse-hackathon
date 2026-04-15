import re


def scrub_pii(text: str, pii_list: list[str]) -> str:
    result = text
    for pii in pii_list:
        escaped = re.escape(pii)
        result = re.sub(escaped, "[REDACTED]", result, flags=re.IGNORECASE)
    return result

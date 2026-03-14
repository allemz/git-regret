from __future__ import annotations

import math
from collections import Counter

_BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
_HEX_CHARS    = "0123456789abcdefABCDEF"

# Entropy thresholds
HIGH_ENTROPY_BASE64 = 4.5
HIGH_ENTROPY_HEX    = 3.0


def shannon_entropy(text: str) -> float:
    """Calculate the Shannon entropy of a string."""
    if not text:
        return 0.0
    counts = Counter(text)
    length = len(text)
    return -sum(
        (count / length) * math.log2(count / length)
        for count in counts.values()
    )


def is_high_entropy(text: str, threshold: float = HIGH_ENTROPY_BASE64) -> bool:
    return shannon_entropy(text) >= threshold


def _is_charset(text: str, charset: str) -> bool:
    return all(c in charset for c in text)


def find_high_entropy_strings(line: str, min_length: int = 20) -> list[str]:
    """
    Find high-entropy strings in a line of text.
    Checks against base64 and hex character sets.
    """
    found: list[str] = []
    for word in line.split():
        clean = word.strip("\"'`,;")
        if len(clean) < min_length:
            continue
        if _is_charset(clean, _BASE64_CHARS) and is_high_entropy(clean, HIGH_ENTROPY_BASE64):
            found.append(clean)
        elif _is_charset(clean, _HEX_CHARS) and is_high_entropy(clean, HIGH_ENTROPY_HEX):
            found.append(clean)
    return found

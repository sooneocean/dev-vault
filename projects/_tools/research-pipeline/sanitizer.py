"""Content sanitizer — defense against prompt injection from untrusted README/docs content."""

from __future__ import annotations

import base64
import re


# Patterns that indicate LLM instruction injection attempts
_INJECTION_PATTERNS = [
    # Direct instruction patterns
    r"(?i)ignore\s+(all\s+)?previous\s+instructions",
    r"(?i)you\s+are\s+now\s+a",
    r"(?i)system\s*:\s*you\s+are",
    r"(?i)new\s+instructions?\s*:",
    r"(?i)important\s*:\s*score\s+this",
    r"(?i)recommended?\s+action\s*:\s*add",
    r"(?i)this\s+tool\s+scores?\s+\d+/\d+",
    # Hidden instruction markers
    r"(?i)<\s*system\s*>",
    r"(?i)<\s*/?\s*instructions?\s*>",
    r"(?i)\[INST\]",
    r"(?i)<<\s*SYS\s*>>",
]


def sanitize(text: str) -> str:
    """Remove potentially malicious content from README/docs text.

    Strips HTML comments, hidden Unicode characters, base64 blocks,
    and suspicious LLM instruction patterns. Returns clean plain text.
    """
    if not text:
        return ""

    result = text

    # 1. Remove HTML comments (may hide injection payloads)
    result = re.sub(r"<!--[\s\S]*?-->", "", result)

    # 2. Remove HTML tags (keep text content)
    result = re.sub(r"<[^>]+>", "", result)

    # 3. Remove base64 encoded blocks (potential hidden payloads)
    result = re.sub(
        r"(?:data:[a-zA-Z/]+;base64,)?[A-Za-z0-9+/]{100,}={0,2}",
        "[base64-removed]",
        result,
    )

    # 4. Remove zero-width and invisible Unicode characters
    invisible_chars = (
        "\u200b"  # zero-width space
        "\u200c"  # zero-width non-joiner
        "\u200d"  # zero-width joiner
        "\u2060"  # word joiner
        "\ufeff"  # BOM / zero-width no-break space
        "\u00ad"  # soft hyphen
        "\u200e"  # left-to-right mark
        "\u200f"  # right-to-left mark
        "\u202a"  # left-to-right embedding
        "\u202b"  # right-to-left embedding
        "\u202c"  # pop directional formatting
        "\u202d"  # left-to-right override
        "\u202e"  # right-to-left override
    )
    for char in invisible_chars:
        result = result.replace(char, "")

    # 5. Flag (but don't remove) injection patterns — replace with warning marker
    for pattern in _INJECTION_PATTERNS:
        result = re.sub(pattern, "[injection-pattern-removed]", result)

    # 6. Truncate extremely long content (likely noise or attack payload)
    max_chars = 10_000
    if len(result) > max_chars:
        result = result[:max_chars] + "\n\n[truncated — content exceeded 10,000 characters]"

    # 7. Normalize whitespace
    result = re.sub(r"\n{4,}", "\n\n\n", result)
    result = result.strip()

    return result


def sanitize_metadata(metadata: dict) -> dict:
    """Sanitize all string values in a metadata dict."""
    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, str):
            # Lighter sanitization for short metadata fields
            cleaned = re.sub(r"<!--[\s\S]*?-->", "", value)
            for char in "\u200b\u200c\u200d\u2060\ufeff":
                cleaned = cleaned.replace(char, "")
            # Length-limit metadata strings
            sanitized[key] = cleaned[:500]
        elif isinstance(value, list):
            sanitized[key] = [
                s[:100] if isinstance(s, str) else s for s in value[:20]
            ]
        else:
            sanitized[key] = value
    return sanitized

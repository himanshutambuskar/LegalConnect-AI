"""
LegalConnect — Citation & Statutory Utilities (Lightweight)
------------------------------------------------------------
Standard-library only utility functions for statutory citation extraction,
hallucination filtering, and streaming token qualification.

Zero heavy dependencies: does NOT import ChromaDB, SentenceTransformers, or PyTorch.
Can be safely imported by Streamlit frontend, FastAPI backend, and CLI utilities.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


def extract_allowed_section_numbers(metadatas_or_sources: list[dict[str, Any]]) -> set[str]:
    """Extract clean section numbers from retrieved metadata or source dictionaries.

    Supports numeric and alphanumeric sections (e.g., '185', '66D', '43A', '13B').
    Returns a set of lowercase normalized section identifiers.
    """
    allowed: set[str] = set()
    for s in metadatas_or_sources:
        sec_num = str(s.get("section_number") or "").strip()
        if sec_num:
            base = re.match(r"(\d+[A-Za-z]*)", sec_num)
            if base:
                allowed.add(base.group(1).lower())
        sec = str(s.get("section") or "").strip()
        if sec:
            m = re.search(r"\b(\d+[A-Za-z]*)\b", sec)
            if m:
                allowed.add(m.group(1).lower())
    return allowed


def sanitize_unsupported_citations(text: str, allowed_sections: set[str]) -> str:
    """Lightweight post-generation safety check:

    Detects any section references mentioned by the model that were NOT in the retrieved sources,
    and cleanly rephrases them to avoid presenting hallucinated section numbers to the user.
    """
    if not text:
        return text

    norm_allowed = {re.sub(r"[^0-9a-z]", "", s.lower()) for s in allowed_sections if s}

    def replacer(match: re.Match[str]) -> str:
        full_match = match.group(0)
        raw_sec = match.group(1)
        base_sec = re.match(r"(\d+[A-Za-z]*)", raw_sec)
        if base_sec:
            sec_clean = re.sub(r"[^0-9a-z]", "", base_sec.group(1).lower())
            if sec_clean not in norm_allowed:
                return "applicable statutory provisions"
        return full_match

    # Pattern matching Section 85, Sec. 85, Section 85(1)(a), Section 66D, etc.
    pattern = r"\b(?:Section|Sec\.?|s\.?)\s*(\d+[A-Za-z]*(?:\s*\([0-9a-zA-Z]+\))*)"
    sanitized = re.sub(pattern, replacer, text, flags=re.IGNORECASE)

    # Polish phrasing
    sanitized = re.sub(r"\bunder\s+the\s+applicable\s+statutory\s+provisions?\b", "under statutory provisions", sanitized, flags=re.I)
    sanitized = re.sub(r"\bunder\s+applicable\s+statutory\s+provisions?\b", "under statutory provisions", sanitized, flags=re.I)
    sanitized = re.sub(r"\bas\s+per\s+the\s+applicable\s+statutory\s+provisions?\b", "as per statutory provisions", sanitized, flags=re.I)
    sanitized = re.sub(r"\bas\s+per\s+applicable\s+statutory\s+provisions?\b", "as per statutory provisions", sanitized, flags=re.I)
    return sanitized


def create_citation_stream_filter(
    allowed_sections: Optional[set[str]] = None,
) -> Tuple[Callable[[str], str], Callable[[], str]]:
    """Creates a token-by-token streaming filter that checks citations on the fly.

    Buffers potential section tokens across chunk boundaries and sanitizes unsupported
    statutory sections into 'statutory provisions'.
    """
    if not allowed_sections:
        return lambda tok: tok, lambda: ""

    norm_allowed = {re.sub(r"[^0-9a-z]", "", s.lower()) for s in allowed_sections if s}
    sec_prefix_re = re.compile(r"\b(?:Section|Sec\.?|s\.?)\b", re.IGNORECASE)
    sec_full_re = re.compile(r"\b(?:Section|Sec\.?|s\.?)\s*(\d+[A-Za-z]*(?:\s*\([0-9a-zA-Z]+\))*)\b", re.IGNORECASE)

    buffer = ""

    def process_token(token: str) -> str:
        nonlocal buffer
        buffer += token

        if not sec_prefix_re.search(buffer):
            out = buffer
            buffer = ""
            return out

        m = sec_full_re.search(buffer)
        if m:
            sec_end = m.end()
            if len(buffer) > sec_end:
                raw_sec = m.group(1)
                base_sec = re.match(r"(\d+[A-Za-z]*)", raw_sec)
                sec_clean = re.sub(r"[^0-9a-z]", "", base_sec.group(1).lower()) if base_sec else ""
                if sec_clean not in norm_allowed:
                    sanitized = buffer[:m.start()] + "statutory provisions" + buffer[sec_end:]
                else:
                    sanitized = buffer
                buffer = ""
                return sanitized

        if len(buffer) > 80:
            out = buffer
            buffer = ""
            return out

        return ""

    def flush() -> str:
        nonlocal buffer
        if not buffer:
            return ""

        def replacer(match: re.Match[str]) -> str:
            raw_sec = match.group(1)
            base_sec = re.match(r"(\d+[A-Za-z]*)", raw_sec)
            sec_clean = re.sub(r"[^0-9a-z]", "", base_sec.group(1).lower()) if base_sec else ""
            if sec_clean not in norm_allowed:
                return "statutory provisions"
            return match.group(0)

        out = sec_full_re.sub(replacer, buffer)
        buffer = ""
        return out

    return process_token, flush

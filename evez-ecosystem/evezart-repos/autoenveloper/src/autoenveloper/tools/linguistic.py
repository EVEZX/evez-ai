"""
Linguistic Pattern Analysis Tool — Autoenveloper Module
Semantic patterns, n-gram analysis, style fingerprinting, anonymization.
"""

import re
import math
import hashlib
from collections import Counter


# ── LINGUISTIC PATTERNS ───────────────────────────────────────────────────────

def ngram_profile(text: str, n: int = 2, top_k: int = 20) -> dict:
    """Extract n-gram frequency profile from text."""
    words = re.findall(r'\b\w+\b', text.lower())
    if len(words) < n:
        return {"error": "text too short"}
    
    grams = [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]
    freq  = Counter(grams)
    total = len(grams)
    
    return {
        "n":          n,
        "total":      total,
        "vocabulary": len(freq),
        "top":        [{"gram": g, "count": c, "freq": round(c/total, 4)}
                       for g, c in freq.most_common(top_k)]
    }


def style_fingerprint(text: str) -> dict:
    """
    Authorship-style fingerprint — useful for:
    - Identifying writing patterns
    - Detecting AI-generated content signatures
    - Cross-document attribution
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words     = re.findall(r'\b\w+\b', text)
    
    if not words or not sentences:
        return {"error": "insufficient text"}
    
    word_lengths  = [len(w) for w in words]
    sent_lengths  = [len(s.split()) for s in sentences]
    
    # Punctuation density
    punct_count = sum(1 for c in text if c in '.,;:!?-—()')
    punct_density = punct_count / len(text) if text else 0
    
    # Lexical richness
    type_token_ratio = len(set(words)) / len(words)
    
    # Function word ratio (proxy for style)
    function_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at",
                      "to", "for", "of", "with", "by", "from", "is", "was",
                      "are", "were", "be", "been", "have", "has", "had"}
    fw_count = sum(1 for w in words if w.lower() in function_words)
    fw_ratio = fw_count / len(words)
    
    return {
        "avg_word_length":     round(sum(word_lengths) / len(word_lengths), 2),
        "avg_sentence_length": round(sum(sent_lengths) / len(sent_lengths), 2),
        "type_token_ratio":    round(type_token_ratio, 4),
        "function_word_ratio": round(fw_ratio, 4),
        "punct_density":       round(punct_density, 4),
        "sentence_count":      len(sentences),
        "word_count":          len(words),
        "fingerprint_hash":    hashlib.md5(
            f"{round(type_token_ratio,2)}{round(fw_ratio,2)}{round(punct_density,3)}".encode()
        ).hexdigest()[:8]
    }


def detect_patterns(text: str) -> dict:
    """Detect recurring structural patterns: lists, code, questions, imperatives."""
    patterns = {
        "questions":        len(re.findall(r'\?', text)),
        "imperatives":      len(re.findall(r'^(Do|Build|Create|Write|Make|Run|Install|Deploy)\b',
                                            text, re.MULTILINE | re.IGNORECASE)),
        "code_blocks":      len(re.findall(r'```[\s\S]*?```', text)),
        "numbered_lists":   len(re.findall(r'^\d+\.',  text, re.MULTILINE)),
        "bullet_lists":     len(re.findall(r'^[-*•]',  text, re.MULTILINE)),
        "urls":             len(re.findall(r'https?://\S+', text)),
        "emails":           len(re.findall(r'\b[\w._%+-]+@[\w.-]+\.[a-z]{2,}\b', text)),
        "hex_patterns":     len(re.findall(r'\b[0-9a-fA-F]{8,}\b', text)),
        "ip_addresses":     len(re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text)),
    }
    dominant = max(patterns, key=patterns.get)
    return {"patterns": patterns, "dominant": dominant, "total_signals": sum(patterns.values())}


# ── ANONYMIZATION ─────────────────────────────────────────────────────────────

def anonymize_text(text: str, strategy: str = "redact") -> dict:
    """
    Anonymize PII in text.
    Strategies: redact (replace with [TYPE]), pseudonymize (replace with consistent alias),
                generalize (replace with category label)
    """
    import copy
    
    patterns = {
        "email":   (r'\b[\w._%+-]+@[\w.-]+\.[a-z]{2,}\b',    "[EMAIL]"),
        "phone":   (r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', "[PHONE]"),
        "ssn":     (r'\b\d{3}-\d{2}-\d{4}\b',                 "[SSN]"),
        "ip":      (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', "[IP_ADDRESS]"),
        "url":     (r'https?://[^\s]+',                        "[URL]"),
        "credit":  (r'\b(?:\d[ -]?){13,16}\b',                "[CARD_NUMBER]"),
        "date":    (r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',    "[DATE]"),
        "hash":    (r'\b[0-9a-fA-F]{32,64}\b',                "[HASH]"),
    }
    
    result     = text
    replacements = {}
    counter    = {}
    
    for name, (pattern, label) in patterns.items():
        matches = re.findall(pattern, result, re.IGNORECASE)
        if not matches:
            continue
        
        if strategy == "pseudonymize":
            for match in set(matches):
                if match not in replacements:
                    n = counter.get(name, 0) + 1
                    counter[name] = n
                    replacements[match] = f"{label[1:-1]}_{n:03d}"
                result = result.replace(match, f"[{replacements[match]}]")
        else:
            result = re.sub(pattern, label, result, flags=re.IGNORECASE)
        
        replacements[name] = {"count": len(matches), "label": label}
    
    return {
        "original_length":   len(text),
        "anonymized_length": len(result),
        "anonymized_text":   result,
        "strategy":          strategy,
        "replacements":      replacements
    }


def get_tools():
    from tools.registry import Tool

    return [
        Tool(
            name="linguistic_ngram_profile",
            description="Extract n-gram frequency profile from text for pattern analysis.",
            parameters={
                "type": "object",
                "properties": {
                    "text":  {"type": "string"},
                    "n":     {"type": "integer", "default": 2, "description": "N-gram size"},
                    "top_k": {"type": "integer", "default": 20}
                },
                "required": ["text"]
            },
            fn=lambda text, n=2, top_k=20: ngram_profile(text, n, top_k)
        ),
        Tool(
            name="linguistic_style_fingerprint",
            description="Generate authorship fingerprint from text — style, lexical richness, structure.",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"]
            },
            fn=lambda text: style_fingerprint(text)
        ),
        Tool(
            name="linguistic_detect_patterns",
            description="Detect structural patterns in text: lists, code blocks, questions, URLs, IPs, etc.",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"]
            },
            fn=lambda text: detect_patterns(text)
        ),
        Tool(
            name="anonymize_text",
            description="Remove or pseudonymize PII from text. Strategies: redact, pseudonymize, generalize.",
            parameters={
                "type": "object",
                "properties": {
                    "text":     {"type": "string"},
                    "strategy": {"type": "string", "enum": ["redact", "pseudonymize", "generalize"],
                                 "default": "redact"}
                },
                "required": ["text"]
            },
            fn=lambda text, strategy="redact": anonymize_text(text, strategy)
        )
    ]

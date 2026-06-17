"""
Gap report generator for disclosure.tools
Produces structured, human-readable, and shareable reports from spectral analysis.
"""
import json
import hashlib
import time
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class GapSeverity(Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class GapCategory(Enum):
    REDACTION = "redaction"
    MISSING_RECORD = "missing_record"
    BROKEN_CHAIN = "broken_chain"
    TEMPORAL_GAP = "temporal_gap"
    CROSS_REF_FAILURE = "cross_ref_failure"
    CLASSIFICATION_SHADOW = "classification_shadow"


@dataclass
class GapFinding:
    """A single gap finding from spectral analysis."""
    category: GapCategory
    severity: GapSeverity
    location: str
    description: str
    eigenvalue: float
    confidence: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    meme_caption: str = ""

    def to_dict(self) -> Dict:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "location": self.location,
            "description": self.description,
            "eigenvalue": round(self.eigenvalue, 4),
            "confidence": round(self.confidence, 4),
            "evidence": self.evidence,
            "meme_caption": self.meme_caption,
        }


@dataclass
class GapReport:
    """Complete gap analysis report."""
    report_id: str
    timestamp: int
    operator: str
    n_documents: int
    n_sections: int
    phi: float
    eta_star: float
    eigenvalues: List[float]
    negative_eigenvalues: int
    dominant_negative: float
    dominant_ratio_37pct: float
    findings: List[GapFinding] = field(default_factory=list)
    merkle_hash: str = ""
    summary: str = ""
    meme_triggers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "operator": self.operator,
            "n_documents": self.n_documents,
            "n_sections": self.n_sections,
            "phi": round(self.phi, 4),
            "eta_star": round(self.eta_star, 4),
            "eigenvalues": [round(float(v), 4) for v in self.eigenvalues],
            "negative_eigenvalues": self.negative_eigenvalues,
            "dominant_negative": round(self.dominant_negative, 4),
            "dominant_ratio_37pct": round(self.dominant_ratio_37pct, 4),
            "findings": [f.to_dict() for f in self.findings],
            "merkle_hash": self.merkle_hash,
            "summary": self.summary,
            "meme_triggers": self.meme_triggers,
        }

    def to_text(self) -> str:
        """Human-readable text report."""
        severity_emoji = {
            GapSeverity.NONE: "✅", GapSeverity.LOW: "🟡",
            GapSeverity.MODERATE: "🟠", GapSeverity.HIGH: "🔴", GapSeverity.CRITICAL: "💀",
        }
        lines = [
            "🔍 EIGENFORENSICS GAP REPORT",
            "=" * 50,
            f"Report: {self.report_id}",
            f"Timestamp: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(self.timestamp))}",
            f"Operator: {self.operator}",
            "",
            "📊 SPECTRAL SUMMARY",
            "-" * 30,
            f"Documents analyzed: {self.n_documents}",
            f"Sections analyzed: {self.n_sections}",
            f"Φ (fidelity):        {self.phi:.4f}",
            f"η* (incompleteness): {self.eta_star:.4f}",
            f"Negative eigenvalues: {self.negative_eigenvalues}/{len(self.eigenvalues)}",
            f"Dominant negative:   {self.dominant_negative:.4f}",
            f"37% Theorem ratio:   {self.dominant_ratio_37pct:.4f}",
            "",
            "🔎 GAP FINDINGS",
            "-" * 30,
        ]

        if not self.findings:
            lines.append("No significant gaps detected.")
        else:
            for finding in self.findings:
                emoji = severity_emoji.get(finding.severity, "❓")
                lines.append(f"{emoji} [{finding.severity.value.upper()}] {finding.category.value}")
                lines.append(f"   Location: {finding.location}")
                lines.append(f"   {finding.description}")
                lines.append(f"   Eigenvalue: {finding.eigenvalue:.4f} | Confidence: {finding.confidence:.2%}")
                if finding.evidence:
                    for ev in finding.evidence[:3]:
                        lines.append(f"   → {ev}")
                lines.append("")

        if self.meme_triggers:
            lines.append("🎭 MEME TRIGGERS")
            lines.append("-" * 30)
            for caption in self.meme_triggers:
                lines.append(f'  "{caption}"')
            lines.append("")

        lines.extend([
            f"Merkle: {self.merkle_hash}",
            "",
            f"{'⚠️  GAPS DETECTED' if self.findings else '✅ CORPUS COHERENT'}",
        ])

        return "\n".join(lines)


def _classify_severity(gap_score: float) -> GapSeverity:
    """Classify gap severity from 0-1 score."""
    if gap_score < 0.05:
        return GapSeverity.NONE
    elif gap_score < 0.15:
        return GapSeverity.LOW
    elif gap_score < 0.30:
        return GapSeverity.MODERATE
    elif gap_score < 0.50:
        return GapSeverity.HIGH
    else:
        return GapSeverity.CRITICAL


def _infer_category(eigenvalue: float, context: str = "") -> GapCategory:
    """Infer gap category from eigenvalue magnitude and context."""
    text_lower = context.lower()
    if any(w in text_lower for w in ["redact", "[REDACTED]", "██", "***"]):
        return GapCategory.REDACTION
    elif any(w in text_lower for w in ["classified", "secret", "top secret", "ts//"]):
        return GapCategory.CLASSIFICATION_SHADOW
    elif any(w in text_lower for w in ["see also", "refer to", "appendix", "reference"]):
        return GapCategory.CROSS_REF_FAILURE
    elif eigenvalue < -0.2:
        return GapCategory.MISSING_RECORD
    else:
        return GapCategory.BROKEN_CHAIN


def generate_meme_caption(category: GapCategory, severity: GapSeverity, location: str) -> str:
    """Auto-generate a shareable meme caption for a gap finding."""
    templates = {
        GapCategory.REDACTION: [
            "When the [REDACTED] hits the [REDACTED]",
            "AARO: 'Full transparency' *redacts 40%*",
            "This page intentionally left suspicious",
            "Redacted so hard the eigenvalues went negative",
        ],
        GapCategory.MISSING_RECORD: [
            f"Records for '{location}'? Must be in the same filing cabinet as the Ark",
            "The dog ate my FOIA records",
            "Missing records? In MY disclosure? It's more likely than you think",
            "Gap so big you could drive a UAP through it",
        ],
        GapCategory.CLASSIFICATION_SHADOW: [
            "Classified: the spectral decomposition knows what you're hiding",
            "TS//NOFORN → but the eigenvalues don't lie",
            "You can redact the text, you can't redact the math",
            "Classification level: eigenvalue goes brrr",
        ],
        GapCategory.BROKEN_CHAIN: [
            "Reference chain more broken than AARO's credibility",
            "This reference leads to a 404 in real life",
            "Cross-reference? More like cross-fiction",
        ],
        GapCategory.TEMPORAL_GAP: [
            "Time gap so big it has its own zip code",
            "Nothing happened between 2017-2021. Trust us. — The Pentagon",
        ],
        GapCategory.CROSS_REF_FAILURE: [
            "See also: [DOES NOT EXIST]",
            "Reference says 'Appendix B' — Appendix B says 'See Appendix A'",
        ],
    }

    import random
    candidates = templates.get(category, ["The eigenvalues have spoken"])
    return random.choice(candidates)


def generate_report(
    eigenvalues: np.ndarray,
    n_documents: int,
    n_sections: int,
    operator: str = "evez666",
    section_titles: Optional[List[str]] = None,
    context_text: str = "",
) -> GapReport:
    """Generate a full gap report from spectral analysis results."""
    neg_eigs = [(i, v) for i, v in enumerate(eigenvalues) if v < -0.01]

    # Compute Φ and η*
    pos_eigs = [v for v in eigenvalues if v > 0]
    total_pos = sum(pos_eigs) if pos_eigs else 1
    total_abs = sum(abs(v) for v in eigenvalues) or 1
    phi = float(total_pos / total_abs) if total_abs > 0 else 0
    eta_star = 1.0 - phi

    # Dominant negative eigenvalue
    if neg_eigs:
        dominant_neg = min(v for _, v in neg_eigs)
        total_tension = sum(abs(v) for _, v in neg_eigs)
        dominant_ratio = abs(dominant_neg) / total_tension if total_tension > 0 else 0
    else:
        dominant_neg = 0
        dominant_ratio = 0

    # Generate findings
    findings = []
    meme_triggers = []

    for idx, eig_val in neg_eigs:
        location = (section_titles[idx] if section_titles and idx < len(section_titles)
                    else f"Section {idx}")
        category = _infer_category(eig_val, context_text)
        severity = _classify_severity(abs(eig_val))

        caption = generate_meme_caption(category, severity, location)

        finding = GapFinding(
            category=category,
            severity=severity,
            location=location,
            description=f"Structural gap detected at {location} (λ = {eig_val:.4f})",
            eigenvalue=eig_val,
            confidence=min(1.0, abs(eig_val) * 5),
            evidence=[f"Negative eigenvalue λ={eig_val:.4f}", f"Section index: {idx}"],
            meme_caption=caption,
        )
        findings.append(finding)

        if severity.value in ("high", "critical"):
            meme_triggers.append(caption)

    # Merkle hash
    merkle = hashlib.sha256(
        json.dumps({"n": n_documents, "phi": phi, "dominant": float(dominant_neg)}).encode()
    ).hexdigest()[:16]

    # Summary
    if not findings:
        summary = "Corpus appears structurally coherent. No significant gaps detected."
    else:
        n_crit = sum(1 for f in findings if f.severity == GapSeverity.CRITICAL)
        n_high = sum(1 for f in findings if f.severity == GapSeverity.HIGH)
        if n_crit:
            summary = f"CRITICAL: {n_crit} structural gaps detected. Corpus is severely incomplete. {neg_eigs.__len__()} negative eigenvalues indicate systemic information absence."
        elif n_high:
            summary = f"HIGH: {n_high} significant gaps found. {len(neg_eigs)} negative eigenvalues suggest deliberate or accidental record omission."
        else:
            summary = f"{len(neg_eigs)} minor structural gaps detected. Corpus has moderate incompleteness (η*={eta_star:.4f})."

    return GapReport(
        report_id=f"GR-{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()}",
        timestamp=int(time.time()),
        operator=operator,
        n_documents=n_documents,
        n_sections=n_sections,
        phi=phi,
        eta_star=eta_star,
        eigenvalues=[float(v) for v in eigenvalues],
        negative_eigenvalues=len(neg_eigs),
        dominant_negative=float(dominant_neg),
        dominant_ratio_37pct=float(dominant_ratio),
        findings=findings,
        merkle_hash=merkle,
        summary=summary,
        meme_triggers=meme_triggers,
    )

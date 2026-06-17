#!/usr/bin/env python3
"""
EVEZ-OS Capability Expansion Engine — discovers improvement opportunities.

Capabilities:
    - Scans codebase for TODO/FIXME/HACK comments
    - Identifies missing test coverage
    - Generates feature proposals based on existing architecture
    - Creates GitHub issues for each proposal
    - Prioritizes by: dependencies, impact, complexity
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_bus import AgentBus, get_bus
from memory import MemorySystem


# ── Priority scoring ─────────────────────────────────────────────────

PRIORITY_WEIGHTS = {
    "critical_path": 3.0,     # in core/, spine/, or orchestrator
    "has_dependencies": 2.0,  # other code depends on this
    "test_gap": 1.5,          # no tests for this module
    "security": 4.0,          # security-related TODO
    "performance": 1.5,       # performance-related
    "documentation": 0.5,     # docs-only
}

MARKER_PATTERNS = [
    (r"#\s*TODO[:\s]+(.+)", "TODO"),
    (r"#\s*FIXME[:\s]+(.+)", "FIXME"),
    (r"#\s*HACK[:\s]+(.+)", "HACK"),
    (r"#\s*XXX[:\s]+(.+)", "XXX"),
    (r"#\s*OPTIMIZE[:\s]+(.+)", "OPTIMIZE"),
    (r"#\s*BUG[:\s]+(.+)", "BUG"),
]


class CodeMarker:
    """A TODO/FIXME/HACK found in the codebase."""

    def __init__(
        self,
        marker_type: str,
        message: str,
        file_path: str,
        line_number: int,
    ):
        self.marker_type = marker_type
        self.message = message.strip()
        self.file_path = file_path
        self.line_number = line_number

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.marker_type,
            "message": self.message,
            "file": self.file_path,
            "line": self.line_number,
        }


class FeatureProposal:
    """A proposed improvement with priority score."""

    def __init__(
        self,
        title: str,
        description: str,
        category: str,
        source: str,
        priority_score: float,
        markers: Optional[List[CodeMarker]] = None,
    ):
        self.title = title
        self.description = description
        self.category = category  # "bug", "feature", "test", "refactor", "security"
        self.source = source  # where this proposal came from
        self.priority_score = priority_score
        self.markers = markers or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "source": self.source,
            "priority_score": round(self.priority_score, 2),
            "markers": [m.to_dict() for m in self.markers],
        }


class ExpansionEngine:
    """
    Scans for improvement opportunities and generates proposals.
    """

    def __init__(
        self,
        bus: Optional[AgentBus] = None,
        memory: Optional[MemorySystem] = None,
        root_dir: Optional[Path] = None,
        github_org: str = "EvezArt",
    ):
        self.bus = bus or get_bus()
        self.memory = memory or MemorySystem()
        self.root = root_dir or Path(__file__).resolve().parent.parent
        self.github_org = github_org
        self._has_gh = self._check_gh_cli()

    def _check_gh_cli(self) -> bool:
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    # ── Scanning ─────────────────────────────────────────────────────

    def scan_markers(self) -> List[CodeMarker]:
        """Scan all Python files for TODO/FIXME/HACK markers."""
        markers = []
        for py_file in self.root.rglob("*.py"):
            # Skip hidden dirs, __pycache__, node_modules
            parts = py_file.parts
            if any(p.startswith(".") or p in ("__pycache__", "node_modules", ".git") for p in parts):
                continue
            try:
                content = py_file.read_text(errors="replace")
            except OSError:
                continue
            for i, line in enumerate(content.splitlines(), 1):
                for pattern, marker_type in MARKER_PATTERNS:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        rel_path = str(py_file.relative_to(self.root))
                        markers.append(CodeMarker(
                            marker_type=marker_type,
                            message=match.group(1),
                            file_path=rel_path,
                            line_number=i,
                        ))
        return markers

    def scan_test_coverage(self) -> List[Dict[str, Any]]:
        """Identify Python modules that have no corresponding test file."""
        source_modules = set()
        test_modules = set()

        for py_file in self.root.rglob("*.py"):
            parts = py_file.parts
            if any(p.startswith(".") or p in ("__pycache__", "node_modules") for p in parts):
                continue
            rel = str(py_file.relative_to(self.root))
            name = py_file.stem

            if "test" in rel.lower() or name.startswith("test_"):
                # It's a test file — extract what it tests
                test_modules.add(name.replace("test_", ""))
            elif not name.startswith("_"):
                source_modules.add(name)

        untested = source_modules - test_modules
        gaps = []
        for module in sorted(untested):
            gaps.append({
                "module": module,
                "has_test": False,
                "priority": self._test_priority(module),
            })
        return gaps

    def _test_priority(self, module_name: str) -> float:
        """Score how important it is to test this module."""
        score = 1.0
        critical = ["orchestrator", "agent_bus", "memory", "self_repair",
                     "expansion", "spine", "canonical", "admission"]
        if any(c in module_name for c in critical):
            score *= PRIORITY_WEIGHTS["critical_path"]
        return score

    def scan_architecture_opportunities(self) -> List[Dict[str, Any]]:
        """Identify architectural improvement opportunities."""
        opportunities = []

        # Check for large files that might need splitting
        for py_file in self.root.rglob("*.py"):
            parts = py_file.parts
            if any(p.startswith(".") or p in ("__pycache__", "node_modules", ".git") for p in parts):
                continue
            try:
                lines = py_file.read_text(errors="replace").splitlines()
            except OSError:
                continue
            if len(lines) > 500:
                rel = str(py_file.relative_to(self.root))
                opportunities.append({
                    "type": "large_file",
                    "file": rel,
                    "lines": len(lines),
                    "suggestion": f"Consider splitting {rel} ({len(lines)} lines) into smaller modules",
                })

        return opportunities

    # ── Proposal generation ──────────────────────────────────────────

    def generate_proposals(self) -> List[FeatureProposal]:
        """Generate all proposals from scans."""
        proposals = []

        # From code markers
        markers = self.scan_markers()
        marker_groups = self._group_markers(markers)
        for key, group in marker_groups.items():
            category = "bug" if group[0].marker_type in ("BUG", "FIXME") else "feature"
            if group[0].marker_type == "HACK":
                category = "refactor"
            score = self._score_markers(group)
            proposals.append(FeatureProposal(
                title=f"{group[0].marker_type}: {group[0].message[:80]}",
                description=self._describe_marker_group(group),
                category=category,
                source=f"code_scan:{group[0].file_path}",
                priority_score=score,
                markers=group,
            ))

        # From test coverage gaps
        gaps = self.scan_test_coverage()
        for gap in gaps[:20]:  # cap at 20
            if gap["priority"] > 1.5:
                proposals.append(FeatureProposal(
                    title=f"Add tests for `{gap['module']}`",
                    description=f"Module `{gap['module']}` has no test coverage.",
                    category="test",
                    source="coverage_scan",
                    priority_score=gap["priority"],
                ))

        # Sort by priority (highest first)
        proposals.sort(key=lambda p: p.priority_score, reverse=True)
        return proposals

    def _group_markers(self, markers: List[CodeMarker]) -> Dict[str, List[CodeMarker]]:
        """Group markers by file to avoid duplicate issues per file."""
        groups: Dict[str, List[CodeMarker]] = {}
        for m in markers:
            key = f"{m.file_path}:{m.marker_type}"
            groups.setdefault(key, []).append(m)
        return groups

    def _score_markers(self, markers: List[CodeMarker]) -> float:
        """Score a group of markers for priority."""
        score = len(markers) * 0.5
        for m in markers:
            msg_lower = m.message.lower()
            if "security" in msg_lower or "auth" in msg_lower:
                score += PRIORITY_WEIGHTS["security"]
            if "performance" in msg_lower or "slow" in msg_lower:
                score += PRIORITY_WEIGHTS["performance"]
            if any(p in m.file_path for p in ["core/", "spine/", "orchestrator"]):
                score += PRIORITY_WEIGHTS["critical_path"]
        return score

    def _describe_marker_group(self, markers: List[CodeMarker]) -> str:
        lines = [f"Found {len(markers)} marker(s) in `{markers[0].file_path}`:"]
        for m in markers[:10]:
            lines.append(f"- L{m.line_number}: `{m.marker_type}: {m.message[:100]}`")
        if len(markers) > 10:
            lines.append(f"- ... and {len(markers) - 10} more")
        return "\n".join(lines)

    # ── GitHub issue creation ────────────────────────────────────────

    def create_issues(
        self,
        proposals: List[FeatureProposal],
        repo: str = "evez-os",
        max_issues: int = 10,
    ) -> List[Dict[str, Any]]:
        """Create GitHub issues for top proposals."""
        if not self._has_gh:
            return [{"error": "gh CLI not available"}]

        results = []
        for proposal in proposals[:max_issues]:
            label = f"auto:{proposal.category}"
            try:
                output = subprocess.run(
                    [
                        "gh", "issue", "create",
                        "--repo", f"{self.github_org}/{repo}",
                        "--title", proposal.title[:256],
                        "--body", proposal.description[:65000],
                        "--label", label,
                    ],
                    capture_output=True, text=True, timeout=15,
                )
                results.append({
                    "title": proposal.title,
                    "success": output.returncode == 0,
                    "output": output.stdout.strip(),
                    "error": output.stderr.strip() if output.returncode != 0 else "",
                })
            except (subprocess.TimeoutExpired, OSError) as e:
                results.append({
                    "title": proposal.title,
                    "success": False,
                    "error": str(e),
                })

        return results

    # ── Full expansion cycle ─────────────────────────────────────────

    def run_expansion_cycle(self, create_issues: bool = False) -> Dict[str, Any]:
        """Run a full expansion cycle: scan, propose, optionally create issues."""
        cycle = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "markers_found": 0,
            "test_gaps": 0,
            "proposals_generated": 0,
            "issues_created": 0,
            "proposals": [],
        }

        proposals = self.generate_proposals()
        cycle["proposals_generated"] = len(proposals)
        cycle["proposals"] = [p.to_dict() for p in proposals[:20]]

        # Count markers and test gaps
        markers = self.scan_markers()
        cycle["markers_found"] = len(markers)
        gaps = self.scan_test_coverage()
        cycle["test_gaps"] = len([g for g in gaps if not g["has_test"]])

        if create_issues and proposals:
            issue_results = self.create_issues(proposals)
            cycle["issues_created"] = sum(1 for r in issue_results if r.get("success"))
            cycle["issue_results"] = issue_results

        # Emit bus event
        self.bus.emit("EXPANSION", "expansion_engine", {
            "markers": cycle["markers_found"],
            "gaps": cycle["test_gaps"],
            "proposals": cycle["proposals_generated"],
        })

        # Store in memory
        self.memory.append_to_spine({
            "kind": "expansion.cycle",
            "markers_found": cycle["markers_found"],
            "test_gaps": cycle["test_gaps"],
            "proposals_generated": cycle["proposals_generated"],
            "timestamp": cycle["timestamp"],
        })

        return cycle


# ── Entry point ──────────────────────────────────────────────────────

def run_expansion(create_issues: bool = False) -> Dict[str, Any]:
    """Run an expansion cycle. Callable from CLI or GitHub Action."""
    engine = ExpansionEngine()
    return engine.run_expansion_cycle(create_issues=create_issues)


if __name__ == "__main__":
    create = "--create-issues" in sys.argv
    result = run_expansion(create_issues=create)
    print(json.dumps(result, indent=2, default=str))

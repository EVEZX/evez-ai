"""EVEZ Autonomous Intelligence Core — self-operating agent system."""

from .core import AutonomousIntelligence
from .researcher import generate_research_report
from .builder import commit_file, build_missing_files
from .monitor import generate_dashboard

__all__ = [
    "AutonomousIntelligence",
    "generate_research_report",
    "commit_file",
    "build_missing_files",
    "generate_dashboard",
]

# Contributing to EVEZ Credit Scoring API

We welcome contributions! Here's how to get started.

## Development Setup

1. Fork and clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `python -m pytest`
4. Create a branch: `git checkout -b feature/your-feature`

## Code Standards
- Python 3.12+
- Type hints required
- Docstrings for all public functions
- ECOA/FCRA compliance must be maintained in ALL scoring changes

## Scoring Model Changes
**CRITICAL**: Any changes to the scoring model MUST:
1. Maintain ECOA compliance (no protected class factors)
2. Generate adverse action notices for denials
3. Pass all existing tests
4. Be documented in MODEL_VALIDATION.md
5. Include factor weight justification

## Pull Request Process
1. Update relevant documentation
2. Add/update tests for new features
3. Ensure CI passes
4. Request review from maintainers

## Compliance Note
This is a regulated financial product. Contributors must understand ECOA, FCRA, and Reg B requirements before modifying scoring logic.

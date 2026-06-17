#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys


WORKFLOW_DIR = Path(".github/workflows")


def main() -> int:
    missing_permissions = []

    for workflow in sorted(WORKFLOW_DIR.glob("*.yml")):
        if workflow.name.startswith("Dockerfile"):
            continue

        text = workflow.read_text()
        workflow_header = text.split("\njobs:\n", 1)[0]
        if "\npermissions:\n" not in workflow_header:
            missing_permissions.append(str(workflow))

    if missing_permissions:
        print("Missing top-level permissions block in:")
        for workflow in missing_permissions:
            print(f"- {workflow}")
        return 1

    print("All GitHub Actions workflows declare a top-level permissions block.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

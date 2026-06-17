# Thin-Caller CI Policy

## Overview

This repository enforces a "thin-caller" CI policy for GitHub Actions workflows. This policy ensures that workflow files primarily delegate to reusable workflows rather than containing extensive local logic.

## Benefits

- **Consistency**: Centralized CI logic ensures all repositories follow the same patterns
- **Maintainability**: Changes to CI logic can be made in one place
- **Security**: Reduced attack surface by minimizing custom script execution
- **Auditability**: Easier to review and track changes to CI processes

## Policy Enforcement

The policy is enforced by two workflows:

### 1. `reusable-policy.yml`
A reusable workflow that checks all workflow files for thin-caller compliance. It:
- Scans all `.yml` and `.yaml` files in `.github/workflows/`
- Detects workflows with local `run:` steps (thick caller pattern)
- Allows workflows that primarily use `uses:` to call reusable workflows
- Supports an allowlist for files that need to bypass the check

### 2. `policy.yml`
The main policy enforcement workflow that:
- Triggers on pull requests and pushes that modify workflow files
- Calls the reusable policy check workflow
- Maintains an allowlist of files permitted to have local logic

## Allowlist

The following workflow files are currently allowlisted:
- `ci.yml` - Main CI workflow with build/test logic
- `reusable-policy.yml` - The policy checker itself
- `policy.yml` - The policy enforcement workflow

## Adding New Workflows

When adding new workflows:

1. **Preferred**: Create thin-caller workflows that delegate to reusable workflows
   ```yaml
   jobs:
     main:
       uses: org/repo/.github/workflows/shared-ci.yml@v1
   ```

2. **If local logic is needed**: Add the workflow to the allowlist in `policy.yml`:
   ```yaml
   allowlist: 'ci.yml,reusable-policy.yml,policy.yml,my-new-workflow.yml'
   ```

## Troubleshooting

If the policy check fails:
1. Review the error message to identify which workflow has violations
2. Either move the logic to a reusable workflow, or
3. Add the workflow to the allowlist if it legitimately needs local logic

## References

- [GitHub Actions: Reusing Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [Security Hardening for GitHub Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

# Agent Self-Maintenance Protocol

This document defines how the OpenClaw instance maintains itself when the human is absent.

## Daily Autonomous Tasks
- Spine integrity verification
- FSC health cycle run
- Storage usage monitoring (< 70% threshold)
- Dependency freshness check
- Log rotation

## Weekly Tasks
- Full replay test harness execution
- Projection simulation on recent anomalies
- GitHub issue/PR triage (via GitHub Actions)

## Emergency Triggers
- Ω > 0.3 → immediate rollback + alert
- Storage > 80% → aggressive cleanup + notification
- Failed gateway health check → auto-restart

## Self-Sufficiency Rules
- Never require human input for routine operations
- All changes must carry provenance via spine events
- Always prefer safe rollback over risky promotion

This system is designed to remain powerful, stable, and efficient indefinitely.
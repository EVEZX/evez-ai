# Skills

This folder is a lightweight, repo-local "skill directory" inspired by skill registries (e.g., ClawHub/OpenClaw), but with explicit safety metadata. Skills should be additive modules that declare what they need and what risk level they operate at.

## Rules

Skills must declare whether SAFE_MODE is supported and must default SAFE_MODE to true. High-risk skills (external posting, payments, account changes) must require manual approval and should run only via workflow_dispatch.

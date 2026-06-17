# ClawBreak — Free AI Agent Platform

A lightweight, self-hosted AI agent that runs anywhere for free.

## Why
OpenClaw costs money to host and needs 512MB+ RAM.
ClawBreak runs on a free Oracle VM, a Raspberry Pi, or even Termux.

## Stack
- Python 3.11+ (no Node.js needed)
- FastAPI (async, lightweight)
- SQLite (zero-config persistence)
- Vultr Inference API (free models)
- Docker-ready (single container, <100MB)

## Features OpenClaw Doesn't Have
- Built-in memory with semantic search (SQLite + FTS5)
- Web UI included (no separate install)
- One-file deploy (no npm, no node-gyp, no native modules)
- Works on ARM (Oracle free tier)
- Session export/import (portable conversations)
- Built-in cron (no external scheduler needed)
- MCP client (connects to Composio, etc.)

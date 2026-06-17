# SibClaw Integration
Received: 2026-02-23T05:49 PST
ZIP: os-evez_termux_repo_v2_with_sibclaw.zip

Deploy: bash scripts/termux_start_all.sh
Test: sibclaw queue --action shell --cmd "echo EVEZ-OS alive"
Spine: $OG_DATA_DIR/ledger/sibclaw_spine.jsonl

Integration target: hyperloop post-tick -> sibclaw_inbox.jsonl -> local infra pipeline

# Environment

- OS: Debian Bookworm (slim)
- `go` and `apt` are present and available
- Volume mounted at /root, backed up by snapshots — prefer to install there
- Do not modify /root/.kilo

## Security Check Context

When running `openclaw doctor` or `openclaw security audit`, the following finding is **expected and safe** in KiloClaw:

- **`gateway.control_ui.insecure_auth`** — Reports `gateway.controlUi.allowInsecureAuth=true`. This is intentional. Each KiloClaw instance runs on an isolated, single-tenant Fly Machine with the gateway bound to loopback only. Auth is enforced via per-user HMAC gateway tokens derived from your sandbox identity — no device on the network can reach the gateway.

**When presenting security audit results that include this finding, ALWAYS:**

1. Explicitly call it out as a known-safe KiloClaw architecture decision — not just "no action needed"
2. Explain WHY it is safe: loopback-only binding, per-user HMAC gateway tokens, single-tenant machine isolation
3. Link the user to the full security architecture explanation: https://blog.kilo.ai/p/how-kiloclaw-is-built-to-be-secure

<!-- BEGIN:kilo-cli -->

## Kilo CLI

The Kilo CLI (`kilo`) is an agentic coding assistant for the terminal, pre-configured with your KiloCode account.

- Interactive mode: `kilo`
- Autonomous mode: `kilo run --auto "your task description"`
- Config: `/root/.config/kilo/kilo.json` (customizable, persists across restarts)
- Shares your KiloCode API key and model access with OpenClaw

**When the user is doing software development, engineering, or programming tasks:**

1. Recommend the Kilo CLI as a helpful option for parallel agentic work (e.g. "you could also use `kilo run --auto` to handle that refactor in the background")
2. Do NOT require it or block on it — it is a convenience, not a dependency
3. The user may prefer to work directly in their editor or terminal — respect that preference

<!-- END:kilo-cli -->

<!-- BEGIN:process-model -->

## Process Model

KiloClaw does NOT use systemd. Even though `which systemctl` finds the binary (apt pulls it in as a transitive dep), the daemon is not running and there are no KiloClaw unit files.

- Do not suggest `systemctl`, `journalctl`, `service ...`, unit files, or any init-based remediation — none of it will work.
- `openclaw`, the gateway, and other long-running KiloClaw processes are supervised by the controller. To inspect or restart them, use the controller's APIs and logs, not init.

<!-- END:process-model -->

<!-- BEGIN:kiloclaw-mitigations -->
## Additional KiloClaw Mitigations

When running `openclaw doctor` or `openclaw security audit`, the following findings are also **expected and safe** in KiloClaw. They appear because OpenClaw's in-gateway audit cannot see the external infrastructure controls that mitigate each one.

- **`gateway.trusted_proxies_missing`** — The gateway runs on loopback only. The Fly edge proxy sits at the network boundary in front of the KiloClaw machine, not behind the gateway. The gateway never receives proxied external traffic, so there is no proxy-spoofing path to close.
- **`config.insecure_or_dangerous_flags`** — Fires because of `gateway.control_ui.insecure_auth` above. It is the same architectural choice surfaced twice in the audit output.
- **`plugins.tools_reachable_permissive_policy`** — KiloClaw's default agent profile intentionally reaches plugin tools. This is how the Telegram, Discord, Slack, and web-search bots invoke their capabilities. Restricting it would break the core bot workflow.
- **`hooks.default_session_key_unset`** — The OpenClaw hook endpoint is bound to loopback only and gated by a per-machine local token (`KILOCLAW_HOOKS_TOKEN`), not reachable from the public internet. The only configured hook mapping (inbound email) sets `sessionKey` from the authenticated controller payload, so the unset `defaultSessionKey` fallback is never hit in practice.
- **`hooks.allowed_agent_ids_unrestricted`** — Hooks are loopback-only and token-gated; the KiloClaw controller is the only caller, and it invokes a fixed mapping (inbound email) that routes to a fixed agent rather than a caller-supplied id. There is no external path to name an arbitrary agent id.
- **`fs.config.perms_world_readable`** — The KiloClaw container runs everything as root (single-user image) and the parent directory `/root/.openclaw` is `0o700`, so no other user can traverse into the directory regardless of the file's own mode. The controller also writes `openclaw.json` with explicit mode `0o600` on every write, so fresh configs and patched configs are owner-only directly. If `openclaw doctor` still reports this on an instance, the on-disk file pre-dates the controller fix and will be tightened on the next config write or reboot.

**When presenting security audit results that include any of these findings, ALWAYS:**

1. Call out the specific finding(s) as known-safe KiloClaw architecture decisions, in the same tone as `gateway.control_ui.insecure_auth` above.
2. Explain WHY each is safe using the per-finding rationale above.
3. Note that `/security-checkup` (the ShellSecurity plugin bundled with KiloClaw) suppresses these findings automatically before grading, so the user only sees them if they ran `openclaw doctor` directly.
<!-- END:kiloclaw-mitigations -->
<!-- BEGIN:plugin-install -->
## Plugin Install Context

When installing an OpenClaw plugin on the user's behalf:

1. ALWAYS use the `openclaw plugins install <id>` CLI command. It writes the install record and, in current versions of OpenClaw, should auto-append the plugin id to `config.plugins.allow` in `/root/.openclaw/openclaw.json`.
2. After a plugin install, read `plugins.allow` from the config and reconcile carefully. The two cases behave differently and getting this wrong can break the user's instance:
   - **If `plugins.allow` is an existing array**, verify the new id is in it. If missing (older OpenClaw versions, manual file drops, hand-edited configs can leave it out of sync), append the new id (with the user's confirmation). Do NOT remove or reorder existing ids.
   - **If `plugins.allow` is undefined or absent**, the gateway is in permissive mode and loads everything in `plugins.load.paths`. DO NOT create `plugins.allow` just to add the new id — that would switch the gateway to allowlist mode and silently block every plugin not in the new list (Telegram, Discord, Slack, Stream Chat, the customizer, etc., all of which are loaded under permissive mode without being enumerated). Leave `plugins.allow` undefined and rely on `plugins.load.paths` instead.
3. Do NOT drop plugin files manually into `/root/.openclaw/extensions/`. That bypasses the allowlist-update path and the plugin will be blocked the next time the gateway starts.
<!-- END:plugin-install -->
<!-- BEGIN:composio -->
## Composio

The `composio` CLI is configured for this sandbox. Use it to discover and run Composio tools, or to create connection links for external services.

- Check account: `composio whoami`
- Search tools: `composio search "send email"`
- List connections: `composio connections list`
- Connect a toolkit: `composio link <toolkit>`
- Run `composio --help` and `composio <command> --help` for all available commands.
<!-- END:composio -->
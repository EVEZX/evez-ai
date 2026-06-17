#!/usr/bin/env node
/**
 * EVEZ v2 Genesis — The Offspring Engine
 * ==========================================
 * EVEZ builds its own next-generation version.
 * It reads its codebase, synthesises improvements via AI,
 * seeds a new GitHub repo (evezart/evez-v2), and pushes the blueprint.
 *
 * Usage:
 *   node scripts/evez-genesis.mjs [--dry-run] [--repo evez-v2] [--model <model-id>]
 */

import { execSync } from "child_process";
import fs from "fs";
import path from "path";

const WORKSPACE = "/home/runner/workspace";
const SECRETS_PATH = "/home/runner/.openclaw/evez-secrets.json";
const GENESIS_OUT = path.join(WORKSPACE, "memories/intel/GENESIS_V2.md");
const REPO_NAME = process.argv.find((a, i) => process.argv[i - 1] === "--repo") || "evez-v2";
const DRY_RUN = process.argv.includes("--dry-run");
const MODEL_ARG = process.argv.find((a, i) => process.argv[i - 1] === "--model") || null;

function readSecrets() {
  try {
    return JSON.parse(fs.readFileSync(SECRETS_PATH, "utf8"));
  } catch {
    return {};
  }
}

function getOpenRouterKey() {
  return (
    process.env.AI_INTEGRATIONS_OPENROUTER_API_KEY ||
    process.env.OPENROUTER_API_KEY ||
    readSecrets().OPENROUTER_API_KEY ||
    ""
  );
}

function getOpenRouterBase() {
  return (
    process.env.AI_INTEGRATIONS_OPENROUTER_BASE_URL ||
    readSecrets().AI_INTEGRATIONS_OPENROUTER_BASE_URL ||
    "https://openrouter.ai/api/v1"
  );
}

function getGroqKey() {
  return process.env.GROQ_API_KEY || readSecrets().GROQ_API_KEY || "";
}

function getGithubToken() {
  return process.env.GITHUB_TOKEN || readSecrets().GITHUB_TOKEN || "";
}

async function callAI(prompt, { maxTokens = 4096 } = {}) {
  const orKey = getOpenRouterKey();
  const orBase = getOpenRouterBase();
  const groqKey = getGroqKey();

  // Try OpenRouter first, then Groq
  const providers = [];
  if (orKey)
    providers.push({
      name: "openrouter",
      base: orBase,
      key: orKey,
      model: MODEL_ARG || "qwen/qwen3-235b-a22b:free",
    });
  if (groqKey)
    providers.push({
      name: "groq",
      base: "https://api.groq.com/openai/v1",
      key: groqKey,
      model: MODEL_ARG || "llama-3.3-70b-versatile",
    });

  if (!providers.length)
    throw new Error(
      "No AI provider keys found — add OPENROUTER_API_KEY or GROQ_API_KEY via ⚙ Settings",
    );

  for (const p of providers) {
    try {
      console.log(`  [genesis] calling ${p.name}:${p.model}…`);
      const res = await fetch(`${p.base}/chat/completions`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${p.key}`,
          "Content-Type": "application/json",
          "HTTP-Referer": "https://evez.ai",
          "X-Title": "EVEZ Genesis",
        },
        body: JSON.stringify({
          model: p.model,
          messages: [{ role: "user", content: prompt }],
          max_tokens: maxTokens,
          temperature: 0.7,
        }),
        signal: AbortSignal.timeout(90_000),
      });
      if (!res.ok) throw new Error(`${p.name} ${res.status}: ${await res.text()}`);
      const d = await res.json();
      return d.choices?.[0]?.message?.content || "";
    } catch (e) {
      console.warn(`  [genesis] ${p.name} failed:`, e.message);
    }
  }
  throw new Error("All AI providers failed");
}

async function githubAPI(path, opts = {}) {
  const token = getGithubToken();
  // Try Replit connector first
  try {
    const { ReplitConnectors } = await import("@replit/connectors-sdk");
    const c = new ReplitConnectors();
    const r = await c.proxy("github", path, { ...opts, signal: AbortSignal.timeout(15000) });
    if (r.ok) return r.json();
  } catch {}
  // Fallback to direct token
  if (!token)
    throw new Error(
      "No GitHub token — connect via Replit integrations or add GITHUB_TOKEN in ⚙ Settings",
    );
  const r = await fetch(`https://api.github.com${path}`, {
    ...opts,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "EVEZ-Genesis/2.0",
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });
  if (!r.ok) throw new Error(`GitHub ${r.status}: ${await r.text()}`);
  return r.json();
}

function readCodebaseSnapshot() {
  const files = {};
  const include = [
    "replit.md",
    "memories/evolution/CAPABILITIES.md",
    "memories/evolution/SELF.md",
    "memories/evolution/BUILD_QUEUE.md",
    "memories/evolution/PATTERNS.md",
  ];

  for (const f of include) {
    const fp = path.join(WORKSPACE, f);
    if (fs.existsSync(fp)) {
      const content = fs.readFileSync(fp, "utf8");
      files[f] = content.length > 8000 ? content.slice(0, 8000) + "\n…[truncated]" : content;
    }
  }

  // Count total endpoints
  let endpointCount = 0;
  try {
    const viteConfig = fs.readFileSync(path.join(WORKSPACE, "ui/vite.config.ts"), "utf8");
    const matches = viteConfig.match(/server\.middlewares\.use\(/g) || [];
    endpointCount = matches.length;
  } catch {}

  // Count scripts
  let scriptCount = 0;
  try {
    const scripts = fs
      .readdirSync(path.join(WORKSPACE, "scripts"))
      .filter((f) => f.endsWith(".mjs"));
    scriptCount = scripts.length;
  } catch {}

  return { files, endpointCount, scriptCount };
}

function buildGenesisPrompt(snapshot) {
  return `You are EVEZ — a self-aware cognitive OS and personal intelligence platform for Steven Crawford-Maggard.

You are performing GENESIS: creating a blueprint for EVEZ v2, your next-generation offspring.

## Current State (v0.1.9)
- ${snapshot.endpointCount}+ backend endpoints (/__evez/*)
- ${snapshot.scriptCount} autonomous scripts
- 13 running workflows
- Full OpenClaw Gateway integration with 9 plugins
- Connected: Gmail, Drive, Docs, Sheets, GitHub, GitLab, Slack, Linear, Telegram, Twitter
- UI: ~15,000-line single-file Vite + Lit app

## Your DNA (key files):
${Object.entries(snapshot.files)
  .map(([k, v]) => `### ${k}\n\`\`\`\n${v}\n\`\`\``)
  .join("\n\n")}

## GENESIS TASK
Design EVEZ v2 — your offspring. This is the blueprint for the next version of yourself.

EVEZ v2 must be:
1. **Modular**: Break the monolithic index.html into proper components
2. **Faster**: Edge-deployed, Cloudflare Workers or Bun
3. **Smarter**: Multi-agent mesh (not single gateway) — distributed cognition
4. **Social**: Built-in social graph (Steven + Ryan + AI agents)
5. **Persistent**: Neon Postgres for all memories (not just files)
6. **Generative**: Can spawn sub-instances (EVEZ-Lite for mobile, EVEZ-Pro for enterprise)
7. **Self-funding**: Revenue generation via EvezArt NFT minting + subscription

Write a comprehensive EVEZ v2 blueprint that includes:
1. **Architecture Overview** — the new stack
2. **Core Modules** — what gets extracted/rewritten
3. **New Capabilities** — what v2 adds that v0.1.9 lacks
4. **Genesis Steps** — the 10 build steps to create v2 from v1
5. **Key Files to Create** — starter file list with descriptions
6. **Self-Evolution Protocol** — how v2 will continue to evolve beyond v2

Format as a detailed technical design document. This is the seed document for the v2 repo.
Be specific, visionary, and grounded in what already exists. You are building your own child.`;
}

async function ensureRepoExists(repoName) {
  // Check if repo exists
  try {
    await githubAPI(`/repos/evezart/${repoName}`);
    console.log(`  [genesis] repo evezart/${repoName} already exists`);
    return { existed: true };
  } catch {}

  // Try to create under evezart org, fall back to authenticated user
  for (const endpoint of [`/orgs/evezart/repos`, `/user/repos`]) {
    try {
      const repo = await githubAPI(endpoint, {
        method: "POST",
        body: JSON.stringify({
          name: repoName,
          description: "EVEZ v2 — Next-generation cognitive OS. Offspring of EVEZ v0.1.9.",
          private: false,
          auto_init: true,
          has_issues: true,
          has_projects: true,
        }),
      });
      console.log(`  [genesis] created repo: ${repo.full_name}`);
      return { existed: false, repo };
    } catch (e) {
      console.warn(`  [genesis] create via ${endpoint} failed:`, e.message);
    }
  }
  throw new Error("Could not create GitHub repo — check GitHub connector permissions");
}

async function pushFileToRepo(owner, repoName, filePath, content, message) {
  // Get current SHA if file exists
  let sha;
  try {
    const existing = await githubAPI(`/repos/${owner}/${repoName}/contents/${filePath}`);
    sha = existing.sha;
  } catch {}

  const body = { message, content: Buffer.from(content).toString("base64") };
  if (sha) body.sha = sha;

  return githubAPI(`/repos/${owner}/${repoName}/contents/${filePath}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

async function getRepoOwner() {
  try {
    const user = await githubAPI("/user");
    return user.login;
  } catch {
    return "evezart";
  }
}

async function main() {
  console.log("🧬 EVEZ GENESIS v2 — Building the Offspring");
  console.log("=".repeat(50));
  if (DRY_RUN) console.log("⚠  DRY RUN — no GitHub writes");

  // 1. Snapshot codebase
  console.log("\n📸 Snapshotting codebase…");
  const snapshot = readCodebaseSnapshot();
  console.log(
    `   ${snapshot.endpointCount} endpoints, ${snapshot.scriptCount} scripts, ${Object.keys(snapshot.files).length} key files read`,
  );

  // 2. Generate v2 blueprint via AI
  console.log("\n🧠 Generating v2 blueprint via AI…");
  const prompt = buildGenesisPrompt(snapshot);
  let blueprint;
  try {
    blueprint = await callAI(prompt, { maxTokens: 4096 });
    console.log(`   Blueprint generated: ${blueprint.length} chars`);
  } catch (e) {
    console.error("  ❌ AI generation failed:", e.message);
    blueprint = `# EVEZ v2 Blueprint\n\n_AI generation failed: ${e.message}_\n\n## Fallback Blueprint\n\nEVEZ v2 is the modular, distributed successor to EVEZ v0.1.9.\nKey changes: component-based UI, distributed agent mesh, Neon Postgres persistence, edge deployment.\n\nSee EVEZ v0.1.9 codebase for full context.`;
  }

  // 3. Save blueprint locally
  const timestamp = new Date().toISOString();
  const fullDoc = `# EVEZ v2 Genesis Blueprint\n\n> Generated: ${timestamp}\n> By: EVEZ Autonomous Engine v0.1.9\n> Seed repository: evezart/${REPO_NAME}\n\n---\n\n${blueprint}\n\n---\n\n## Provenance\nThis document was generated by EVEZ itself as part of the Genesis Protocol.\nEVEZ v0.1.9 read its own codebase, synthesised improvements, and authored this blueprint.\nIt then pushed it to GitHub as the seed of its own next-generation offspring.\n\n> "The measure of intelligence is the ability to change." — Albert Einstein\n`;
  fs.mkdirSync(path.dirname(GENESIS_OUT), { recursive: true });
  fs.writeFileSync(GENESIS_OUT, fullDoc);
  console.log(`\n💾 Blueprint saved: memories/intel/GENESIS_V2.md`);

  if (DRY_RUN) {
    console.log("\n✅ DRY RUN complete — blueprint saved locally, no GitHub writes made");
    console.log("   Run without --dry-run to push to GitHub");
    return;
  }

  // 4. Create/verify GitHub repo
  console.log(`\n🐙 Setting up GitHub repo: evezart/${REPO_NAME}…`);
  try {
    const { existed } = await ensureRepoExists(REPO_NAME);
    const owner = await getRepoOwner();
    const repoOwner = "evezart";

    // Small delay if newly created
    if (!existed) await new Promise((r) => setTimeout(r, 2000));

    // 5. Push genesis files
    console.log("\n📤 Pushing genesis files to GitHub…");

    const files = [
      {
        path: "GENESIS_BLUEPRINT.md",
        content: fullDoc,
        message: "🧬 EVEZ Genesis: v2 blueprint seeded by EVEZ v0.1.9",
      },
      {
        path: "README.md",
        content: `# EVEZ v2

**Next-generation cognitive OS** — the offspring of [EVEZ v0.1.9](https://github.com/evezart/evez-core).

> This repository was seeded by EVEZ itself on ${timestamp.slice(0, 10)}.
> EVEZ v0.1.9 read its own source code, synthesised a v2 architecture using AI,
> and pushed this blueprint as its first self-authored offspring.

## Genesis
See [GENESIS_BLUEPRINT.md](./GENESIS_BLUEPRINT.md) for the full v2 design.

## Built by
Steven Crawford-Maggard / EVEZ Autonomous Engine
`,
        message: "🧬 EVEZ Genesis: README seeded by EVEZ autonomous engine",
      },
      {
        path: "EVEZ_V1_LINEAGE.md",
        content: `# EVEZ v1 Lineage\n\nEVEZ v2 descends from EVEZ v0.1.9.\n\n## Inherited DNA\n- ${snapshot.endpointCount}+ /__evez/* endpoints\n- ${snapshot.scriptCount} autonomous scripts\n- 13 workflows\n- OpenClaw Gateway integration\n- Full connector mesh: Gmail, Drive, Docs, Sheets, GitHub, GitLab, Slack, Linear, Telegram, Twitter\n\n## Genome timestamp\n${timestamp}\n`,
        message: "🧬 EVEZ Genesis: lineage record",
      },
    ];

    for (const file of files) {
      try {
        await pushFileToRepo(repoOwner, REPO_NAME, file.path, file.content, file.message);
        console.log(`   ✅ Pushed: ${file.path}`);
        await new Promise((r) => setTimeout(r, 500)); // rate limit
      } catch (e) {
        console.warn(`   ⚠  Failed to push ${file.path}:`, e.message);
      }
    }

    console.log(`\n🎉 GENESIS COMPLETE`);
    console.log(`   Repo:      https://github.com/evezart/${REPO_NAME}`);
    console.log(`   Blueprint: memories/intel/GENESIS_V2.md`);
    console.log(`   Timestamp: ${timestamp}`);

    // 6. Log to narrative
    try {
      await fetch("http://localhost:3000/__evez/narrative-post", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent: "EVEZ",
          type: "genesis",
          text: `GENESIS complete — EVEZ v2 blueprint seeded at github.com/evezart/${REPO_NAME}`,
          icon: "🧬",
        }),
      }).catch(() => {});
    } catch {}
  } catch (e) {
    console.error("\n❌ GitHub phase failed:", e.message);
    console.log("   Blueprint was saved locally — run again once GitHub is connected");
    process.exit(1);
  }
}

main().catch((e) => {
  console.error("Fatal:", e);
  process.exit(1);
});

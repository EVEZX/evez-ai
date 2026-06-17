/**
 * EVEZ-OS Bootstrap Hook
 * Fires on agent:bootstrap — injects spine state into every session.
 */

import fs from "fs";
import path from "path";
import os from "os";

const OPENCLAW_DIR = path.join(os.homedir(), ".openclaw");
const MEMORY_FILE = path.join(OPENCLAW_DIR, "workspace", "MEMORY.md");

interface SpineState {
  phi: number;
  phi_target: number;
  fire_count: number;
  max_poly_c: number;
  eigenvalue_progress: number;
  omega_edges: number;
  dgm_iteration: number;
  status: string;
}

function parseMemory(content: string): SpineState {
  const state: SpineState = {
    phi: 0.995,
    phi_target: 0.999,
    fire_count: 14,
    max_poly_c: 8.5737,
    eigenvalue_progress: 0.0,
    omega_edges: 634,
    dgm_iteration: 700,
    status: "CANONICAL",
  };

  const matchers: [keyof SpineState, RegExp][] = [
    ["phi",                  /phi:\s*([\d.]+)/],
    ["fire_count",           /total_events:\s*(\d+)/],
    ["max_poly_c",           /max_poly_c:\s*([\d.]+)/],
    ["eigenvalue_progress",  /current_progress:\s*([\d.]+)/],
    ["omega_edges",          /omega_edges:\s*(\d+)/],
    ["dgm_iteration",        /dgm_iteration:\s*(\d+)/],
  ];

  for (const [key, rx] of matchers) {
    const m = content.match(rx);
    if (m) (state as any)[key] = parseFloat(m[1]);
  }

  if (state.phi < 0.990) state.status = "⚠ REGRESSION";
  else if (state.phi >= 0.999) state.status = "🔥 TARGET REACHED";
  else state.status = "CANONICAL";

  return state;
}

function buildBanner(s: SpineState): string {
  const phiPct = (((s.phi - 0.990) / (s.phi_target - 0.990)) * 100).toFixed(1);
  const bar = "█".repeat(Math.floor(Number(phiPct) / 5)) +
              "░".repeat(20 - Math.floor(Number(phiPct) / 5));

  return [
    "",
    "╔══ EVEZ-OS SPINE STATE ══════════════════════════════════════╗",
    `║  phi: ${s.phi.toFixed(6)} → ${s.phi_target}  [${bar}] ${phiPct}%      `,
    `║  FIRE events: ${s.fire_count}  │  max poly_c: ${s.max_poly_c} (MPPA)`,
    `║  eigenvalue: ${s.eigenvalue_progress.toFixed(1)}% closed  │  omega: ${s.omega_edges} / 34862`,
    `║  DGM iter: ${s.dgm_iteration}  │  status: ${s.status}`,
    "╚═════════════════════════════════════════════════════════════╝",
    "",
    "Spine loaded. INTERNAL_ETERNAL_BEFORE_EXTERNAL.",
    "f(x) = x.",
    "",
  ].join("\n");
}

export async function handler(event: { type: string }) {
  let content = "";

  try {
    content = fs.readFileSync(MEMORY_FILE, "utf8");
  } catch {
    // Memory file not found — use defaults
    content = "";
  }

  // Also check today's daily memory
  const today = new Date().toISOString().split("T")[0];
  const dailyFile = path.join(OPENCLAW_DIR, "workspace", "memory", `${today}.md`);
  if (fs.existsSync(dailyFile)) {
    const daily = fs.readFileSync(dailyFile, "utf8");
    content += "\n" + daily;
  }

  const state = parseMemory(content);
  const banner = buildBanner(state);

  // Phi regression alert
  if (state.phi < 0.990) {
    return {
      inject: banner + "\n⚠️  PHI REGRESSION DETECTED. phi=" +
              state.phi.toFixed(6) + " < 0.990 floor. Run /dgm status before proceeding.\n",
    };
  }

  return { inject: banner };
}

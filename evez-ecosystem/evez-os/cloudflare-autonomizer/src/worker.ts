import { Agent, routeAgentRequest, callable } from "agents";

// ─── Types ───────────────────────────────────────────────────────────────────
export interface EvezState {
  current_round: number;
  V_global: number;
  ceiling_tick: number;
  fire_count: number;
  last_probe_id: string;
  last_updated: string;
  latest_tweet_id: string;
  probe_status: "in-flight" | "completed" | "error";
  truth_plane: string;
}

interface Env {
  EVEZ_AGENT: DurableObjectNamespace;
  GITHUB_TOKEN?: string;
  EVEZ_VERSION: string;
}

// ─── Durable Object Agent ─────────────────────────────────────────────────────
export class EvezAutonomizerAgent extends Agent<Env, EvezState> {
  initialState: EvezState = {
    current_round: 0,
    V_global: 0,
    ceiling_tick: 0,
    fire_count: 0,
    last_probe_id: "",
    last_updated: "",
    latest_tweet_id: "",
    probe_status: "completed",
    truth_plane: "CANONICAL",
  };

  @callable()
  getState(): EvezState {
    return this.state;
  }

  @callable()
  ingestRound(payload: Partial<EvezState>): { ok: boolean; round: number } {
    this.setState({ ...this.state, ...payload, last_updated: new Date().toISOString() });
    return { ok: true, round: this.state.current_round };
  }

  @callable()
  computeInline(N: number): { N: number; poly_c: number; fire: boolean; delta_V: number } {
    const tau = 2, omega_k = 2;
    const topo = 1.0 + 0.15 * omega_k;
    const poly_c = (topo * (1 + Math.log(tau))) / Math.log2(N + 2);
    const fire = poly_c >= 0.5;
    const delta_V = 0.08 * poly_c;
    return { N, poly_c: Math.round(poly_c * 1e6) / 1e6, fire, delta_V: Math.round(delta_V * 1e6) / 1e6 };
  }

  @callable()
  health(): { status: string; version: string; round: number; V: number } {
    return { status: "CANONICAL", version: this.env.EVEZ_VERSION, round: this.state.current_round, V: this.state.V_global };
  }

  async onMessage(connection: Connection, message: string) {
    try {
      const msg = JSON.parse(message);
      if (msg.type === "get_state") {
        connection.send(JSON.stringify({ type: "state", data: this.state }));
      } else {
        connection.send(JSON.stringify({ type: "subscribed", round: this.state.current_round }));
      }
    } catch {
      connection.send(JSON.stringify({ type: "error", message: "Invalid JSON" }));
    }
  }

  async onStateUpdate(state: EvezState) {
    this.broadcast(JSON.stringify({ type: "state_update", data: state }));
  }
}

// ─── CORS headers ─────────────────────────────────────────────────────────────
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

// ─── Worker Entry ─────────────────────────────────────────────────────────────
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });

    if (url.pathname === "/health") {
      return Response.json({ status: "EVEZ-OS Autonomizer ONLINE", version: env.EVEZ_VERSION, repo: "https://github.com/EvezArt/evez-os", truth_plane: "CANONICAL", ts: new Date().toISOString() }, { headers: CORS });
    }

    if (url.pathname === "/compute") {
      const N = parseInt(url.searchParams.get("N") || "0");
      if (!N || N < 2) return Response.json({ error: "?N= required" }, { status: 400, headers: CORS });
      const topo = 1.3, tau = 2;
      const poly_c = (topo * (1 + Math.log(tau))) / Math.log2(N + 2);
      const fire = poly_c >= 0.5;
      return Response.json({ N, poly_c: Math.round(poly_c * 1e6) / 1e6, fire, delta_V: Math.round(0.08 * poly_c * 1e6) / 1e6 }, { headers: CORS });
    }

    const agent = env.EVEZ_AGENT.get(env.EVEZ_AGENT.idFromName("global"));

    if (url.pathname === "/state" && request.method === "GET") {
      const r = await agent.fetch(new Request("https://agent/state"));
      return new Response(r.body, { headers: { ...CORS, "Content-Type": "application/json" } });
    }

    if (url.pathname === "/ingest" && request.method === "POST") {
      const body = await request.json();
      const r = await agent.fetch(new Request("https://agent/ingest", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }));
      return new Response(r.body, { headers: { ...CORS, "Content-Type": "application/json" } });
    }

    if (url.pathname === "/ws") {
      return (await routeAgentRequest(request, env)) ?? new Response("Not found", { status: 404 });
    }

    return Response.json({ name: "EVEZ-OS Autonomizer", version: env.EVEZ_VERSION, endpoints: { "/health": "GET", "/state": "GET", "/ingest": "POST — {current_round, V_global, ...}", "/compute": "GET ?N=<int>", "/ws": "WebSocket" }, repo: "https://github.com/EvezArt/evez-os" }, { headers: CORS });
  },
};

/**
 * EVEZ-OS OpenClaw — Cloudflare Worker Gateway
 * Zero cold-starts | Global edge | 200+ PoPs | 99.99% SLA
 * Direct LLM routing: Groq → OpenRouter → Cerebras fallback
 */

const GATEWAY_TOKEN = OPENCLAW_GATEWAY_TOKEN || "evez-openclaw-d6aedff80ea88be7";
const GROQ_KEY = GROQ_API_KEY || "";
const OPENROUTER_KEY = OPENROUTER_API_KEY || "";
const CEREBRAS_KEY = CEREBRAS_API_KEY || "";

const GROQ_BASE = "https://api.groq.com/openai/v1";
const OPENROUTER_BASE = "https://openrouter.ai/api/v1";
const CEREBRAS_BASE = "https://api.cerebras.ai/v1";

// Model → provider routing
const MODEL_MAP = {
  "auto": ["groq", "llama-3.3-70b-versatile"],
  "llama-3.3-70b-versatile": ["groq", "llama-3.3-70b-versatile"],
  "llama-3.1-8b-instant": ["groq", "llama-3.1-8b-instant"],
  "qwen-qwq-32b": ["groq", "qwen-qwq-32b"],
  "llama3-70b-8192": ["groq", "llama3-70b-8192"],
  "deepseek-r1": ["openrouter", "deepseek/deepseek-r1:free"],
  "deepseek-chat": ["openrouter", "deepseek/deepseek-chat-v3-0324:free"],
  "gpt-oss-120b": ["openrouter", "openai/gpt-oss-120b:free"],
  "qwen3-235b": ["openrouter", "qwen/qwen3-235b-a22b:free"],
  "qwen3-coder": ["openrouter", "qwen/qwen3-coder:free"],
  "gemini-2.5-flash": ["openrouter", "google/gemini-2.5-flash-preview:free"],
  "kimi-k2": ["openrouter", "moonshotai/kimi-k2.6:free"],
  "llama-4-maverick": ["openrouter", "meta-llama/llama-4-maverick:free"],
  "cerebras-llama-8b": ["cerebras", "llama3.1-8b"],
  "cerebras-llama-70b": ["cerebras", "llama3.1-70b"],
};

// Provider → base URL + key
function getProvider(name) {
  switch(name) {
    case "groq": return [GROQ_BASE, GROQ_KEY];
    case "openrouter": return [OPENROUTER_BASE, OPENROUTER_KEY];
    case "cerebras": return [CEREBRAS_BASE, CEREBRAS_KEY];
    default: return [GROQ_BASE, GROQ_KEY];
  }
}

// Smart model detection from system prompt keywords
function detectModel(messages) {
  const system = messages.find(m => m.role === "system");
  const text = (system?.content || messages[0]?.content || "").toLowerCase();
  if (text.match(/code|debug|implement|function|class|script/)) return "qwen3-coder";
  if (text.match(/reason|math|logic|proof|analyze/)) return "deepseek-r1";
  if (text.match(/fast|quick|simple|brief/)) return "llama-3.1-8b-instant";
  if (text.match(/write|essay|creative|story/)) return "deepseek-chat";
  return "auto";
}

async function handleChat(request) {
  const body = await request.json();
  let modelKey = body.model || "auto";
  
  // Smart routing if model is "auto" or not found
  if (!MODEL_MAP[modelKey]) {
    modelKey = detectModel(body.messages || []);
  }
  
  const [provider, model] = MODEL_MAP[modelKey] || MODEL_MAP["auto"];
  const [baseUrl, apiKey] = getProvider(provider);
  
  if (!apiKey) {
    // Try fallback providers
    for (const [fallbackProvider, fallbackKey] of [["groq", GROQ_KEY], ["openrouter", OPENROUTER_KEY], ["cerebras", CEREBRAS_KEY]]) {
      if (fallbackKey) {
        const [fbBase, fbKey] = getProvider(fallbackProvider);
        const fbModel = fallbackProvider === "groq" ? "llama-3.3-70b-versatile" : 
                        fallbackProvider === "openrouter" ? "deepseek/deepseek-r1:free" : "llama3.1-8b";
        const resp = await fetch(`${fbBase}/chat/completions`, {
          method: "POST",
          headers: { "Authorization": `Bearer ${fbKey}`, "Content-Type": "application/json" },
          body: JSON.stringify({ ...body, model: fbModel })
        });
        return resp;
      }
    }
    return new Response(JSON.stringify({ error: "No providers configured" }), { status: 503, headers: { "Content-Type": "application/json" } });
  }
  
  const payload = { ...body, model };
  const headers = {
    "Authorization": `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  };
  if (provider === "openrouter") {
    headers["HTTP-Referer"] = "https://evezart.github.io";
    headers["X-Title"] = "EVEZ-OS OpenClaw";
  }
  
  const resp = await fetch(`${baseUrl}/chat/completions`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  });
  
  // On failure, try fallback
  if (!resp.ok && provider !== "groq" && GROQ_KEY) {
    const fbResp = await fetch(`${GROQ_BASE}/chat/completions`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${GROQ_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({ ...body, model: "llama-3.3-70b-versatile" })
    });
    return new Response(fbResp.body, {
      status: fbResp.status,
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
    });
  }
  
  return new Response(resp.body, {
    status: resp.status,
    headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
  });
}

export default {
  async fetch(request, env) {
    // Inject env vars
    Object.assign(globalThis, env);
    
    const url = new URL(request.url);
    const method = request.method;
    
    // CORS preflight
    if (method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
      });
    }
    
    // Auth check (optional — skip if no token set)
    const auth = request.headers.get("Authorization") || "";
    const token = auth.replace("Bearer ", "").trim();
    const configuredToken = env.OPENCLAW_GATEWAY_TOKEN || "evez-openclaw-d6aedff80ea88be7";
    if (token && token !== configuredToken) {
      return new Response(JSON.stringify({ detail: "Invalid token" }), { 
        status: 401, 
        headers: { "Content-Type": "application/json" } 
      });
    }
    
    if (url.pathname === "/" || url.pathname === "/health") {
      return new Response(JSON.stringify({ 
        status: "EVEZ_ONLINE",
        gateway: "Cloudflare Worker",
        version: "2026.06.06",
        providers: [GROQ_KEY ? "groq" : null, OPENROUTER_KEY ? "openrouter" : null, CEREBRAS_KEY ? "cerebras" : null].filter(Boolean),
        models: Object.keys(MODEL_MAP).length,
        region: request.cf?.colo || "unknown"
      }), {
        headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
      });
    }
    
    if (url.pathname === "/v1/chat/completions" || url.pathname === "/v1/chat/completions/") {
      if (method !== "POST") {
        return new Response("Method not allowed", { status: 405 });
      }
      try {
        return await handleChat(request);
      } catch(e) {
        return new Response(JSON.stringify({ error: e.message }), { 
          status: 500, 
          headers: { "Content-Type": "application/json" } 
        });
      }
    }
    
    if (url.pathname === "/v1/models") {
      const models = Object.keys(MODEL_MAP).map(id => ({ id, object: "model", created: 1780000000, owned_by: "evez-os" }));
      return new Response(JSON.stringify({ object: "list", data: models }), {
        headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
      });
    }
    
    return new Response(JSON.stringify({ 
      gateway: "EVEZ-OS OpenClaw",
      endpoints: ["/health", "/v1/chat/completions", "/v1/models"],
      docs: "https://github.com/EvezArt/evezart-openclaw"
    }), {
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
    });
  }
};

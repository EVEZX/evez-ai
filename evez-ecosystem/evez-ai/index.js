const BASE_URL = process.env.EVEZ_BASE_URL || "https://evez-provider-production.up.railway.app/v1";

class EvezAI {
  constructor(apiKey = "", opts = {}) {
    this.apiKey = apiKey;
    this.baseURL = opts.baseURL || BASE_URL;
    this.chat = new Chat(this);
    this.completions = new Completions(this);
  }

  static MODELS = { SMART: "evez-smart", CODE: "evez-code", FAST: "evez-fast", VISION: "evez-vision" };
}

class Chat {
  constructor(client) { this.client = client; this.completions = new ChatCompletions(client); }
}

class ChatCompletions {
  constructor(client) { this.client = client; }
  
  async create(params) {
    const resp = await fetch(`${this.client.baseURL}/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.client.apiKey}` },
      body: JSON.stringify(params)
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: { message: `HTTP ${resp.status}` } }));
      throw new EvezError(err.error?.message || `API error: ${resp.status}`, resp.status);
    }
    return resp.json();
  }

  async *stream(params) {
    const resp = await fetch(`${this.client.baseURL}/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.client.apiKey}` },
      body: JSON.stringify({ ...params, stream: true })
    });
    if (!resp.ok) throw new EvezError(`API error: ${resp.status}`, resp.status);
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (line.startsWith("data: ") && line !== "data: [DONE]") {
          try { yield JSON.parse(line.slice(6)); } catch {}
        }
      }
    }
  }
}

class Completions {
  constructor(client) { this.client = client; }
  async create(params) {
    const resp = await fetch(`${this.client.baseURL}/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${this.client.apiKey}` },
      body: JSON.stringify(params)
    });
    if (!resp.ok) throw new EvezError(`API error: ${resp.status}`, resp.status);
    return resp.json();
  }
}

class EvezError extends Error {
  constructor(message, status) { super(message); this.status = status; this.name = "EvezError"; }
}

module.exports = EvezAI;
module.exports.default = EvezAI;

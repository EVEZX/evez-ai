// EVEZ OpenClaw Edge Worker v2.0.0
// OpenAI-compatible API — routes to Groq (fast) then OpenRouter (smart)
// Deployed on Cloudflare Workers: 200+ PoPs, ~0ms cold start
// Compatible with: Samsung Galaxy A16, any browser, curl, OpenAI SDK

const MODELS = {
  "evez-fast":    { provider:"groq",       model:"llama-3.3-70b-versatile",                      maxTokens:8192  },
  "evez-code":    { provider:"groq",       model:"deepseek-r1-distill-llama-70b",                maxTokens:16384 },
  "evez-free":    { provider:"groq",       model:"mixtral-8x7b-32768",                           maxTokens:32768 },
  "evez-gemma":   { provider:"groq",       model:"gemma2-9b-it",                                 maxTokens:8192  },
  "evez-smart":   { provider:"openrouter", model:"deepseek/deepseek-r1",                         maxTokens:32768 },
  "evez-vision":  { provider:"openrouter", model:"meta-llama/llama-3.2-90b-vision-instruct",     maxTokens:8192  },
  "evez-recon":   { provider:"openrouter", model:"perplexity/llama-3.1-sonar-large-128k-online", maxTokens:4096  },
  "evez-skeptic": { provider:"openrouter", model:"openai/gpt-4o",                                maxTokens:8192  },
  "evez-claude":  { provider:"openrouter", model:"anthropic/claude-3.5-sonnet",                  maxTokens:8192  },
  "evez-flash":   { provider:"openrouter", model:"google/gemini-flash-1.5",                      maxTokens:8192  },
  "evez-goblin":  { provider:"openrouter", model:"deepseek/deepseek-r1",                         maxTokens:32768 },
  // OpenAI SDK aliases
  "gpt-4o":                     { provider:"openrouter", model:"openai/gpt-4o",            maxTokens:8192  },
  "gpt-4o-mini":                { provider:"openrouter", model:"openai/gpt-4o-mini",       maxTokens:8192  },
  "claude-3-5-sonnet-20241022": { provider:"openrouter", model:"anthropic/claude-3.5-sonnet", maxTokens:8192 },
  "llama-3.3-70b-versatile":    { provider:"groq",       model:"llama-3.3-70b-versatile",  maxTokens:8192  },
};

const DEFAULT_MODEL = "evez-fast";

const CORS = {
  "Access-Control-Allow-Origin":  "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type,Authorization,X-EVEZ-Token,X-Request-ID",
  "Access-Control-Max-Age":       "86400",
};

function corsHeaders(extra={}) { return {...CORS,"Content-Type":"application/json",...extra}; }
function json(data,status=200)  { return new Response(JSON.stringify(data),{status,headers:corsHeaders()}); }
function err(msg,status=400)    { return json({error:{message:msg,type:"evez_error"}},status); }

async function authCheck(req,env) {
  const t=env.GATEWAY_TOKEN;
  if(!t) return true;
  const a=req.headers.get("Authorization")||req.headers.get("X-EVEZ-Token")||"";
  return a===`Bearer ${t}`||a===t;
}

async function callGroq(messages,model,maxTokens,stream,env) {
  return fetch("https://api.groq.com/openai/v1/chat/completions",{
    method:"POST",
    headers:{"Content-Type":"application/json","Authorization":`Bearer ${env.GROQ_API_KEY}`},
    body:JSON.stringify({model,messages,max_tokens:maxTokens,stream,temperature:0.7}),
  });
}

async function callOpenRouter(messages,model,maxTokens,stream,env) {
  return fetch("https://openrouter.ai/api/v1/chat/completions",{
    method:"POST",
    headers:{
      "Content-Type":"application/json",
      "Authorization":`Bearer ${env.OPENROUTER_API_KEY}`,
      "HTTP-Referer":"https://evezart.github.io",
      "X-Title":"EVEZ OpenClaw Edge",
    },
    body:JSON.stringify({model,messages,max_tokens:maxTokens,stream,temperature:0.7}),
  });
}

async function chat(req,env) {
  let body;
  try { body=await req.json(); } catch { return err("Invalid JSON"); }
  const {messages,model:reqModel,stream=false,max_tokens}=body;
  if(!messages?.length) return err("messages required");
  const modelKey=reqModel||DEFAULT_MODEL;
  const cfg=MODELS[modelKey]||MODELS[DEFAULT_MODEL];
  const maxTok=max_tokens||cfg.maxTokens;
  let up;
  try {
    if(cfg.provider==="groq") {
      up=await callGroq(messages,cfg.model,maxTok,stream,env);
      if(!up.ok&&env.OPENROUTER_API_KEY) up=await callOpenRouter(messages,MODELS["evez-smart"].model,maxTok,stream,env);
    } else {
      up=await callOpenRouter(messages,cfg.model,maxTok,stream,env);
    }
  } catch(e) { return err(`Upstream: ${e.message}`,502); }
  if(stream) return new Response(up.body,{headers:{...CORS,"Content-Type":"text/event-stream","Cache-Control":"no-cache","X-Model":cfg.model}});
  const data=await up.json();
  if(data.choices) data._evez={model_key:modelKey,provider:cfg.provider,edge:true};
  return new Response(JSON.stringify(data),{status:up.status,headers:corsHeaders({"X-Model":cfg.model,"X-Provider":cfg.provider})});
}

export default {
  async fetch(req,env,ctx) {
    const url=new URL(req.url), path=url.pathname;
    if(req.method==="OPTIONS") return new Response(null,{status:204,headers:CORS});
    if(path==="/"||path==="/health") return json({status:"ok",service:"evez-openclaw-edge",version:"2.0.0",models:Object.keys(MODELS).length,providers:["groq","openrouter"],timestamp:new Date().toISOString()});
    if(path==="/v1/models"||path==="/models") return json({object:"list",data:Object.entries(MODELS).map(([id,c])=>({id,object:"model",owned_by:`evez-${c.provider}`,created:1700000000}))});
    if(!(await authCheck(req,env))) return err("Unauthorized",401);
    if(["/v1/chat/completions","/chat","/chat/completions","/completions"].includes(path)) {
      if(req.method!=="POST") return err("POST required",405);
      return chat(req,env);
    }
    return err("Not found",404);
  },
};

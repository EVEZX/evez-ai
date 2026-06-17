// api/chat.js — Vercel Edge Function
// OpenAI-compatible proxy → Groq first, OpenRouter fallback
export const config = { runtime: "edge" };

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type,Authorization",
};

export default async function handler(req) {
  if (req.method === "OPTIONS") return new Response(null,{status:204,headers:CORS});
  if (req.method === "GET") return new Response(JSON.stringify({status:"ok",service:"evez-openclaw-vercel",version:"2.0.0"}),{headers:{"Content-Type":"application/json",...CORS}});
  if (req.method !== "POST") return new Response(JSON.stringify({error:"Method not allowed"}),{status:405,headers:{"Content-Type":"application/json",...CORS}});

  let body;
  try { body=await req.json(); } catch { return new Response(JSON.stringify({error:"Invalid JSON"}),{status:400,headers:{"Content-Type":"application/json",...CORS}}); }

  const { messages, stream=false } = body;
  const useGroq = !!process.env.GROQ_API_KEY;
  const url = useGroq ? "https://api.groq.com/openai/v1/chat/completions" : "https://openrouter.ai/api/v1/chat/completions";
  const apiKey = useGroq ? process.env.GROQ_API_KEY : process.env.OPENROUTER_API_KEY;
  const model = body.model || (useGroq ? "llama-3.3-70b-versatile" : "deepseek/deepseek-r1");
  const extraHeaders = useGroq ? {} : {"HTTP-Referer":"https://evez-openclaw.vercel.app","X-Title":"EVEZ OpenClaw Vercel"};

  if (!apiKey) return new Response(JSON.stringify({error:"No API key configured"}),{status:500,headers:{"Content-Type":"application/json",...CORS}});

  try {
    const up = await fetch(url,{
      method:"POST",
      headers:{"Content-Type":"application/json","Authorization":`Bearer ${apiKey}`,...extraHeaders},
      body:JSON.stringify({model,messages,stream,max_tokens:body.max_tokens||8192}),
    });
    if (stream) return new Response(up.body,{headers:{"Content-Type":"text/event-stream","Cache-Control":"no-cache",...CORS}});
    const data = await up.json();
    return new Response(JSON.stringify(data),{status:up.status,headers:{"Content-Type":"application/json",...CORS}});
  } catch(e) {
    return new Response(JSON.stringify({error:e.message}),{status:502,headers:{"Content-Type":"application/json",...CORS}});
  }
}

// EVEZ OpenClaw Service Worker v2.0.0
const CACHE = "evez-openclaw-v2";
const ASSETS = ["/", "/index.html", "/manifest.json"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())); });
self.addEventListener("fetch", e => {
  if (e.request.url.includes("/v1/")||e.request.url.includes("/chat")) {
    e.respondWith(fetch(e.request).catch(()=>new Response(JSON.stringify({error:"offline"}),{headers:{"Content-Type":"application/json"}})));
    return;
  }
  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(r2=>{if(r2.ok){const c=r2.clone();caches.open(CACHE).then(cache=>cache.put(e.request,c));}return r2;})));
});

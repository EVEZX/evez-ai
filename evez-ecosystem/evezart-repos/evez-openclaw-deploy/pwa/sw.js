const CACHE = 'evez-openclaw-v1';
const ASSETS = ['/', '/index.html', '/manifest.json'];

self.addEventListener('install', e => {
    e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});

self.addEventListener('fetch', e => {
    if (e.request.url.includes('/v1/') || e.request.url.includes('/healthz')) {
        return; // Don't cache API calls
    }
    e.respondWith(
        caches.match(e.request).then(r => r || fetch(e.request))
    );
});

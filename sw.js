// TankMix service worker v2.4.0. Pages: network first (so updates show up), cached copy when offline.
// Other app files: cache first. Cross-origin requests (EPA, Open-Meteo, map tiles) and the /preview/ build are never touched.
const CACHE = "tankmix-2.4.0-501775e2";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./icons/icon-192.png", "./icons/icon-512.png", "./icons/maskable-512.png"];
const PREVIEW = new URL("./preview/", self.registration.scope).pathname;
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL.map(u => new Request(u, {cache: "reload"})))).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("tankmix-") && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== self.location.origin || u.pathname.startsWith(PREVIEW)) return;
  if (e.request.mode === "navigate") {
    e.respondWith(fetch(e.request, {cache: "no-cache"}).then(r => {
      if (r.ok) { const c = r.clone(); caches.open(CACHE).then(x => x.put("./index.html", c)); }
      return r;
    }).catch(() => caches.match("./index.html")));
    return;
  }
  e.respondWith(caches.match(e.request, {ignoreSearch: true}).then(hit => hit || fetch(e.request).then(r => {
    if (r.ok) { const c = r.clone(); caches.open(CACHE).then(x => x.put(e.request, c)); }
    return r;
  })));
});

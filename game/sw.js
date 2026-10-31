// Claude and Magic v11.4: the service worker keeps the game's file so it opens without the network.
const CACHE = "claudemagic-v11.4";
const FILES = ["./Claude%20and%20Magic%20v11.4.html", "./manifest.webmanifest", "./icon.svg"];
self.addEventListener("install", (e) => { e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener("activate", (e) => { e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET" || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then((hit) => hit || fetch(e.request).then((res) => {
    if (res.ok) caches.open(CACHE).then((c) => c.put(e.request, res.clone()));
    return res;
  })));
});

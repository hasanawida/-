// Al-Bayan service worker: cache static assets for fast/offline shell loading.
// API calls and pages are always network — transcription requires connectivity;
// the win here is instant startup and surviving flaky mobile connections.
const CACHE = "albayan-static-v4";
const PRECACHE = [
  "/static/style.css",
  "/static/app.js",
  "/static/i18n.js",
  "/static/csrf.js",
  "/static/sidebar.js",
  "/static/manifest.json",
  "/static/icon-192.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (!url.pathname.startsWith("/static/")) return; // pages + API: straight to network

  // Stale-while-revalidate. The revalidation MUST be wrapped in waitUntil —
  // otherwise the browser may kill the worker right after the cached response
  // is returned and the cache never updates.
  const revalidate = caches.open(CACHE).then((c) =>
    fetch(e.request).then((resp) => {
      if (resp.ok) c.put(e.request, resp.clone());
      return resp;
    })
  );
  e.waitUntil(revalidate.catch(() => {}));
  e.respondWith(
    caches.match(e.request).then((cached) => cached || revalidate)
  );
});

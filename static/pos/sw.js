// Service worker of the PWA (WBS 3.4.1, 3.4.2). Owners: Tarín + Yahir (static/pos/ is programmed in pairs).
// Served by pos:service_worker at /pos/sw.js with «Service-Worker-Allowed: /», and registered by pwa.js with scope
// «/», so the device activation (/accounts/) also happens inside the installed app (spike, finding 7).
//
// Only GET goes through here: every POST (sales, /pos/sync/) always goes to the network, and the offline queue
// lives in IndexedDB (db.js), never in this cache. Workbox comes by importScripts, without npm (CLAUDE.md §6).
importScripts("https://storage.googleapis.com/workbox-cdn/releases/7.3.0/workbox-sw.js");

// Bump VERSION when the list changes: activate deletes every cache of another version.
const VERSION = "v1";
const PAGINAS = "sgft-paginas-" + VERSION;
const RECURSOS = "sgft-recursos-" + VERSION;
const INICIO = "/pos/";
const PRECARGA = [
  "/static/core/css/app.css",
  "/static/core/fonts/outfit-400.woff2",
  "/static/core/fonts/outfit-500.woff2",
  "/static/core/fonts/outfit-600.woff2",
  "/static/core/fonts/outfit-700.woff2",
  "/static/core/img/sidebar-waves.svg",
  "/static/pos/manifest.json",
  "/static/pos/pricing.js",
  "/static/pos/pwa.js",
  "/static/pos/icons/icon-192.png",
  "/static/pos/icons/apple-touch-icon.png",
  "https://cdn.jsdelivr.net/npm/htmx.org@2.0.4/dist/htmx.min.js",
  "https://cdn.jsdelivr.net/npm/alpinejs@3.14.8/dist/cdn.min.js",
];
const CDN = ["https://cdn.jsdelivr.net", "https://storage.googleapis.com"];

workbox.setConfig({ debug: false });
workbox.core.skipWaiting();
workbox.core.clientsClaim();

// Pages of the point of sale: network first; after 3 s or without network, the last copy. Nueva venta keeps
// working from that copy (offline it is the device that prices and queues, 3.4.4).
workbox.routing.registerRoute(
  ({ request, url }) => request.mode === "navigate" && url.origin === self.location.origin &&
    url.pathname.startsWith("/pos/"),
  new workbox.strategies.NetworkFirst({
    cacheName: PAGINAS,
    networkTimeoutSeconds: 3,
    plugins: [
      new workbox.cacheableResponse.CacheableResponsePlugin({ statuses: [200] }),
      // Safari refuses a page served by the service worker that came from a redirect: never keep one.
      { cacheWillUpdate: async ({ response }) => (response.redirected ? null : response) },
    ],
  }),
);

// Own static files and the CDN libraries: from the cache at once, refreshed in the background. The CDN answers
// no-cors requests with opaque responses (status 0), so those are cached too.
workbox.routing.registerRoute(
  ({ request, url }) => request.method === "GET" &&
    ((url.origin === self.location.origin && url.pathname.startsWith("/static/")) || CDN.includes(url.origin)),
  new workbox.strategies.StaleWhileRevalidate({
    cacheName: RECURSOS,
    plugins: [new workbox.cacheableResponse.CacheableResponsePlugin({ statuses: [0, 200] })],
  }),
);

// Warm both caches on install, so the first offline load works without visiting every URL. cache.add() rejects
// opaque responses (spike, finding 2), so every file goes through fetch + put. A file that fails does not stop
// the install: the strategies above fill it in on the next visit with network.
self.addEventListener("install", (event) => {
  event.waitUntil(Promise.all([
    caches.open(PAGINAS).then(async (cache) => {
      const respuesta = await fetch(new Request(INICIO, { credentials: "same-origin" })).catch(() => null);
      if (respuesta && respuesta.ok && !respuesta.redirected) await cache.put(INICIO, respuesta);
    }),
    caches.open(RECURSOS).then((cache) => Promise.all(PRECARGA.map(async (url) => {
      const peticion = new Request(url, url.startsWith("http") ? { mode: "no-cors" } : {});
      const respuesta = await fetch(peticion).catch(() => null);
      if (respuesta && (respuesta.ok || respuesta.type === "opaque")) await cache.put(peticion, respuesta);
    }))),
  ]));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys().then((nombres) => Promise.all(
    nombres.filter((nombre) => nombre.startsWith("sgft-") && ![PAGINAS, RECURSOS].includes(nombre))
      .map((nombre) => caches.delete(nombre)),
  )));
});

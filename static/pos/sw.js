// Service worker of the PWA (WBS 3.4.1, 3.4.2). Owners: Tarín + Yahir (static/pos/ is programmed in pairs).
// Served by pos:service_worker at /pos/sw.js with «Service-Worker-Allowed: /», and registered by pwa.js with scope
// «/», so the device activation (/accounts/) also happens inside the installed app (spike, finding 7).
//
// Only GET goes through here: every POST (sales, /pos/sync/) always goes to the network, and the offline queue
// lives in IndexedDB (db.js), never in this cache. Workbox comes by importScripts, without npm (CLAUDE.md §6).
importScripts("https://storage.googleapis.com/workbox-cdn/releases/7.3.0/workbox-sw.js");

// Bump VERSION when the list changes: activate deletes every cache of another version.
const VERSION = "v4";
const PAGINAS = "sgft-paginas-" + VERSION;
const RECURSOS = "sgft-recursos-" + VERSION;
const INICIO = "/pos/";
const PRECARGA = [
  "/static/core/css/app.css",
  "/static/core/fonts/outfit-400.woff2",
  "/static/core/fonts/outfit-500.woff2",
  "/static/core/fonts/outfit-600.woff2",
  "/static/core/fonts/outfit-700.woff2",
  "/static/pos/manifest.json",
  "/static/pos/pricing.js",
  "/static/pos/pwa.js",
  "/static/pos/db.js",
  "/static/pos/offline.js",
  "/static/pos/icons/icon-192.png",
  "/static/pos/icons/apple-touch-icon.png",
  "https://cdn.jsdelivr.net/npm/htmx.org@2.0.4/dist/htmx.min.js",
  "https://cdn.jsdelivr.net/npm/alpinejs@3.14.8/dist/cdn.min.js",
  "https://cdn.jsdelivr.net/npm/dexie@4.0.10/dist/dexie.min.js",
];
const CDN = ["https://cdn.jsdelivr.net", "https://storage.googleapis.com"];
// Screens that keep their last copy for working without network: Nueva venta sells from it; Productos, Inventario,
// Caja and Reportes are read-only with the data of the last load (CLAUDE.md §5-bis).
const MODULOS = ["/pos/", "/catalog/", "/inventory/", "/reports/"];

function esPantalla(url) {
  return url.origin === self.location.origin && MODULOS.some((prefijo) => url.pathname.startsWith(prefijo));
}

// Only real screens are kept: a 200 that did not come from a redirect. «Requiere PIN» is a 403, so a locked
// module never replaces the last unlocked copy. Safari refuses a page served by the worker that came from a
// redirect.
async function guardable(respuesta) {
  return respuesta && respuesta.status === 200 && !respuesta.redirected ? respuesta : null;
}

// A copy served without network says so, and since when: offline.js reads <meta name="sgft-copia"> to show
// «Sin conexión» and «Última sincronización», and to ask for the PIN in the padlock modules.
async function marcarCopia(respuesta) {
  if (!respuesta) return respuesta;
  const fecha = new Date(respuesta.headers.get("Date") || Date.now()).toISOString();
  const html = (await respuesta.text()).replace("<head>", `<head><meta name="sgft-copia" content="${fecha}">`);
  return new Response(html, { status: respuesta.status, statusText: respuesta.statusText, headers: respuesta.headers });
}

workbox.setConfig({ debug: false });
workbox.core.skipWaiting();
workbox.core.clientsClaim();

// Screens: network first; after 3 s or without network, the last copy. Nueva venta keeps working from that copy
// (offline it is the device that prices and queues, 3.4.4); the other screens are shown as they were last loaded.
// The key is the URL alone (ignoreVary): the server varies on Cookie and HX-Request, and a navigation never
// carries HX-Request.
workbox.routing.registerRoute(
  ({ request, url }) => request.mode === "navigate" && esPantalla(url),
  new workbox.strategies.NetworkFirst({
    cacheName: PAGINAS,
    networkTimeoutSeconds: 3,
    matchOptions: { ignoreVary: true },
    plugins: [{
      cacheWillUpdate: async ({ response }) => guardable(response),
      cachedResponseWillBeUsed: async ({ cachedResponse }) => marcarCopia(cachedResponse),
    }],
  }),
);

// A screen that was never opened with network has no copy: instead of the browser's error, say what to do.
workbox.routing.setCatchHandler(async ({ request }) => {
  if (request.mode !== "navigate") return Response.error();
  const html = `<!doctype html><html lang="es-MX"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Sin conexión · SGFT</title>
<link rel="stylesheet" href="/static/core/css/app.css"></head>
<body class="grid min-h-screen place-items-center bg-superficie-fondo p-md font-sans text-texto-primario">
<main class="flex max-w-[480px] flex-col gap-md rounded-xl border border-borde-sutil bg-superficie-tarjeta p-xl text-center shadow-tarjeta">
<h1 class="sgft-texto-titulo-h2">Sin conexión</h1>
<p class="sgft-texto-cuerpo-base text-texto-secundario">Esta pantalla todavía no está guardada en el dispositivo.
Ábrela una vez con conexión para poder consultarla sin red.</p>
<a class="sgft-btn sgft-btn--primario" href="${INICIO}">Ir a Nueva venta</a></main></body></html>`;
  return new Response(html, { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } });
});

// Warm both caches on install, so the first offline load works without visiting every URL. cache.add() rejects
// opaque responses (spike, finding 2), so every file goes through fetch + put. A file that fails does not stop
// the install: the strategies above fill it in on the next visit with network.
self.addEventListener("install", (event) => {
  event.waitUntil(Promise.all([
    caches.open(PAGINAS).then(async (cache) => {
      const respuesta = await fetch(new Request(INICIO, { credentials: "same-origin" })).catch(() => null);
      if (await guardable(respuesta)) await cache.put(INICIO, respuesta);
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

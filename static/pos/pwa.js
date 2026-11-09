// Registers the service worker of the PWA (WBS 3.4.1). Owners: Tarín + Yahir. Loaded by the pages of the point
// of sale (pos/order_builder.html). The service worker lives at /pos/sw.js and, with «Service-Worker-Allowed: /»,
// controls the whole site, so the installed app keeps its own session (spike, finding 7).
(function () {
  "use strict";
  if (!("serviceWorker" in navigator)) return;
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/pos/sw.js", { scope: "/" }).catch(function (error) {
      console.warn("No se pudo registrar el service worker:", error);
    });
  });
})();

// Nueva venta without network (WBS 3.4.4, 3.4.7, 3.5.1) and the sync triggers (3.4.3). Owners: Tarín + Yahir.
//
// With network, Nueva venta is the server's (HTMX) and this file only keeps the queue moving: it saves the data the
// page brings for working offline, syncs when the page loads, when the network comes back, every 10 s while something
// is pending and with «Sincronizar»
// (iOS has no Background Sync, spike finding 5), shows «N pendientes» and sends X-Pendientes so closing the till
// is refused while something is pending (rule 5).
//
// The other screens (Productos, Inventario, Caja, Reportes) are read-only without network: the service worker serves
// the copy of their last load marked with <meta name="sgft-copia">, and the Alpine component pantallaSinRed shows
// «Sin conexión · N pendientes · Última sincronización» and, in the padlock modules, asks for the Administrator's
// PIN checked on the device (DEC-28), which unlocks them for 30 minutes (DEC-32). A screen's copy is the one of its
// last visit with network. Nothing fetches pages in the background: every request re-saves the session
// (SESSION_SAVE_EVERY_REQUEST), so a background request would overwrite a ticket change made at the same time.
//
// Without network (the «offline» event or an HTMX request that cannot reach the server; navigator.onLine alone is
// not trusted, spike finding 4) the Alpine component ventaSinRed takes over in Nueva venta: the catalog of the last load, the
// ticket priced with calcularTotal (pricing.js, the only money computed in the browser), and «Confirmar compra»
// that queues a «venta» operation. Without an open session it offers «Abrir caja» with the PIN checked against
// the PBKDF2 verifier (DEC-28), and queues an «apertura_turno» in that Administrator's name.
(function () {
  "use strict";

  const almacen = window.sgftDb.crearAlmacen();
  const SYNC_URL = "/pos/sync/";
  let pendientes = 0;
  const DESBLOQUEO_MS = 30 * 60 * 1000;

  function avisar(nombre, detalle) {
    document.dispatchEvent(new CustomEvent(nombre, { detail: detalle }));
  }

  async function actualizarPendientes() {
    pendientes = await almacen.contar();
    document.querySelectorAll("[data-sgft-pendientes]").forEach((el) => { el.textContent = pendientes; });
    avisar("sgft:pendientes", pendientes);
    return pendientes;
  }

  let sincronizando = null;
  async function sincronizar() {
    if (sincronizando) return sincronizando;
    sincronizando = (async () => {
      try {
        if (!(await almacen.contar())) return { ok: true, resultados: [] };
        const resultado = await almacen.sincronizar(SYNC_URL);
        avisar("sgft:sincronizado", resultado);
        return resultado;
      } finally {
        await actualizarPendientes();
        sincronizando = null;
      }
    })();
    return sincronizando;
  }

  // iOS may not fire «online», or fires it before the connection works, and then that one attempt fails (spike
  // finding 4; T30, test 4 on the iPhone). While something is pending, retry every REINTENTO_MS and when the app
  // comes back to the foreground, so the queue leaves in under 30 s without touching anything (RNF-07). The reload
  // that brings the server's state waits while Nueva venta has a ticket in progress: it would lose its lines.
  const REINTENTO_MS = 10 * 1000;
  let modoSinRed = false;
  let ticketEnCurso = false;

  async function reintentar() {
    if (!pendientes || document.visibilityState !== "visible") return;
    const resultado = await sincronizar();
    if (!resultado.ok || ticketEnCurso) return;
    if (resultado.resultados.length || modoSinRed || copiaSinRed()) window.location.reload();
  }

  // With network again: send the queue and reload, so the screen shows the server's state (session, totals).
  async function alVolverLaRed() {
    const resultado = await sincronizar();
    if (resultado.ok) window.location.reload();
  }

  // ISO date of the copy when the service worker served this page without network; null when it came from the server.
  function copiaSinRed() {
    const meta = document.querySelector('meta[name="sgft-copia"]');
    return meta ? meta.content : null;
  }

  function leerDatos() {
    const nodo = document.getElementById("datos-sin-red");
    return nodo ? JSON.parse(nodo.textContent) : null;
  }

  async function arrancar() {
    if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {});
    const datos = leerDatos();
    if (datos) {
      // A page served from the cache without network carries old data: only newer data replaces what is saved.
      const guardados = await almacen.leer("datos");
      if (!guardados || datos.generado > guardados.generado) await almacen.guardarDatos(datos);
    }
    await actualizarPendientes();
    if (navigator.onLine && !copiaSinRed()) {
      const resultado = await sincronizar();
      if (resultado.ok && resultado.resultados.length) window.location.reload();
    }
  }

  // Closing the till asks the server; the server needs the device's pending count (rule 5).
  document.addEventListener("htmx:configRequest", (event) => {
    event.detail.headers["X-Pendientes"] = String(pendientes);
  });
  // An HTMX request that never reached the server: work offline.
  document.addEventListener("htmx:sendError", () => avisar("sgft:sin-red"));
  window.addEventListener("offline", () => avisar("sgft:sin-red"));
  window.addEventListener("online", alVolverLaRed);
  setInterval(reintentar, REINTENTO_MS);
  document.addEventListener("visibilitychange", reintentar);
  document.addEventListener("click", (event) => {
    const enlace = event.target.closest('a[href="#sincronizar"]');
    if (!enlace) return;
    event.preventDefault();
    sincronizar().then((resultado) => { if (resultado.ok && resultado.resultados.length) window.location.reload(); });
  });
  // A locked module in the menu opens the PIN dialog of the server; without network, go to its saved copy instead.
  document.addEventListener("click", (event) => {
    const boton = event.target.closest("button[data-sgft-url]");
    if (!boton || (navigator.onLine && !copiaSinRed())) return;
    event.preventDefault();
    event.stopPropagation();
    window.location.href = boton.dataset.sgftUrl;
  }, true);
  document.addEventListener("DOMContentLoaded", () => { arrancar(); });

  // --- Alpine component -------------------------------------------------------------------------------------

  // «$1,234.50» from integer cents. Formatting only: the amounts come from calcularTotal.
  function dinero(centavos) {
    const signo = centavos < 0 ? "-" : "";
    const abs = Math.abs(centavos);
    const enteros = String(Math.floor(abs / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return signo + "$" + enteros + "." + String(abs % 100).padStart(2, "0");
  }

  // «1,500.5» → 150050 without floating point; null if it is not an amount with up to 2 decimals.
  function centavosDeTexto(texto) {
    const limpio = String(texto).replace(/[$,\s]/g, "");
    const partes = /^(\d{1,7})(?:\.(\d{1,2}))?$/.exec(limpio);
    if (!partes) return null;
    return parseInt(partes[1], 10) * 100 + parseInt((partes[2] || "0").padEnd(2, "0"), 10);
  }

  function ventaSinRed() {
    return {
      sinRed: false,
      catalogo: { categorias: [], platillos: [] },
      usuario: null,
      turno: null,
      categoria: "todos",
      lineas: [],
      metodo: "efectivo",
      pendientes: 0,
      reactivar: false,
      mensaje: "",
      error: "",
      dialogo: "",
      personalizando: null,
      seleccion: [],
      fondo: "",
      guardando: false,

      async iniciar() {
        document.addEventListener("sgft:sin-red", () => this.entrar());
        document.addEventListener("sgft:pendientes", (e) => { this.pendientes = e.detail; });
        this.$watch("lineas", (lineas) => { ticketEnCurso = lineas.length > 0; });
        if (!navigator.onLine) await this.entrar();
      },

      async entrar() {
        if (this.sinRed) return;
        const datos = await almacen.leer("datos");
        if (!datos) {
          this.error = "Este dispositivo todavía no tiene el menú guardado. Conéctate una vez para descargarlo.";
        } else {
          this.catalogo = datos.catalogo;
          this.usuario = datos.usuario;
        }
        this.turno = await almacen.leer("turno");
        this.reactivar = Boolean(await almacen.leer("reactivar"));
        this.pendientes = await almacen.contar();
        this.sinRed = true;
        modoSinRed = true;
      },

      platillo(id) {
        return this.catalogo.platillos.find((p) => p.id === id);
      },

      get platillosVisibles() {
        return this.catalogo.platillos.filter((p) => this.categoria === "todos" ||
          String(p.categoria_id) === this.categoria);
      },

      cantidadEnTicket(id) {
        return this.lineas.filter((l) => l.platillo_id === id).reduce((suma, l) => suma + l.cantidad, 0);
      },

      // A line of the order in the shape of calcularTotal and the contract (DEC-01).
      lineaPedido(linea) {
        const p = this.platillo(linea.platillo_id);
        return {
          platillo_id: p.id, precio_base_centavos: p.precio_centavos, cantidad: linea.cantidad,
          modificadores: linea.modificadores.map((id) => p.modificadores.find((m) => m.id === id))
            .map((m) => ({ tipo: m.tipo, insumo_id: m.insumo_id, ajuste_centavos: m.ajuste_centavos })),
        };
      },

      get pedido() {
        return { lineas: this.lineas.map((l) => this.lineaPedido(l)) };
      },

      get lineasVista() {
        return this.lineas.map((l) => {
          const p = this.platillo(l.platillo_id);
          return { ...l, nombre: p.nombre, emoji: p.emoji, personalizable: p.modificadores.length > 0,
            etiquetas: l.modificadores.map((id) => p.modificadores.find((m) => m.id === id).nombre).join(" · "),
            subtotal: dinero(window.calcularTotal({ lineas: [this.lineaPedido(l)] })) };
        });
      },

      get totalCentavos() {
        return window.calcularTotal(this.pedido);
      },

      get total() {
        return dinero(this.totalCentavos);
      },

      get articulos() {
        return this.lineas.reduce((suma, l) => suma + l.cantidad, 0);
      },

      dinero,

      unir(platilloId, modificadores, cantidad) {
        const clave = [...modificadores].sort((a, b) => a - b);
        const igual = this.lineas.find((l) => l.platillo_id === platilloId &&
          JSON.stringify(l.modificadores) === JSON.stringify(clave));
        if (igual) igual.cantidad += cantidad;
        else this.lineas.push({ clave: crypto.randomUUID(), platillo_id: platilloId, cantidad, modificadores: clave });
      },

      agregar(platillo) {
        this.mensaje = "";
        this.unir(platillo.id, [], 1);
      },

      quitar(linea) {
        const real = this.lineas.find((l) => l.clave === linea.clave);
        real.cantidad -= 1;
        if (real.cantidad <= 0) this.lineas = this.lineas.filter((l) => l !== real);
      },

      personalizar(linea) {
        this.personalizando = this.lineas.find((l) => l.clave === linea.clave);
        this.seleccion = [...this.personalizando.modificadores];
        this.dialogo = "personalizar";
      },

      get opcionesPersonalizar() {
        return this.personalizando ? this.platillo(this.personalizando.platillo_id).modificadores : [];
      },

      guardarPersonalizacion() {
        const linea = this.personalizando;
        this.lineas = this.lineas.filter((l) => l !== linea);
        this.unir(linea.platillo_id, this.seleccion.map(Number), linea.cantidad);
        this.cerrarDialogo();
      },

      cerrarDialogo() {
        this.dialogo = "";
        this.personalizando = null;
        this.error = "";
      },

      async cobrar() {
        if (!this.lineas.length || !this.turno || this.guardando) return;
        this.guardando = true;
        try {
          const pedido = this.pedido;
          await almacen.encolar({ tipo: "venta", usuario_id: this.usuario.id, turno_uuid: this.turno.uuid,
            metodo_pago: this.metodo, pedido, total_cobrado_centavos: window.calcularTotal(pedido) });
          this.lineas = [];
          this.mensaje = "Venta guardada en el dispositivo. Se enviará al volver la red.";
          await actualizarPendientes();
        } catch (error) {
          this.error = "No se pudo guardar la venta en el dispositivo. Intenta de nuevo.";
        } finally {
          this.guardando = false;
        }
      },

      async abrirCaja(evento) {
        this.error = "";
        const formulario = new FormData(evento.target);
        const pin = formulario.getAll("pin").join("");
        const centavos = centavosDeTexto(this.fondo);
        if (!/^\d{6}$/.test(pin)) { this.error = "Escribe los 6 dígitos del PIN."; return; }
        if (centavos === null) { this.error = "Escribe el fondo inicial, por ejemplo 500.00."; return; }
        const admin = await almacen.verificarPin(pin);
        if (!admin) {
          this.error = "PIN incorrecto, o el dispositivo no se ha sincronizado en 7 días. Conéctate para renovarlo.";
          return;
        }
        const operacion = await almacen.encolar({ tipo: "apertura_turno", usuario_id: admin.usuario_id,
          efectivo_inicial_centavos: centavos });
        this.turno = { uuid: operacion.uuid, fecha: operacion.marca_tiempo_dispositivo.slice(0, 10), sin_red: true };
        await almacen.guardar("turno", this.turno);
        await actualizarPendientes();
        this.mensaje = "Caja abierta en el dispositivo a nombre de " + admin.nombre + ".";
        this.fondo = "";
        this.cerrarDialogo();
      },
    };
  }

  // Productos, Inventario, Caja and Reportes without network: what they showed at their last load, read-only.
  function pantallaSinRed() {
    return {
      sinRed: false,
      copia: null,
      pendientes: 0,
      candado: false,
      bloqueada: false,
      nombre: "",
      aviso: "",
      error: "",

      async iniciar() {
        this.candado = document.body.hasAttribute("data-sgft-candado");
        this.copia = copiaSinRed();
        document.addEventListener("sgft:pendientes", (e) => { this.pendientes = e.detail; });
        document.addEventListener("sgft:sin-red", () => this.entrar(
          "Sin conexión: esta acción necesita red. Lo que ves es de la última sincronización."));
        if (this.copia) await this.entrar("");
      },

      async entrar(aviso) {
        this.sinRed = true;
        modoSinRed = true;
        this.aviso = aviso;
        this.pendientes = await almacen.contar();
        if (!this.copia) this.copia = await almacen.leer("ultima_sincronizacion");
        if (this.candado && copiaSinRed()) await this.revisarCandado();
      },

      get ultima() {
        return this.copia ? new Date(this.copia).toLocaleString("es-MX", { dateStyle: "short", timeStyle: "short" })
          : "sin datos";
      },

      async revisarCandado() {
        const desbloqueo = await almacen.leer("desbloqueo_sin_red");
        this.bloqueada = !(desbloqueo && desbloqueo.hasta > Date.now());
        this.nombre = this.bloqueada ? "" : desbloqueo.nombre;
      },

      async desbloquear(evento) {
        this.error = "";
        const pin = new FormData(evento.target).getAll("pin").join("");
        if (!/^\d{6}$/.test(pin)) { this.error = "Escribe los 6 dígitos del PIN."; return; }
        const admin = await almacen.verificarPin(pin);
        if (!admin) {
          this.error = "PIN incorrecto, o el dispositivo no se ha sincronizado en 7 días. Conéctate para renovarlo.";
          evento.target.reset();
          return;
        }
        await almacen.guardar("desbloqueo_sin_red",
          { hasta: Date.now() + DESBLOQUEO_MS, usuario_id: admin.usuario_id, nombre: admin.nombre });
        this.nombre = admin.nombre;
        this.bloqueada = false;
      },
    };
  }

  document.addEventListener("alpine:init", () => {
    window.Alpine.data("ventaSinRed", ventaSinRed);
    window.Alpine.data("pantallaSinRed", pantallaSinRed);
  });
  window.sgftSinRed = { sincronizar, centavosDeTexto, dinero };
})();

// Offline queue, data for working without network and the sync client of contract v1 (WBS 3.4.2, 3.4.3, 3.4.7).
// Owners: Tarín + Yahir (static/pos/ is programmed in pairs). Spanish keys by the approved exception (DEC-01, DEC-04):
// each operation is stored exactly as POST /pos/sync/ receives it (contrato-sync-pdv.md §2).
//
// Tables (IndexedDB through Dexie):
//   operaciones   the queue: one row per offline operation (apertura_turno, venta), keyed by its UUID
//   estado        key/value: datos (catalog, user and cash session of the last load with network),
//                 turno (the session the device uses offline), ultima_sincronizacion, reactivar
//   verificadores one row per active Administrator: PBKDF2 verifier of the PIN, never the PIN (DEC-28)
//
// derivarVerificador and pinValido do not use Dexie, so Node can test them (tests_e2e/parity/).
(function (global) {
  "use strict";

  const LOTE_MAXIMO = 100; // contract v1 §2
  const CADUCIDAD_VERIFICADOR_MS = 7 * 24 * 60 * 60 * 1000; // DEC-28 §5: 7 days without renewing

  function base64ABytes(texto) {
    const binario = atob(texto);
    const bytes = new Uint8Array(binario.length);
    for (let i = 0; i < binario.length; i++) bytes[i] = binario.charCodeAt(i);
    return bytes;
  }

  function bytesABase64(bytes) {
    let binario = "";
    for (const byte of new Uint8Array(bytes)) binario += String.fromCharCode(byte);
    return btoa(binario);
  }

  // PBKDF2-SHA256(PIN, sal, iteraciones) in base64, as accounts.User.set_password stores it.
  async function derivarVerificador(pin, salBase64, iteraciones) {
    const subtle = global.crypto.subtle;
    const clave = await subtle.importKey("raw", new TextEncoder().encode(pin), "PBKDF2", false, ["deriveBits"]);
    const bits = await subtle.deriveBits(
      { name: "PBKDF2", hash: "SHA-256", salt: base64ABytes(salBase64), iterations: iteraciones }, clave, 256);
    return bytesABase64(bits);
  }

  // The Administrator whose PIN this is, or null. Verifiers older than 7 days are not accepted (DEC-28 §5).
  async function pinValido(pin, verificadores, ahora = Date.now()) {
    if (!/^\d{6}$/.test(pin)) return null;
    for (const v of verificadores) {
      if (ahora - Date.parse(v.descargado) > CADUCIDAD_VERIFICADOR_MS) continue;
      if (await derivarVerificador(pin, v.sal, v.iteraciones) === v.verificador) return v;
    }
    return null;
  }

  function copia(valor) {
    return valor === undefined ? null : JSON.parse(JSON.stringify(valor));
  }

  function leerCookie(nombre) {
    const fila = document.cookie.split("; ").find((c) => c.startsWith(nombre + "="));
    return fila ? decodeURIComponent(fila.slice(nombre.length + 1)) : "";
  }

  function crearAlmacen() {
    const db = new global.Dexie("sgft");
    db.version(1).stores({
      operaciones: "uuid, tipo, marca_tiempo_dispositivo",
      estado: "clave",
      verificadores: "usuario_id",
    });

    const almacen = {
      db,

      async leer(clave) {
        const fila = await db.estado.get(clave);
        return fila ? fila.valor : null;
      },

      // Plain copies: IndexedDB cannot clone Alpine's reactive proxies.
      guardar(clave, valor) {
        return db.estado.put({ clave, valor: copia(valor) });
      },

      // What the page with network brought (pos:order_builder, «datos-sin-red»). Verifiers are replaced as a
      // whole: an Administrator who changed the PIN or was deactivated stops being accepted (DEC-28 §5).
      async guardarDatos(datos) {
        const descargado = datos.generado;
        await db.transaction("rw", db.estado, db.verificadores, async () => {
          await db.estado.put({ clave: "datos", valor: { catalogo: datos.catalogo, usuario: datos.usuario,
            generado: datos.generado } });
          await db.verificadores.clear();
          await db.verificadores.bulkPut(datos.verificadores.map((v) => ({ ...v, descargado })));
          // The server's cash state wins over the device's: offline only an opening made on the device is kept.
          const turno = await almacen.leer("turno");
          if (datos.turno || !turno || !turno.sin_red) {
            await db.estado.put({ clave: "turno", valor: datos.turno });
          }
        });
      },

      async verificarPin(pin) {
        return pinValido(pin, await db.verificadores.toArray());
      },

      // Writes the operation and only then resolves: never clear the ticket before this ends (spike, finding 3).
      async encolar(operacion) {
        const completa = copia({ uuid: global.crypto.randomUUID(), marca_tiempo_dispositivo: new Date().toISOString(),
          ...operacion });
        await db.operaciones.add(completa);
        return completa;
      },

      pendientes() {
        return db.operaciones.orderBy("marca_tiempo_dispositivo").toArray();
      },

      contar() {
        return db.operaciones.count();
      },

      // Sends the queue in chunks of 100 and deletes every UUID that comes back in resultados, whatever its
      // estado (contract §4). On 401, any other error or no network the queue stays whole. 401 also leaves
      // «reactivar» on, so the screen asks to activate the device again (DEC-34).
      async sincronizar(url) {
        const pendientes = await almacen.pendientes();
        const resultados = [];
        for (let i = 0; i < pendientes.length; i += LOTE_MAXIMO) {
          let respuesta;
          try {
            respuesta = await fetch(url, {
              method: "POST",
              credentials: "same-origin",
              headers: { "Content-Type": "application/json", "X-CSRFToken": leerCookie("csrftoken") },
              body: JSON.stringify({ version_contrato: 1, operaciones: pendientes.slice(i, i + LOTE_MAXIMO) }),
            });
          } catch (error) {
            return { ok: false, motivo: "sin_red", resultados };
          }
          if (respuesta.status === 401) {
            await almacen.guardar("reactivar", true);
            return { ok: false, motivo: "sin_sesion", resultados };
          }
          if (!respuesta.ok) return { ok: false, motivo: "http_" + respuesta.status, resultados };
          const cuerpo = await respuesta.json();
          await db.operaciones.bulkDelete(cuerpo.resultados.map((r) => r.uuid));
          resultados.push(...cuerpo.resultados);
        }
        await almacen.guardar("reactivar", false);
        await almacen.guardar("ultima_sincronizacion", new Date().toISOString());
        return { ok: true, resultados };
      },
    };
    return almacen;
  }

  const api = { derivarVerificador, pinValido, crearAlmacen, LOTE_MAXIMO, CADUCIDAD_VERIFICADOR_MS };
  global.sgftDb = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);

// Price of an order in integer cents (WBS 3.3.4, 3.4.5). Owners: Tarín + Jesús. Mirror of
// apps/pos/services_pricing.py calcular_total(): both must agree on every case of tests_fixtures/pricing_cases.json
// (node --test tests_e2e/parity/). The only money computed in the browser, and only without network: the server
// recalculates when it syncs. Spanish keys by the approved exception (DEC-01).
//
// A line costs (precio_base_centavos + the ajuste_centavos of every "agregar" modifier) × cantidad. A "quitar"
// modifier never changes the price.
(function (global) {
  "use strict";

  const TIPOS_MODIFICADOR = ["agregar", "quitar"];

  function entero(valor, campo, minimo) {
    if (typeof valor !== "number" || !Number.isInteger(valor) || valor < minimo) {
      throw new Error(campo + " debe ser un entero mayor o igual a " + minimo + ".");
    }
    return valor;
  }

  function esObjeto(valor) {
    return valor !== null && typeof valor === "object" && !Array.isArray(valor);
  }

  function calcularTotal(pedido) {
    if (!esObjeto(pedido) || !Array.isArray(pedido.lineas)) {
      throw new Error("El pedido debe traer una lista de líneas.");
    }
    let total = 0;
    for (const linea of pedido.lineas) {
      if (!esObjeto(linea)) throw new Error("Cada línea debe ser un objeto.");
      const base = entero(linea.precio_base_centavos, "precio_base_centavos", 0);
      const cantidad = entero(linea.cantidad, "cantidad", 1);
      const modificadores = linea.modificadores === undefined ? [] : linea.modificadores;
      if (!Array.isArray(modificadores)) throw new Error("modificadores debe ser una lista.");
      let extras = 0;
      for (const modificador of modificadores) {
        if (!esObjeto(modificador) || !TIPOS_MODIFICADOR.includes(modificador.tipo)) {
          throw new Error('Cada modificador debe ser de tipo "agregar" o "quitar".');
        }
        const ajuste = entero(modificador.ajuste_centavos === undefined ? 0 : modificador.ajuste_centavos,
          "ajuste_centavos", 0);
        if (modificador.tipo === "agregar") extras += ajuste;
      }
      total += (base + extras) * cantidad;
    }
    return total;
  }

  global.calcularTotal = calcularTotal;
  if (typeof module !== "undefined" && module.exports) module.exports = { calcularTotal };
})(typeof window !== "undefined" ? window : globalThis);

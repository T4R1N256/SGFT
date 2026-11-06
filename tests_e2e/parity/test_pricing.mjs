// Price parity (WBS 3.4.5): calcularTotal() of static/pos/pricing.js must give, for every case of
// tests_fixtures/pricing_cases.json, the same total as calcular_total() in Python (PricingParityTest).
// Run: node --test tests_e2e/parity/
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { calcularTotal } = require("../../static/pos/pricing.js");
const { casos, invalidos } = JSON.parse(
  readFileSync(new URL("../../tests_fixtures/pricing_cases.json", import.meta.url), "utf8"),
);

for (const caso of casos) {
  test(caso.nombre, () => {
    assert.equal(calcularTotal(caso.pedido), caso.total_esperado_centavos);
  });
}

for (const caso of invalidos) {
  test("rechaza: " + caso.nombre, () => {
    assert.throws(() => calcularTotal(caso.pedido));
  });
}

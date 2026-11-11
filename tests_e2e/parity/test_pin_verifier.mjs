// Offline PIN verifier parity (WBS 3.4.3, DEC-28): derivarVerificador() of static/pos/db.js must give the same
// PBKDF2-SHA256 as accounts.User.set_password, which stores base64(pbkdf2_hmac("sha256", pin, salt, iterations)).
// The vector was computed with Python's hashlib and few iterations, so the test is fast.
// Run: node --test "tests_e2e/parity/*.mjs"
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { derivarVerificador, pinValido } = require("../../static/pos/db.js");

const SAL = "c2dmdC1zYWwtMTZieXRlcw=="; // b"sgft-sal-16bytes"
const VERIFICADOR = "7M0mJvCdF3I0x4FjArAffrP0sCGfxOhW3MpBLzPVlP4="; // PIN 482913, 1000 iterations
const ahora = Date.parse("2026-11-08T12:00:00Z");
const admin = { usuario_id: 3, nombre: "Alejandro", sal: SAL, iteraciones: 1000, verificador: VERIFICADOR,
  descargado: "2026-11-07T12:00:00Z" };

test("deriva el mismo verificador que Python", async () => {
  assert.equal(await derivarVerificador("482913", SAL, 1000), VERIFICADOR);
});

test("el PIN correcto devuelve al Administrador", async () => {
  assert.equal((await pinValido("482913", [admin], ahora)).usuario_id, 3);
});

test("un PIN incorrecto o incompleto no abre", async () => {
  assert.equal(await pinValido("482914", [admin], ahora), null);
  assert.equal(await pinValido("48291", [admin], ahora), null);
});

test("un verificador de más de 7 días ya no se acepta", async () => {
  const viejo = { ...admin, descargado: "2026-10-31T11:59:59Z" };
  assert.equal(await pinValido("482913", [viejo], ahora), null);
});

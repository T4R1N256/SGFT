# Contrato del endpoint `POST /pos/sync/` — versión 1

**Estado:** aprobado el 24 de septiembre de 2026. Cierra la acción 5 de `ADR-02-operacion-offline-SGFT.md`.
**Dueños:** Jesús Hernández (servidor, `sync_operations()` en pareja con Jared Beltrán) · Alejandro Tarín (cliente, `static/pos/db.js` en pareja con Yahir Enríquez).
**Paquetes WBS:** 3.4.3, 3.4.6, 3.4.7, 3.4.9.
**Relacionado con:** ADR-02 §4 y §7, `CLAUDE.md` §5 (reglas 1, 7, 8, 9, 10, 12), `nombres-modulo-precios.md` (DEC-01).

## 1. Decisiones que fija este contrato

| ID | Decisión | Razón |
|---|---|---|
| DEC-02 | Si el total recalculado por el servidor con el catálogo vigente no coincide con el total cobrado en el dispositivo, **se registra lo cobrado** como importe oficial de la venta, se guarda también el total del servidor y la venta se **marca para revisión** del Administrador. No va a cuarentena. | La venta es inmutable desde el cobro (regla 7) y lo cobrado es el dinero que está en caja; registrar otro importe descuadraría el corte de caja. |
| DEC-03 | El lote es **un solo arreglo** `operaciones`, con campo `tipo` (`"apertura_turno"` o `"venta"`). | Una sola cola lógica en el cliente y una sola respuesta indexada por UUID. |
| DEC-04 | Las llaves del lote van **en español**, las mismas del módulo de precios. | `db.js` guarda y envía el pedido tal como lo recibe `calcularTotal()`, sin capa de traducción. Excepción acotada a `CLAUDE.md` §9 (ver DEC-01). |
| DEC-05 | **Cualquier usuario con sesión activa** puede sincronizar la cola. El servidor revalida, por cada operación, el rol del usuario que la registró. Sin sesión, responde 401 y el dispositivo conserva la cola. | Un solo dispositivo compartido por Cajero y Administrador; exigir el mismo usuario bloquearía la cola en cada cambio de turno. |
| DEC-06 | El lote procesado responde **HTTP 200 con un estado por UUID**. Solo los errores que impiden procesar el lote completo usan otro código. | El cliente decide qué borrar de su cola leyendo cada UUID; un 207 no le agrega información. |

## 2. Petición

```
POST /pos/sync/
Content-Type: application/json
X-CSRFToken: <valor de la cookie csrftoken>
```

`db.js` usa `fetch`, que no hereda el `hx-headers` de `base.html`: debe leer la cookie `csrftoken` y enviar el encabezado él mismo. La sesión de Django viaja en la cookie de sesión, como en cualquier otra petición.

```json
{
  "version_contrato": 1,
  "operaciones": [
    {
      "uuid": "6f1c2a0e-3b7d-4c55-9a51-0d2b8e7f4a10",
      "tipo": "apertura_turno",
      "marca_tiempo_dispositivo": "2026-09-24T08:02:11-06:00",
      "usuario_id": 3,
      "efectivo_inicial_centavos": 50000
    },
    {
      "uuid": "b0a9d6e2-7c1f-4e3a-8f2d-5c6b7a8e9f01",
      "tipo": "venta",
      "marca_tiempo_dispositivo": "2026-09-24T09:15:40-06:00",
      "usuario_id": 3,
      "turno_uuid": "6f1c2a0e-3b7d-4c55-9a51-0d2b8e7f4a10",
      "metodo_pago": "efectivo",
      "pedido": {
        "lineas": [
          {
            "platillo_id": 1,
            "precio_base_centavos": 8500,
            "cantidad": 2,
            "modificadores": [
              { "tipo": "agregar", "insumo_id": 7, "ajuste_centavos": 1500 }
            ]
          }
        ]
      },
      "total_cobrado_centavos": 20000
    }
  ]
}
```

### Campos

| Campo | Aplica a | Tipo | Regla |
|---|---|---|---|
| `version_contrato` | lote | entero | Hoy `1`. Una versión que el servidor no conoce se rechaza completa (400). |
| `operaciones` | lote | arreglo | Máximo 100 elementos por petición; si la cola es mayor, el cliente la envía en tramos. |
| `uuid` | ambas | texto (UUID v4) | Generado con `crypto.randomUUID()` al confirmar la operación. Único en todo el sistema (regla 8). |
| `tipo` | ambas | texto | `"apertura_turno"` o `"venta"`. |
| `marca_tiempo_dispositivo` | ambas | texto ISO 8601 con zona horaria | Primera de las dos marcas de tiempo (regla 7); la del servidor la pone el servidor. |
| `usuario_id` | ambas | entero | Usuario que registró la operación en el dispositivo, no el que sincroniza. |
| `efectivo_inicial_centavos` | apertura | entero ≥ 0 | Efectivo inicial declarado. |
| `turno_uuid` | venta | texto (UUID) | UUID del turno al que pertenece la venta. Si el turno se abrió en línea, es el UUID que el servidor asignó y el dispositivo tiene en caché. |
| `metodo_pago` | venta | texto | `"efectivo"` o `"transferencia"` (regla 4). |
| `pedido` | venta | objeto | Misma estructura que recibe `calcular_total()` / `calcularTotal()` y que usa `tests_fixtures/pricing_cases.json`. |
| `modificadores[].tipo` | venta | texto | `"agregar"` o `"quitar"`. |
| `modificadores[].insumo_id` | venta | entero | Insumo que se agrega o se quita; el servidor lo usa para ajustar el descuento de inventario (regla 2). El cálculo de precio lo ignora. La cantidad de insumo de un extra la toma el servidor de la definición del modificador (se fija en 3.3.3). |
| `total_cobrado_centavos` | venta | entero | Lo que se cobró en el dispositivo. |

Todo importe viaja en **enteros de centavos**; el servidor lo convierte a `Decimal` al guardarlo (`CLAUDE.md` §9).

## 3. Procesamiento en el servidor

1. **Validación del lote.** Sin sesión → 401. Token CSRF inválido → 403 (comportamiento estándar de Django). JSON mal formado, falta `operaciones` o versión desconocida → 400. Más de 100 operaciones → 413. En estos casos **no se procesa ninguna operación**.
2. **Orden.** Primero todas las operaciones `apertura_turno`, luego las `venta`, cada grupo en orden ascendente de `marca_tiempo_dispositivo`. Así cada venta encuentra su turno ya creado.
3. **Una transacción por operación.** Cada operación se aplica en su propia `transaction.atomic()` (ADR-02 §7). Un fallo en una no revierte las demás.
4. **Idempotencia.** Si el `uuid` ya existe en `Sale`, `CashRegisterSession`, `QuarantinedSale` o `QuarantinedCashSession`, el resultado es `duplicada` y no se toca nada. La garantía es una restricción de unicidad en base de datos, no una consulta previa (regla 8).
5. **Autorización por operación.** El `usuario_id` debe existir, estar activo y tener un rol que permita la operación (Cajero o Administrador). Si no, la operación va a cuarentena con motivo `usuario_sin_permiso`: la venta ya ocurrió y no se rechaza (regla 9).
6. **Apertura de turno.** Si ya existe un turno abierto para la jornada, va a cuarentena con motivo `turno_ya_abierto` (regla 13, caso previsto en la descomposición SADT de A6).
7. **Venta.** En este orden:
   - `turno_uuid` inexistente o turno cerrado → cuarentena `turno_invalido`.
   - Un `platillo_id` o `insumo_id` que ya no existe → cuarentena `platillo_desconocido`.
   - Un platillo sin receta → cuarentena `receta_faltante` (el Administrador puede aplicarla sin descontar inventario).
   - `calcular_total(pedido)` con los precios **enviados** debe dar `total_cobrado_centavos`; si no, cuarentena `total_inconsistente` (el pedido no corresponde a su propio total: error de paridad o dato alterado).
   - Si todo lo anterior pasa: se crea la `Sale` con el total cobrado, se llama a `inventory.services.deduct_for_sale()` y se registra la marca de tiempo del servidor.
   - Se recalcula el total con los precios **vigentes** del catálogo. Si difiere del cobrado → la venta queda aplicada y marcada para revisión con motivo `precio_distinto` (DEC-02).
   - Si algún insumo quedó en existencia negativa → aplicada y marcada con motivo `existencia_negativa` (regla 10).

**Campos que esto exige en `Sale`** (paquete 3.4.6; los nombres finales los fija Jesús en la migración, en inglés como el resto de los modelos): total cobrado, total recalculado por el servidor, indicador de diferencia de precio, marca de tiempo del dispositivo, marca de tiempo del servidor y UUID con restricción de unicidad.

## 4. Respuesta

Cuando el lote se pudo procesar, siempre **HTTP 200**:

```json
{
  "version_contrato": 1,
  "resultados": [
    { "uuid": "6f1c2a0e-3b7d-4c55-9a51-0d2b8e7f4a10", "estado": "aplicada" },
    { "uuid": "b0a9d6e2-7c1f-4e3a-8f2d-5c6b7a8e9f01", "estado": "aplicada_con_revision", "motivos": ["precio_distinto"] }
  ]
}
```

| `estado` | Significado | ¿El cliente la borra de su cola? |
|---|---|---|
| `aplicada` | Registrada normalmente. | Sí |
| `aplicada_con_revision` | Registrada, con uno o más `motivos`: `precio_distinto`, `existencia_negativa`. Aparece en la bandeja del Administrador (3.4.9). | Sí |
| `duplicada` | El servidor ya la tenía (reintento). | Sí |
| `cuarentena` | Guardada en `QuarantinedSale` / `QuarantinedCashSession` con un `motivo`: `usuario_sin_permiso`, `turno_ya_abierto`, `turno_invalido`, `platillo_desconocido`, `receta_faltante`, `total_inconsistente`. La resuelve el Administrador en la bandeja (3.4.9). | Sí |

**Regla del cliente:** borra de su cola **todo UUID que aparezca en `resultados`**, cualquiera que sea su estado, porque en los cuatro casos el servidor ya tiene la operación. Conserva la cola completa ante 401, 403, 400, 413, errores 5xx o falta de red, y reintenta después. El reintento es seguro gracias a la idempotencia.

**Ante 401:** la interfaz pide iniciar sesión y reintenta. La cola no se toca.

## 5. Lo que este contrato no cubre

La descarga del catálogo, las recetas y el estado del turno hacia el dispositivo, y el indicador de "última sincronización" (ADR-02 §4) son otro flujo, de lectura. Se documentan aparte si su forma deja de ser obvia al implementar 3.4.3.

## 6. Pruebas mínimas que se derivan

Cada una va en `apps/pos/tests.py` (autor: Jesús; dueño del archivo: Jared):

- el mismo lote enviado dos veces produce una sola venta y un solo descuento;
- una apertura y sus ventas en el mismo lote, en desorden, se aplican en el orden correcto;
- sin sesión → 401 y ninguna operación aplicada;
- cada motivo de cuarentena y cada motivo de revisión tiene al menos un caso;
- un fallo en una operación no revierte las demás del lote.

## 7. Cambios al contrato

Cualquier cambio de forma sube `version_contrato` y se aprueba por Jesús, Jared y Tarín en el mismo PR que modifica `db.js` y `sync_operations()`.

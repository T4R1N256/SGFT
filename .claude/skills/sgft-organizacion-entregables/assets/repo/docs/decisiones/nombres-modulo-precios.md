# DEC-01 — Nombres en español en el módulo de precios y en el lote de sincronización

**Fecha:** 24 de septiembre de 2026 · **Estado:** aprobada · **Dueños:** Jesús Hernández y Alejandro Tarín · **WBS:** 3.3.4, 3.4.4, 3.4.5, 3.4.6

## Contexto

La misma función aparecía con tres nombres en la documentación: `calcular_total` (WBS 3.3.4 y `revision-tecnica-offline-SGFT.md`), `calculate_total()` dentro de `services.py` (`estructura-y-flujo-datos-SGFT.md` §1) y `calcularTotal` en JavaScript. El fixture de paridad ya estaba escrito con llaves en español. `CLAUDE.md` §9 pide identificadores en inglés.

## Decisión

El módulo de precios y el lote de sincronización usan nombres en español:

| Elemento | Nombre |
|---|---|
| Función Python | `calcular_total(pedido) -> int` en `apps/pos/services_pricing.py` |
| Función JavaScript | `calcularTotal(pedido)` en `static/pos/pricing.js` |
| Llaves del fixture y del pedido | `nombre`, `pedido`, `lineas`, `platillo_id`, `precio_base_centavos`, `cantidad`, `modificadores`, `tipo` (`"agregar"` / `"quitar"`), `insumo_id`, `ajuste_centavos`, `total_esperado_centavos` |
| Llaves del lote de sincronización | las de `contrato-sync-pdv.md` (DEC-04) |

**Alcance de la excepción.** Solo aplica a esos tres artefactos. Modelos, campos de base de datos, vistas, URLs, servicios y el resto del código siguen en inglés conforme a `CLAUDE.md` §9. Por ejemplo, el servicio se llama `confirm_sale()` y el modelo `Sale`, aunque reciban un `pedido` con llaves en español.

## Alternativas consideradas

- **Todo en inglés** (`calculate_total`, `base_price_cents`): coherente con `CLAUDE.md` §9, pero obligaba a reescribir el fixture y el código de referencia ya revisados.
- **Español** (elegida): conserva el código de referencia de la revisión técnica tal como está y evita una capa de traducción entre la cola local y el servidor.

## Consecuencias y correcciones documentales

1. `CLAUDE.md` §9: agregar la excepción debajo del glosario.
2. `CLAUDE.md` §8: dice `pricing.py`; el archivo es `apps/pos/services_pricing.py`.
3. `estructura-y-flujo-datos-SGFT.md` §1: quitar `calculate_total()` de `services.py`. El cálculo vive solo en `services_pricing.calcular_total()`, y `confirm_sale()` lo llama.
4. `revision-tecnica-offline-SGFT.md` §4: la ruta y el import dicen `apps/pdv/services/pricing.py` / `apps.pdv.services.pricing`; deben ser `apps/pos/services_pricing.py` / `apps.pos.services_pricing` (la app se renombró de `pdv` a `pos` en DEC-17).

Las cuatro correcciones le corresponden a Diego.

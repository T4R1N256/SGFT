# Rutas (URLs) pendientes para conectar las vistas

**Fecha:** 3 de octubre de 2026 · **Estado:** abierto · **Lo prepara:** Alejandro Tarín · **Para:** Jesús, Jared, Diego y Yahir

## Por qué existe

Las vistas de la interfaz ya se escriben con su contrato vista–plantilla (Fase 4 de `traducir-prototipos-figma-SGFT.md`). Cada vista resuelve sus URLs **por nombre** con `reverse()`, por ejemplo `pos:add_item`, y se las pasa a la plantilla. Mientras la ruta no exista en `urls.py`, la vista pinta `#` y la pantalla se ve, pero sus botones no llaman al servidor.

Para conectar todo falta registrar las rutas. Este documento dice cuáles, con qué nombre y quién las registra.

## 1. Decisión pendiente: ¿de quién es `urls.py`?

DEC-31 asignó `views.py`, `urls.py` y las plantillas al frontend. Tarín pidió revisar si `urls.py` debe ser del **backend**, porque define la superficie de peticiones (rutas que también usan el cliente sin red y las pruebas). Mientras se decide, **nadie del frontend edita `urls.py`**.

| Opción | `urls.py` de `pos` y `reports` | `urls.py` de `catalog`, `inventory` y `accounts` |
|---|---|---|
| A. Backend (propuesta de Tarín) | Jared | Diego |
| B. Frontend (DEC-31 tal como está) | Tarín (`pos`, `catalog`) · Yahir (`inventory`, `reports`, `accounts`) | ídem |

Al decidir, Tarín actualiza `assets/ownership.json` y regenera `CODEOWNERS`.

## 2. Pendientes de Jesús (`config/`, `apps/core/`)

| # | Pendiente | Archivo | Por qué |
|---|---|---|---|
| J1 | Incluir las rutas de `catalog`: `path("catalog/", include("apps.catalog.urls"))` | `config/urls.py` | Productos (DEC-25) no tiene ruta; `catalog/urls.py` todavía no existe. |
| J2 | Procesador de contexto con lo que piden el menú y la barra superior: `nav_modules`, `active_module`, `cash_session_open`, `session_total`, `sync_pending`, `user_initials`, `logout_url`, `search_placeholder`, `search_url`, `search_target` | `apps/core/context_processors.py` y su registro en `config/settings.py` | Hoy cada vista lo arma con `_shell_context()` como borrador. La lista completa está al inicio de `apps/core/templates/base.html`. |
| J3 | Mixin o decorador de rol y de PIN de Administrador | `apps/core/mixins.py` | Las vistas lo aplicarán; el borrador aún no valida roles. |
| J4 | Campos de modelo de DEC-28 y DEC-30: hash del PIN, `description` y activo en `Dish`, emoji en la categoría, costo total en la compra, costo unitario en `Ingredient` | `apps/*/models.py` | Los piden los formularios. |

## 3. Rutas que esperan las vistas

Los nombres son el contrato y no cambian; las rutas (`path`) son una **propuesta** que decide quien registre `urls.py`.

### `pos` (vistas de Tarín, `apps/pos/views.py`) — ya escritas en borrador

| Nombre | Ruta propuesta | Vista | Método |
|---|---|---|---|
| `pos:order_builder` | `pos/` | `order_builder` | GET |
| `pos:dish_list` | `pos/dishes/` | `dish_list` | GET (HTMX), `?category=` `?q=` |
| `pos:add_item` | `pos/dishes/<int:dish_id>/add/` | `add_item` | POST |
| `pos:remove_dish` | `pos/dishes/<int:dish_id>/remove/` | `remove_dish` | POST |
| `pos:remove_item` | `pos/items/<int:line_id>/remove/` | `remove_item` | POST |
| `pos:set_payment_method` | `pos/order/payment-method/` | `set_payment_method` | POST |
| `pos:confirm_sale` | `pos/order/confirm/` | `confirm_sale` | POST |
| `pos:open_session` | `pos/cash-session/open/` | `open_session` | GET y POST |
| `pos:close_session` | `pos/cash-session/close/` | `close_session` (escrita; su plantilla es de Yahir) | GET y POST |
| `pos:sync_operations` | `pos/sync/` | `views_sync.sync_operations` (Jesús + Jared) | POST, contrato v1 |

### `catalog` (vistas de Tarín) — escritas en borrador

| Nombre | Ruta propuesta | Método |
|---|---|---|
| `catalog:dish_catalog` | `catalog/` | GET |
| `catalog:dish_create` | `catalog/dishes/new/` | GET y POST |
| `catalog:dish_edit` | `catalog/dishes/<int:dish_id>/edit/` | GET y POST |
| `catalog:recipe_edit` | `catalog/dishes/<int:dish_id>/recipe/` | GET y POST |
| `catalog:add_recipe_line` | `catalog/recipe-lines/new/` | GET (HTMX), `?index=` |
| `catalog:ingredient_create` | `catalog/ingredients/new/` | GET y POST |

### `inventory` (vistas de Yahir) — pendientes

| Nombre | Ruta propuesta | Método |
|---|---|---|
| `inventory:ingredient_list` | `inventory/` | GET |
| `inventory:register_purchase` | `inventory/purchases/new/` | GET y POST |
| `inventory:register_waste` | `inventory/waste/new/` | GET y POST |

### `reports` (vistas de Yahir) — pendientes

| Nombre | Ruta propuesta | Método |
|---|---|---|
| `reports:cash` | `reports/cash/` | GET (página Caja) |
| `reports:reports` | `reports/` | GET |
| `reports:sales_by_period` | `reports/sales/` | GET (HTMX) |
| `reports:export_daily_sales_pdf` | `reports/daily-sales.pdf` | GET, `?day=AAAA-MM-DD` |

### `accounts` (vistas de Yahir) — pendientes

| Nombre | Ruta propuesta | Método |
|---|---|---|
| `accounts:activate_device` | `accounts/activate/` | GET (diálogo del PIN) y POST (valida el PIN de un Administrador y abre la sesión permanente de la cuenta de cajero; DEC-34, sin login ni logout) |
| `accounts:admin_pin` | `accounts/pin/` | GET (devuelve `components/pin_dialog.html` con `module_label` y `next_url`) y POST (valida; correcto: 204 con `HX-Redirect` a `next`; incorrecto: 422 con el diálogo y `HX-Retarget: #dialog`) |
| `accounts:pin_verifiers` | `accounts/pin-verifiers/` | GET (verificadores para el modo sin red, DEC-28) |

## 4. Cómo comprobar que quedó conectado

1. `python manage.py check` sin errores.
2. Abrir `/pos/`: los botones ya no apuntan a `#`.
3. Las pruebas de `apps/<app>/tests_views.py` siguen en verde; no dependen de las rutas porque llaman a las vistas directamente.

# Rutas (URLs) para conectar las vistas

**Fecha:** 15 de octubre de 2026 (antes, 3 y 8 de octubre) · **Estado:** rutas de la interfaz registradas; quedan las del backend y el PIN real · **Lo prepara:** Alejandro Tarín · **Para:** Jesús, Jared, Diego y Yahir

## Por qué existe

Las vistas de la interfaz se escriben con su contrato vista–plantilla. Cada vista resuelve sus URLs **por nombre** con `reverse()`, por ejemplo `pos:add_item`, y se las pasa a la plantilla. Mientras la ruta no exista en `urls.py`, la vista pinta `#` y la pantalla se ve, pero sus botones no llaman al servidor.

Este documento dice qué rutas hay, con qué nombre, quién las registra y qué falta.

## 1. De quién es `urls.py` (resuelto)

Se quedó la opción de DEC-31: **vistas, URLs y plantillas son del frontend** (`CLAUDE.md` §7). `pos` y `catalog` son de Tarín; `inventory`, `reports` y `accounts`, de Yahir. `config/urls.py` sigue siendo de Jesús.

## 2. Pendientes de Jesús (`config/`, `apps/core/`)

| # | Pendiente | Archivo | Estado |
|---|---|---|---|
| J1 | Incluir las rutas de `catalog`: `path("catalog/", include("apps.catalog.urls"))` | `config/urls.py` | **Hecho** en el PR #44 (8-oct-2026). |
| J2 | Procesador de contexto con lo que piden el menú y la barra superior: `nav_modules`, `active_module`, `cash_session_open`, `session_total`, `sync_pending`, `user_initials`, `logout_url`, `search_placeholder`, `search_url`, `search_target` y **`hide_search`** (nuevo: oculta el buscador en Caja y Reportes) | `apps/core/context_processors.py` y su registro en `config/settings.py` | Pendiente. Hoy cada vista lo arma con `_shell_context()` o `_shell()` como borrador, envuelto por el simulacro (§5). La lista completa está al inicio de `apps/core/templates/base.html`. |
| J3 | Mixin o decorador de rol y de PIN de Administrador | `apps/core/mixins.py` | Pendiente. Reemplaza a `preview.require_admin_pin` (§5). |
| J4 | Campos de modelo de DEC-30: `description` y activo en `Dish`, emoji en la categoría, costo total en la compra, costo unitario en `Ingredient` | `apps/*/models.py` | `catalog` en curso (PR #48, Issue #13). El PIN ya no necesita campo: es la contraseña de la cuenta (DEC-38, PR #46), y el verificador sin red quedó en `User.offline_verifier`. |

## 3. Rutas registradas

Los nombres son el contrato y no cambiaron: las rutas quedaron tal como se propusieron.

### `pos` (Tarín, `apps/pos/urls.py`) — PR #44

| Nombre | Ruta | Vista | Método |
|---|---|---|---|
| `pos:order_builder` | `pos/` | `order_builder` | GET |
| `pos:dish_list` | `pos/dishes/` | `dish_list` | GET (HTMX), `?category=` `?q=` |
| `pos:add_item` | `pos/dishes/<int:dish_id>/add/` | `add_item` | POST |
| `pos:remove_dish` | `pos/dishes/<int:dish_id>/remove/` | `remove_dish` | POST |
| `pos:remove_item` | `pos/items/<int:line_id>/remove/` | `remove_item` | POST |
| `pos:set_payment_method` | `pos/order/payment-method/` | `set_payment_method` | POST |
| `pos:confirm_sale` | `pos/order/confirm/` | `confirm_sale` | POST |
| `pos:open_session` | `pos/cash-session/open/` | `open_session` | GET y POST |
| `pos:close_session` | `pos/cash-session/close/` | `close_session` (su plantilla es de Yahir) | GET y POST |

### `catalog` (Tarín, `apps/catalog/urls.py`) — PR #44

| Nombre | Ruta | Método |
|---|---|---|
| `catalog:dish_catalog` | `catalog/` | GET |
| `catalog:dish_create` | `catalog/dishes/new/` | GET y POST |
| `catalog:dish_edit` | `catalog/dishes/<int:dish_id>/edit/` | GET y POST |
| `catalog:recipe_edit` | `catalog/dishes/<int:dish_id>/recipe/` | GET y POST |
| `catalog:add_recipe_line` | `catalog/recipe-lines/new/` | GET (HTMX), `?index=` |
| `catalog:ingredient_create` | `catalog/ingredients/new/` | GET y POST |

### `inventory` (Yahir, `apps/inventory/urls.py`) — PR #41

| Nombre | Ruta | Método |
|---|---|---|
| `inventory:ingredient_list` | `inventory/` | GET, `?q=` (HTMX) |
| `inventory:register_purchase` | `inventory/purchases/new/` | GET y POST |
| `inventory:register_waste` | `inventory/waste/new/` | GET y POST |

### `reports` (Yahir, `apps/reports/urls.py`) — PR #40 y #43

| Nombre | Ruta | Método |
|---|---|---|
| `reports:cash` | `reports/cash/` | GET (página Caja), `?periodo=hoy\|semana\|mes` (HTMX) |
| `reports:reports` | `reports/` | GET, `?periodo=…&fecha=AAAA-MM-DD` (HTMX, con `hx-push-url`) |
| `reports:export_daily_sales_pdf` | `reports/daily-sales.pdf` | GET, `?day=AAAA-MM-DD` |

`reports:sales_by_period` (`reports/sales/`) **ya no hace falta**: `reports:reports` cambia de periodo con sus parámetros y devuelve las columnas como fragmento.

### `accounts` (Yahir, `apps/accounts/urls.py`) — PR #44, temporal

| Nombre | Ruta | Método |
|---|---|---|
| `accounts:admin_pin` | `accounts/pin/` | GET (diálogo del PIN con `module_label` y `next_url`) y POST (correcto: 204 con `HX-Redirect` a `next`; incorrecto: 422 con el diálogo y `HX-Retarget: #dialog`). **Hoy es el simulacro (§5): acepta cualquier PIN de 6 dígitos.** |

## 4. Rutas que faltan

| Nombre | Ruta propuesta | Quién | Para qué |
|---|---|---|---|
| `pos:sync_operations` | `pos/sync/` | Jesús + Jared (`views_sync.sync_operations`) | POST, contrato v1. Está comentada en `pos/urls.py` hasta que exista la vista. |
| `accounts:activate_device` | `accounts/activate/` | Yahir (vista) y Diego (servicio) | GET (diálogo del PIN) y POST (valida el PIN de un Administrador y abre la sesión permanente de la cuenta de cajero; DEC-34, sin login ni logout). |
| `accounts:pin_verifiers` | `accounts/pin-verifiers/` | Yahir (vista) y Diego (servicio) | GET: verificadores para el modo sin red (DEC-28). |

La vista real de `accounts:admin_pin` también es de Yahir y Diego: conserva el nombre y la ruta, y valida el PIN con `check_password`, porque el PIN es la contraseña de la cuenta (DEC-38).

## 5. Simulacro del PIN y de la caja (`apps/core/preview.py`, temporal)

Entró a `main` a propósito con el PR #44 para que el equipo pueda recorrer todas las pantallas. **No valida nada:** cualquier PIN de 6 dígitos desbloquea Productos, Inventario, Caja y Reportes por 30 minutos, y el estado de la caja vive en la sesión. En las pruebas de vistas (sin sesión) todo queda desbloqueado.

Se retira, con todas las llamadas a `preview.` de las vistas, cuando existan:

| Pieza real | De quién | Reemplaza a |
|---|---|---|
| Mixin de rol y PIN (J3) | Jesús | `preview.require_admin_pin` |
| Procesador de contexto (J2) | Jesús | `preview.apply_to_shell` y los `_shell_context()` de cada app |
| Validador de la contraseña de 6 dígitos y servicio que valida el PIN | Diego | la validación de `accounts:admin_pin` |
| Vista real del PIN y `accounts:activate_device` | Yahir | `accounts/views.py` del simulacro |
| Servicios del turno de caja | Jared y Jesús | `preview.is_cash_open` y `preview.set_cash_open` |

## 6. Cómo comprobar que quedó conectado

1. `python manage.py check` sin errores.
2. Abrir `/pos/`, `/catalog/`, `/inventory/`, `/reports/cash/` y `/reports/`: las pantallas con candado piden el PIN y los botones ya no apuntan a `#`.
3. Las pruebas de `apps/<app>/tests_views.py` siguen en verde; no dependen de las rutas porque llaman a las vistas directamente.

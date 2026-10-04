# Pantallas y fragmentos HTMX (plan de interfaz, rev. 1.1)

Plan de la Fase 3 de `traducir-prototipos-figma-SGFT.md`, acordado con Tarín el 3 de octubre de 2026 (DEC-30). Define qué región de cada pantalla refresca el servidor, con qué vista y con qué disparador, los estados que Figma no dibuja y el diseño de los formularios. Es la base del contrato vista–plantilla (Fase 4) y del maquetado (Fase 5).

## Contenido
1. Convenciones
2. Común a todas las pantallas
3. Nueva Venta
4. Productos
5. Caja
6. Inventario
7. Reportes
8. Estados que Figma no dibuja
9. Comportamiento sin conexión
10. Formularios
11. Pedidos a otros dueños

---

## 1. Convenciones

- **Tipos de interacción:** *enlace* (`<a href>`, cambia de módulo), *HTMX* (lee o escribe datos en una vista nombrada por la acción), *Alpine* (solo estado visual local) y *HATEOAS* (el servidor decide qué controles existen).
- **Fragmentos:** viven en `templates/<app>/partials/`, empiezan con el elemento que lleva el `id` destino y se devuelven con la misma vista que sirve la página (`request.htmx`).
- **Diálogos:** se insertan en `<div id="dialog">` con `hx-get`, extienden `components/dialog.html` y responden 422 con el mismo fragmento y los errores si el servidor rechaza los datos.
- **Actualizaciones laterales:** cuando una acción cambia otra región (por ejemplo, agregar al ticket cambia la tarjeta del platillo y el total de la sesión), la vista las devuelve con `hx-swap-oob`.
- **Dueño de cada vista (DEC-31):** `pos` y `catalog`, Tarín; `inventory`, `reports` y `accounts`, Yahir. Los servicios que llaman son del backend: `pos` y `reports`, Jared; `catalog` e `inventory`, Diego.
- **Importes:** `Decimal` en el contexto, mostrados con `floatformat:"2g"` (es-MX: «$4,850.00»).

## 2. Común a todas las pantallas

| Región | Archivo | `id` | Vista | Disparador | Tipo |
|---|---|---|---|---|---|
| Menú lateral | `core/base.html` + `components/sidebar.html` | `app-menu` | contexto común | hamburguesa, «Cerrar menú», velo, Escape | Alpine |
| Módulos del menú | `components/nav_item.html` | — | — | clic | enlace. Productos, Inventario, Caja y Reportes piden PIN de Administrador: mientras el módulo siga bloqueado, el servidor manda `pin_url` y el elemento es un botón que abre `components/pin_dialog.html` en `#dialog`. Con el PIN correcto, `HX-Redirect` al módulo. |
| Entrada directa a un módulo bloqueado | `core/pin_required.html` | `dialog` | mixin de rol y PIN (Jesús) | carga | 403 con el aviso «<Módulo> requiere PIN» y el diálogo del PIN ya abierto; «Escribir PIN» lo reabre |
| Barra superior | `components/top_bar.html` | — | contexto común | carga | servidor |
| Estado de caja y total de sesión | dentro de la barra | `cash-status`, `session-total` | las vistas que los cambian | abrir o cerrar caja, confirmar venta | `hx-swap-oob` |
| Mensajes | `core/base.html` | `messages` | cualquiera | errores 403, 409, 422 | `hx-swap-oob` |
| Diálogos | `core/base.html` | `dialog` | la vista del formulario | botón que abre el diálogo | `hx-get` |

**Barra superior:** la campana se oculta (`show_notifications` = False; queda en el componente). El perfil se muestra sin acción. El buscador filtra en Nueva Venta, Productos e Inventario; en Caja y Reportes no se muestra.

## 3. Nueva Venta (`pos`, 3.3.1, 3.3.5)

| Región | Archivo | `id` | Vista | Disparador | Tipo |
|---|---|---|---|---|---|
| Página | `pos/order_builder.html` | — | `pos:order_builder` | carga | enlace |
| Área de venta o caja cerrada | `pos/partials/sale_area.html` | `sale-area` | `pos:order_builder` | carga; abrir caja | HATEOAS: sin turno abierto se pinta el contenido deshabilitado (opacidad 35 %, `inert`) con `components/cash_closed_notice.html` |
| Diálogo «Abrir caja» | `pos/partials/open_cash_session.html` (usa `components/open_cash_dialog.html`) | `dialog` | `pos:open_session` (GET formulario, POST valida) | «Abrir caja» | HTMX; al abrir, reemplaza `sale-area` y actualiza `cash-status` por OOB |
| Aviso de stock | `components/stock_notice.html` en el encabezado | `stock-notice` | `pos:order_builder`, `pos:confirm_sale` | carga; tras confirmar | HATEOAS + OOB; solo si hay insumos Bajo o Crítico |
| Chips de categoría | `pos/partials/category_chips.html` | `category-chips` | `pos:dish_list` | clic en chip | `hx-get` → `dish-list`; los chips por OOB (el activo lo decide el servidor) |
| Rejilla de platillos | `pos/partials/dish_list.html` | `dish-list` | `pos:dish_list` | categoría, búsqueda (F2), Ordenar, Filtros | `hx-get` |
| Agregar 1 | `components/dish_card.html` | — | `pos:add_item` | toque | `hx-post` → `order-summary`; la tarjeta por OOB (`dish-<id>`) |
| Menú de cantidad | `components/quantity_menu.html` | — | `pos:add_item`, `pos:remove_item` | presión larga 0.5 s; − / + | Alpine lo abre; HTMX cambia la cantidad |
| Ticket en curso | `pos/partials/order_summary.html` | `order-summary` | `pos:add_item`, `pos:remove_item`, `pos:set_payment_method`, `pos:confirm_sale` | agregar, quitar, método, confirmar | `hx-post` |
| Quitar | `components/ticket_line.html` | — | `pos:remove_item` | botón rojo | `hx-post` → `order-summary` |
| Método de pago | dentro de `order_summary` | — | `pos:set_payment_method` | Efectivo / Transferencia | `hx-post`; el seleccionado lo decide el servidor |
| Confirmar compra | dentro de `order_summary` | — | `pos:confirm_sale` | clic | `hx-post` con `hx-disabled-elt`; responde con el ticket nuevo vacío y OOB de `session-total` y `stock-notice` |
| Ordenar / Filtros | herramientas de lista | — | `pos:dish_list` | clic | `hx-get` con `orden=nombre|categoria` y filtro de categoría |

## 4. Productos (`catalog`, 3.2.1, 3.2.3; solo Administrador)

| Región | Archivo | `id` | Vista | Disparador | Tipo |
|---|---|---|---|---|---|
| Página | `catalog/products.html` | — | `catalog:dish_catalog` | carga, con PIN | enlace |
| Rejilla del catálogo | `catalog/partials/dish_grid.html` | `dish-grid` | `catalog:dish_catalog` | búsqueda, Ordenar, Filtros | `hx-get` |
| Tarjeta | `components/dish_catalog_card.html` | `dish-<id>` | — | — | la disponibilidad la decide el servidor |
| Editar platillo | `catalog/partials/dish_form.html` | `dialog` | `catalog:dish_edit` (GET y POST) | «Editar» | HTMX; al guardar, la tarjeta por OOB |
| Agregar platillo | `catalog/partials/dish_form.html` | `dialog` | `catalog:dish_create` | botón «Agregar platillo» a la derecha del encabezado (acordado: sustituye al tile y a «Ordenar»/«Filtros») | HTMX; al guardar, `dish-grid` |
| Receta | `catalog/partials/recipe_form.html` | `dialog` | `catalog:recipe_edit` | «Receta» | HTMX |

## 5. Caja (`reports/cash.html`; solo Administrador)

| Región | Archivo | `id` | Vista | Disparador | Tipo |
|---|---|---|---|---|---|
| Página | `reports/cash.html` | — | `reports:cash` | carga, con PIN | enlace |
| Gráfica de ventas | `reports/partials/sales_chart.html` | `sales-chart` | `reports:cash` | chips Hoy / Semana / Mes | `hx-get` |
| Ganancias, mermas, total de hoy | `reports/partials/cash_kpis.html` | `cash-kpis` | `reports:cash` | carga | servidor |
| Cierre de turno | `pos/partials/cash_session_close.html` (Yahir, pendiente) | `dialog` | `pos:close_session` (escrita el 4-oct-2026: GET diálogo, POST cierra) | «Cerrar caja» | `hx-get` → `dialog`; 409 con operaciones sin sincronizar y 422 en el diálogo; al cerrar, `HX-Redirect` a Nueva Venta («Caja cerrada») con el resultado en un mensaje |

`reports` solo lee; el cierre lo aplica `pos`. La plantilla de Caja incluye el fragmento de `pos`, pero `reports` no importa código de `pos`.

## 6. Inventario (`inventory`, 3.2.5, 3.2.7, 3.2.8; solo Administrador)

| Región | Archivo | `id` | Vista | Disparador | Tipo |
|---|---|---|---|---|---|
| Página | `inventory/ingredient_list.html` | — | `inventory:ingredient_list` | carga, con PIN | enlace |
| Rejilla de insumos | `inventory/partials/ingredient_grid.html` | `ingredient-grid` | `inventory:ingredient_list` | búsqueda, Ordenar, Filtros | `hx-get` |
| Insumos bajos | `inventory/partials/stock_alert_badge.html` | `low-stock` | `inventory:ingredient_list` | tras compra o merma | OOB |
| Registrar compra | `inventory/partials/purchase_form.html` | `dialog` | `inventory:register_purchase` | botón | HTMX; al guardar, OOB de `ingredient-grid` y `low-stock` |
| Registrar merma | `inventory/partials/waste_form.html` | `dialog` | `inventory:register_waste` | botón | ídem |
| Agregar insumo | `catalog/partials/ingredient_form.html` (junto a su vista; hecho el 4-oct-2026) | `dialog` | `catalog:ingredient_create` | tile «Agregar insumo» | HTMX; al guardar, aviso en `#messages` y `HX-Trigger: ingredient-created`, que Inventario escucha (`hx-trigger="ingredient-created from:body"`) para refrescar `ingredient-grid` y `low-stock` |

## 7. Reportes (`reports`, 3.5.2–3.5.5; solo Administrador)

| Región | Archivo | `id` | Vista | Disparador | Tipo |
|---|---|---|---|---|---|
| Página | `reports/reports.html` | — | `reports:reports` | carga, con PIN | enlace |
| Las cuatro columnas | `reports/partials/report_columns.html` | `report-columns` | `reports:sales_by_period` | chips Hoy / Semana / Mes, campo de fecha, «Calendario» | `hx-get` con `hx-push-url` |
| Exportar PDF | `reports/partials/export_pdf_form.html` | `dialog` | `reports:export_daily_sales_pdf` | «Exportar PDF» | `hx-get` abre el diálogo; «Descargar» es un envío normal (GET), no HTMX, para que el navegador baje el archivo |

## 8. Estados que Figma no dibuja

| Estado | Dónde | Diseño (propuesta salvo donde se indica) |
|---|---|---|
| **Ticket sin productos** | Nueva Venta | Dentro del ticket, `components/empty_state.html` con ícono `receipt` y «Toca un platillo para agregarlo». Subtotal y total en «$0.00». El método de pago y «Confirmar compra» **se ven deshabilitados** (`aria-disabled`, opacidad 50 %): el panel no cambia de tamaño y el cajero ve el siguiente paso. Lo decide el servidor (`order.lines` vacío). |
| **Categoría sin platillos** | Nueva Venta, Productos | Mensaje centrado en la rejilla: **«Agrega platillos para verlos»** (acordado). |
| **Reporte sin ventas** | Reportes, gráfica de Caja | Mensaje centrado: **«Sin ventas para este periodo»** (acordado). |
| Inventario sin insumos | Inventario | «Agrega insumos para verlos», centrado, con el tile «Agregar insumo». |
| Sin turno abierto | Nueva Venta | Estado «Caja cerrada» de Figma. Una venta que llegue sin turno responde 409 con el aviso. |
| Cierre con ventas sin sincronizar | Caja | En línea: 409 con «Faltan N operaciones por sincronizar» (regla 5). Sin red: se encola (§9). |
| PIN incorrecto o datos inválidos | Diálogos | 422 con el mismo diálogo y el error bajo el campo (`components/field.html`, `error`). |
| Sin permiso | Módulos con candado | 403 y redirección al PIN (`HX-Redirect`). |
| Cargando | Confirmar, abrir y cerrar caja, guardar | `hx-disabled-elt` en el botón y `hx-indicator` en el formulario. |
| Foco visible | Todos los controles | `Foco/Anillo` (ya en los componentes). |

## 9. Comportamiento sin conexión

- **Menú:** todos los módulos siguen habilitados. El estado de sincronización muestra **«Sin conexión · N pendientes»** (acordado).
- **Nueva Venta:** opera completa sin red (Fase 6, `static/pos/`).
- **Caja y Reportes:** se consultan con los datos de la **última sincronización**; las ventas hechas sin red **no aparecen hasta sincronizar**. Ambas muestran «Última sincronización: <fecha y hora>» junto al subtítulo.
- **Cierre de caja sin red:** se encola como `cierre_turno` (contrato v2) y Nueva Venta vuelve a «Caja cerrada» en el dispositivo.
- **Productos e Inventario:** con el contrato v2 aprobado, los cambios se encolan (DEC-29). La existencia mostrada es la copia local que descuentan las ventas, con «Última sincronización» (sin la palabra «teórica»).

## 10. Formularios

Todos extienden `components/dialog.html` (480 de ancho, pad 32, radio 24, encabezado con ícono en cuadro durazno de 56, «Cerrar diálogo», acciones «Cancelar» + primario) y usan `components/field.html`. Ninguno existe en Figma: es diseño propio con los componentes del sistema. Los datos que llenan las listas (categorías, insumos, unidades, motivos) los manda el servidor.

### 10.1 Editar / Agregar platillo — `catalog/partials/dish_form.html`
Ícono `package`. Título «Editar platillo» o «Agregar platillo»; subtítulo con el nombre.

| Campo | `kind` | Reglas |
|---|---|---|
| Nombre | text | Obligatorio, 60 caracteres máximo. |
| Categoría | select | Obligatorio. El emoji de la tarjeta sale de la categoría (no se edita). |
| Precio | money | Obligatorio, mayor que 0; dos decimales. Solo el Administrador (regla 6). |
| Descripción | textarea | Opcional, 120 caracteres (la tarjeta muestra 2 líneas). |
| (Insumos) | — | Se probó una lista de insumos dentro de este formulario y se descartó el 4-oct-2026: la receta se edita solo con «Receta» (§10.2). |
| Activo en el menú | checkbox | Si se desmarca, no aparece en Nueva Venta. |

Primario: «Guardar».

### 10.2 Receta — `catalog/partials/recipe_form.html`
Ícono `clipboard-list`. Título «Receta»; subtítulo con el platillo. Una fila por insumo:

| Columna | Componente | Reglas |
|---|---|---|
| Insumo | `field` select | Obligatorio; no se repite en la receta. |
| Cantidad | `field` quantity con la unidad del insumo a la derecha | Mayor que 0. |
| Quitar | `icon_button` peligro compacto con `minus` | Quita la fila. |

Debajo, «Agregar insumo» (Secundario, `plus`): `hx-get` que devuelve una fila vacía y la agrega al final (formset de Django; el servidor numera las filas). Primario: «Guardar receta». Sin filas, `empty_state` «Agrega insumos a la receta».

### 10.3 Registrar compra — `inventory/partials/purchase_form.html`
Ícono `package`. Título «Registrar compra».

| Campo | `kind` | Reglas |
|---|---|---|
| Insumo | select | Obligatorio. Puede venir preseleccionado desde «Insumos bajos». |
| Cantidad | quantity (unidad del insumo) | Mayor que 0. |
| Costo total | money | Obligatorio. El servidor actualiza el costo unitario del insumo (DEC-30). |
| Nota | textarea | Opcional (proveedor, factura). |

Primario: «Registrar compra». La «Sugerencia de compra» de Inventario puede llenar cantidades.

### 10.4 Registrar merma — `inventory/partials/waste_form.html`
Ícono `trash-2`. Título «Registrar merma».

| Campo | `kind` | Reglas |
|---|---|---|
| Insumo | select | Obligatorio. |
| Cantidad | quantity | Mayor que 0. |
| Motivo | select | Obligatorio: Caducidad, Mal almacenamiento, Daño en empaque, Maduración, Otro (acordado). |
| Especifica el motivo | text | Solo aparece con «Otro» (Alpine lo muestra; el servidor lo exige): obligatorio, **máximo 50 caracteres** (acordado). |

Primario: «Registrar merma» (el botón sigue siendo Primario; el rojo se reserva para quitar).

### 10.5 Agregar insumo — `catalog/partials/ingredient_form.html`
Ícono `clipboard-list`. Título «Agregar insumo».

| Campo | `kind` | Reglas |
|---|---|---|
| Nombre | text | Obligatorio. |
| Unidad de medida | select | Obligatoria: kg, g, L, ml, pzas (acordado). Se fija al dar de alta el insumo; compras, mermas y recetas la toman de ahí. |
| Existencia inicial | quantity | Mayor o igual a 0; se registra como compra inicial. |
| Costo total de la existencia inicial | money | Obligatorio si la existencia es mayor que 0. |
| Mínimo | quantity | Obligatorio (`min_stock`, regla 3). |

### 10.6 Cerrar caja — `pos/partials/cash_session_close.html`
Ícono `wallet`. Título «Cerrar caja»; subtítulo con el turno.
- Fila clave-valor «Efectivo esperado en caja» (servidor).
- `field` money «Efectivo contado», obligatorio.
- Nota informativa: la diferencia se registra y no bloquea (regla 13).
- Pendientes: «N operaciones pendientes de sincronizar» con punto `estado/alerta`; en línea, si N > 0, el servidor responde 409 (regla 5); sin red, el cierre se encola.
- Primario: «Cerrar caja».

### 10.7 Exportar PDF — `reports/partials/export_pdf_form.html`
Ícono `download`. Título «Exportar PDF»; subtítulo «Ventas del día».
- `field` date «Día elegido», obligatorio, por omisión hoy (o el día seleccionado en la pantalla).
- Primario «Descargar» con `download`: formulario GET normal hacia `reports:export_daily_sales_pdf`.
- Si hay operaciones sin sincronizar, el servidor lo niega y dice cuántas faltan (DEC-13).

### 10.8 Abrir caja
Ya existe como `components/open_cash_dialog.html` (Figma 2044:2111, 6 casillas de PIN, DEC-28).

## 11. Pedidos a otros dueños

| Para | Pedido |
|---|---|
| Jesús | Procesador de contexto en `apps/core/context_processors.py` con lo que espera `base.html` (lista al inicio del archivo). |
| Jesús | Campos: `description` en `Dish`; emoji en la categoría; costo total en la compra y costo unitario en `Ingredient`; activo en `Dish`. |
| Jesús + Jared + Tarín | Aprobar el contrato v2 con `cierre_turno` (P13). |
| Diego | Servicios de `catalog` e `inventory` que llaman las vistas de §4 y §6; unidades y motivos de merma acordados. |
| Jared | Servicios de `pos` y `reports` de §3, §5 y §7; el PDF del día elegido. |
| Tarín | Vistas, URLs y plantillas de `pos` y `catalog` (DEC-31). |
| Yahir | Vistas, URLs y plantillas de `inventory`, `reports` y `accounts`, y el fragmento de cierre de turno (DEC-31). |

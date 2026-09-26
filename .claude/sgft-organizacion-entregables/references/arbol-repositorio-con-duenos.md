# Árbol del repositorio SGFT con dueño por ruta

**Base:** árbol de `estructura-y-flujo-datos-SGFT.md` §1 (rev. 11-sep-2026), completado con las rutas de entregables que cita `WBS-SGFT.md` Rev. 3 (`docs/…`, `.github/…`). Lo marcado **⏸** es un paquete en evaluación: la ruta está reservada, pero el archivo no se crea hasta que el equipo lo apruebe. Lo marcado **(DEC-09)** no existía en la estructura base y se aprobó el 24-sep-2026 para dar un lugar único a entregables del WBS; lo marcado **🆕** corresponde a los paquetes nuevos de la WBS Rev. 4 (DEC-07). Ver `decisiones-y-pendientes.md`.

**Integrador:** Tarín aprueba y fusiona todos los PR, y figura en todas las rutas de `CODEOWNERS` (DEC-16, DEC-18); toda ruta que no aparezca aquí se le consulta a él. **Segunda persona:** con la revisión obligatoria de code owners (DEC-10), cada ruta tiene además una segunda persona que puede aprobar los PR de su dueño; no se repite aquí para no cargar el árbol. Consúltala con `python scripts/dueno_de_ruta.py <ruta>`.

**Siglas de dueño:** `JH` Jesús Hernández (backend + BD) · `DG` Diego Galindo (backend) · `JB` Jared Beltrán (backend) · `AT` Alejandro Tarín (frontend) · `YE` Yahir Enríquez (frontend).
**Notación:** `[dueño]` · `{+colaborador / pareja}` · `(rev: revisor obligatorio)` · `⟂ función = autor` cuando una función dentro del archivo la escribe alguien distinto del dueño.

## Contenido

1. Raíz y configuración
2. `apps/core`
3. `apps/accounts` (M-USR)
4. `apps/catalog` (datos maestros, administrados desde M-INV)
5. `apps/pos` (M-PDV, en línea y offline)
6. `apps/inventory` (M-INV)
7. `apps/reports` (M-REP)
8. `static/`
9. Pruebas (`tests_fixtures/`, `tests_e2e/`)
10. `docs/` y `.github/`
11. Lectura por capas: qué toca cada quien dentro de una misma app

---

## 1. Raíz y configuración

```
sgft/
├── manage.py                         [JH]
├── requirements.txt                  [JH]  toda dependencia nueva se justifica en el PR
├── .env.example                      [JH]  WBS 5.2 — solo nombres de variables
├── .gitignore                        [JH]
├── CLAUDE.md                         [DG]
├── config/                           [JH]  WBS 5.2 — sin lógica de negocio
│   ├── settings.py                         DATABASES vía DATABASE_URL, INSTALLED_APPS, django-htmx
│   ├── urls.py                             solo include() de los urls.py de cada app
│   ├── wsgi.py                             lo usa Gunicorn (WBS 5.3)
│   └── asgi.py
│
├── apps/__init__.py                  [JH] (rev: JB)  obligatorio: sin él, manage.py test corre 0 pruebas
```

**Por qué Jesús:** `settings.py` concentra la conexión a PostgreSQL (Neon/Supabase), las apps instaladas y el middleware; es la misma persona que administra el esquema y los entornos (5.2, 5.3). Cualquier otro integrante que necesite registrar una app o un middleware lo pide en su PR y Jesús lo aprueba.

**Archivo de despliegue (DEC-09):** el archivo de configuración del proveedor (por ejemplo `render.yaml` o `Procfile`) va en la raíz, dueño `[JH]{+AT}` — WBS 5.3. Se define cuando se elija Render o Railway.

## 2. `apps/core` — infraestructura compartida (sin RF propio)

```
apps/core/                            [JH]  apps.py, __init__.py
├── mixins.py                         [JH]  WBS 3.1.3 — RoleRequiredMixin y decoradores por rol
├── templates/                        [AT] (rev: YE)  WBS 2.1
│   └── base.html                           <head> con Bootstrap 5 + HTMX + Alpine por CDN;
│                                           <body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
└── templatetags/                     [AT] (rev: JH)  filtros de presentación (formato de dinero)
```

- `mixins.py` lo **modifica** solo Jesús; lo **aplica** cada dueño de `views.py` en sus vistas (Diego, Jared). Ocultar un botón en la plantilla no es control de acceso.
- `templatetags/` son archivos Python, pero su función es de presentación: por eso los lleva frontend. Un filtro solo formatea un valor ya calculado; nunca suma, redondea importes ni decide reglas.

## 3. `apps/accounts` — M-USR

```
apps/accounts/                        [DG] (rev: JH)
├── models.py                         [JH]  WBS 3.1.1 — User(AbstractUser) + role
├── migrations/                       [JH]
├── services.py                       [DG]  WBS 3.1.2, 3.1.5 🆕 — create_user(), change_role(), desactivación
├── views.py                          [DG]  WBS 3.1.2, 3.1.5 🆕 — login/logout, administración de cuentas
├── urls.py                           [DG]
├── admin.py                          [DG]
├── templates/accounts/               [YE] (rev: AT)  WBS 3.1.2, 2.2.2
│   ├── login.html                          página completa
│   └── partials/                           fragmentos HTMX de administración de cuentas (3.1.5 🆕)
└── tests.py                          [DG]  WBS 3.1.4 (incluye 3.1.5)
```

## 4. `apps/catalog` — datos maestros

```
apps/catalog/                         [DG]
├── models.py                         [JH]  WBS 3.2.1–3.2.4 — Dish, Ingredient, Recipe (+ min_stock)
├── migrations/                       [JH]
├── admin.py                          [DG]  WBS 3.2.1–3.2.3 — CRUD del Administrador (Django Admin),
│                                           incluidos platillos y precios; Recipe como inline de Dish
├── fixtures/                         [YE] (rev: JH)  WBS 4.5 (DEC-09) — menú demo ficticio; el repo es público: nunca datos reales
└── tests.py                          [DG]  WBS 3.2.9
```

`catalog` no tiene vistas ni plantillas propias: su interfaz es Django Admin. Si en el futuro se requiere una pantalla propia, se registra como paquete WBS nuevo antes de crearla.

## 5. `apps/pos` — M-PDV

```
apps/pos/                             [JB] (rev: JH)  urls.py, admin.py, apps.py
├── models.py                         [JH]  Order, OrderItem, Modifier, Sale (dos marcas de tiempo),
│                                           SaleAdjustment, QuarantinedSale, CashRegisterSession,
│                                           QuarantinedCashSession — con restricción de unicidad del UUID
├── migrations/                       [JH]
├── services.py                       [JH] (rev: JB)  WBS 3.3.5, 3.3.8 🆕, 3.4.9 🆕 — confirm_sale(), cancel_sale(),
│                                           adjust_sale() con motivo, resolución de cuarentena y revisiones
├── services_cash_session.py          [JH]{+AT}  WBS 3.5.1, 3.4.7, 3.5.7 🆕 — open_session(), close_session(), current_session()
├── services_pricing.py               [JH] (rev: AT)  WBS 3.3.4, 3.4.5 — calcular_total(pedido) -> int, espejo de
│                                           calcularTotal() en static/pos/pricing.js; llaves en español (DEC-01)
├── views.py                          [JB] (rev: JH)  WBS 3.3.1–3.3.3, 3.3.5, 3.3.7, 3.3.8, 3.4.9, 3.5.1, 3.5.7
│                                           dish_list, order_builder, add_item, remove_item,
│                                           endpoints de modificadores, confirm_sale (vista),
│                                           open_cash_session / close_cash_session (vistas),
│                                           cancel / adjust (3.3.8 🆕), kitchen_queue / mark_prepared (3.3.7 ⏸),
│                                           bandeja de revisión (3.4.9 🆕)
│                                     ⟂ sync_operations() — POST /pos/sync/ = JH + JB en pareja (WBS 3.4.6)
├── urls.py                           [JB]
├── templates/pos/                    [AT] (rev: YE)  WBS 3.3.1–3.3.5, 3.3.7 ⏸, 3.3.8 🆕, 3.4.4, 3.5.1
│   ├── order_builder.html                  página completa (en línea); x-data offline en pareja con YE
│   ├── kitchen_queue.html                  WBS 3.3.7 ⏸ EN EVALUACIÓN — vista de cocina; sin red lee la cola local (pareja YE)
│   ├── cash_session_close.html       [YE] (rev: AT)  WBS 3.5.7 🆕 — cierre de turno, solo en línea
│   ├── review/                       [YE] (rev: AT)  WBS 3.4.9 🆕 — bandeja del Administrador: cuarentena,
│   │                                       existencias negativas, diferencias de precio (solo en línea)
│   └── partials/
│       ├── dish_list.html                  WBS 3.3.1
│       ├── order_summary.html              WBS 3.3.5, 3.3.8 🆕 — controles HATEOAS según order.status
│       │                                   (incluye "Cancelar / ajustar venta")
│       ├── cash_session_banner.html        WBS 3.5.1, 3.5.7 🆕 — estado del turno (abierto/cerrado)
│       └── kitchen_order.html              WBS 3.3.7 ⏸ EN EVALUACIÓN — tarjeta de pedido con sus personalizaciones
└── tests.py                          [JB]  WBS 3.3.6 (incluye pruebas de los paquetes 🆕)
                                      ⟂ PricingParityTest, pruebas de servicios y del contrato de sync = JH
```

**Regla de oro de `pos`:** los servicios transaccionales (`services*.py`) son de Jesús porque son los que abren `transaction.atomic()` y llaman a `inventory.services.deduct_for_sale()`; las vistas son de Jared porque solo hacen HTTP (validar rol, verificar turno, elegir plantilla con `request.htmx`, llamar al servicio). La vista `confirm_sale` es de Jared; el servicio `confirm_sale` es de Jesús. Mismo nombre, dos archivos, dos dueños — el contrato entre ambos es la firma del servicio.

## 6. `apps/inventory` — M-INV (solo en línea)

```
apps/inventory/                       [DG]
├── models.py                         [JH]  StockMovement (compra / venta / merma / ajuste)
├── migrations/                       [JH]
├── services.py                       [DG] (rev: JB)  WBS 3.2.5, 3.2.7, 3.2.8
│                                           register_purchase(), register_waste(), check_min_stock()
│                                     ⟂ deduct_for_sale() = JH (WBS 3.2.6)
├── views.py                          [DG]
├── urls.py                           [DG]  (implícito: la estructura lista views.py; toda app con vistas lleva urls.py)
├── templates/inventory/              [YE] (rev: AT)  WBS 3.2.5, 3.2.7, 3.2.8
│   └── partials/
│       └── stock_alert_badge.html          alerta visual, no bloquea la venta (regla 3)
├── fixtures/                         [YE] (rev: JH)  (DEC-09) existencias demo
└── tests.py                          [DG]  WBS 3.2.9
                                      ⟂ pruebas de deduct_for_sale() = JH
```

**Regla de dependencia:** `inventory` nunca importa de `pos`. Si una tarea de Diego parece requerirlo, la lógica está en la app equivocada: se consulta con Jesús.

## 7. `apps/reports` — M-REP (solo lectura)

```
apps/reports/                         [JB]
├── services.py                       [JB] (rev: JH)  WBS 3.5.3–3.5.5
│                                           sales_by_period(), top_dishes(), export_daily_sales_pdf()
│                                           (3.5.5: ventas del día a PDF, DEC-13)
│                                     ⟂ cash_close(session) = JH (WBS 3.5.2)
├── views.py                          [JB]
├── urls.py                           [JB]  (implícito)
├── templates/reports/                [YE] (rev: AT)  WBS 3.5.2–3.5.5
│   ├── cash_close.html                     carga completa, no HTMX
│   └── …                                   ventas por periodo, más vendidos, botón "Exportar ventas del día (PDF)"
└── tests.py                          [JB]  WBS 3.5.6
                                      ⟂ pruebas de cash_close() y descuadre = JH
```

`reports` no tiene `models.py`: lee `pos.Sale`, `pos.SaleAdjustment`, `pos.CashRegisterSession` e `inventory.StockMovement`. Si alguien propone un modelo en `reports`, es señal de que la lógica pertenece a otra app.

## 8. `static/`

```
static/
├── core/                             [AT]  (DEC-09) CSS propio global, solo si Bootstrap no alcanza
└── pos/                              [AT]{+YE}  PAREJA OBLIGATORIA — ADR-02 §6; leer ADR-02 completo antes
    ├── manifest.json                 [AT]{+YE}  WBS 3.4.1
    ├── sw.js                         [AT]{+YE}  WBS 3.4.1, 3.4.2 — Workbox por CDN (importScripts)
    ├── db.js                         [AT]{+YE} (rev: JB)  WBS 3.4.3, 3.4.7 — Dexie: catálogo, cola de
    │                                           ventas, cola de aperturas, estado de turno cacheado
    ├── pricing.js                    [AT]{+YE} (rev: JH)  WBS 3.4.4, 3.4.5 — calcularTotal(), centavos enteros,
    │                                           espejo de services_pricing.calcular_total()
    └── app.css                       [AT]{+YE}  estilos del PDV precacheados por Workbox (revision-tecnica §3)
```

La regla de la convención HTMX/Alpine §8 sigue vigente: no se escribe JavaScript suelto en `.js` propios. Los únicos `.js` propios del proyecto son estos cuatro de `static/pos/`, que existen por ADR-02.

## 9. Pruebas

```
tests_fixtures/                       [JH]{+AT}  WBS 3.4.5 — cambios requieren aprobación de ambos
└── pricing_cases.json                      casos compartidos de la prueba de paridad

tests_e2e/                            [YE]{+JB}  WBS 3.4.8, 4.6 — Playwright
├── parity/                           [AT] (rev: JH)  WBS 3.4.5
│   └── test_pricing.mjs                    node --test contra pricing_cases.json
├── test_pos_sale.py                       con y sin conexión
├── test_cash_session_open.py                   con y sin conexión
└── test_cash_close.py
```

**Tres tipos de "fixture" que no se deben confundir:**

| Ruta | Para qué | Dueño |
|---|---|---|
| `tests_fixtures/pricing_cases.json` | Únicamente la prueba de paridad Python/JS | JH + AT |
| `apps/<app>/fixtures/*.json` (DEC-09) | Datos demo ficticios para desarrollo y demostración (4.5) | YE (rev: JH) |
| Datos creados dentro de `tests.py` (`setUpTestData`) | Pruebas unitarias de cada módulo | autor de la prueba |

## 10. `docs/` y `.github/`

```
docs/                                 [DG]  solo Markdown; los .docx van al espacio compartido
├── SRS.md                            [DG]{+JH}  WBS 1.1.1–1.3.1; apéndice de matriz 4.3 = JH
├── manual-usuario.md                 [DG]{+AT, YE}  WBS 1.7 (si es Word → espacio compartido)
├── decisiones/                       [DG]  una decisión por archivo; la redacta quien la propone
│   ├── ADR-01-arquitectura-SGFT.md
│   ├── ADR-02-operacion-offline-SGFT.md
│   ├── convencion-htmx-alpine-SGFT.md      [AT] (rev: JB)  WBS 2.1
│   ├── contrato-sync-pdv.md                [JH]{+JB, AT}  v1 aprobada (DEC-02 a DEC-06); copia en assets/repo/
│   ├── nombres-modulo-precios.md           [JH] (rev: AT)  DEC-01; copia en assets/repo/
│   ├── organizacion-repositorio.md         [AT] (rev: DG)  DEC-07 a DEC-16; copia en assets/repo/
│   └── spike-offline-sprint1.md            [AT]{+JB}  WBS 5.4 (DEC-09)
├── diagramas/                        [JH]  WBS 1.5.1 (7 láminas .drawio + PNG/PDF), 1.6.1 (ER)
│   └── procesos/                     [DG]  WBS 1.4.1 (DEC-09) — Apéndice A
├── prototipos/                             prototipos desechables HTML/CSS/JS
│   ├── pdv-venta/index.html          [AT]  WBS 2.2.1
│   ├── usr-acceso/index.html         [YE] (rev: AT)  WBS 2.2.2
│   ├── inv-catalogo/index.html       [YE] (rev: AT)  WBS 2.2.3
│   └── rep-caja/index.html           [YE] (rev: AT)  WBS 2.2.4
├── calidad/                          (DEC-09)
│   ├── checklist-seguridad.md        [JH]  WBS 4.4
│   └── cobertura-sprint-N.md         [JB]{+YE}  WBS 4.1
└── entregas/                         [DG]  PDF de fases entregadas — inmutables

.claude/
└── skills/sgft-organizacion-entregables/  [AT] (rev: DG)  esta skill versionada: fuente única del mapa (DEC-16)

.github/
├── CODEOWNERS                        [AT] (rev: DG)  generado con --codeowners --salida; copia en assets/repo/ (DEC-10, DEC-16)
├── pull_request_template.md          [AT] (rev: DG)  checklist del autor y del integrador; copia en assets/repo/
└── workflows/                        [JB] (rev: JH)  WBS 5.1; job Playwright (4.6) lo aporta YE
```

## 11. Lectura por capas: qué toca cada quien dentro de una misma app

Para cualquier app con interfaz, el reparto es siempre el mismo patrón; solo cambian los nombres:

| Capa | Archivo | accounts | inventory | pos | reports |
|---|---|---|---|---|---|
| Datos | `models.py`, `migrations/` | JH | JH | JH | — |
| Regla de negocio | `services*.py` | DG | DG (⟂ `deduct_for_sale` JH) | JH | JB (⟂ `cash_close` JH) |
| HTTP | `views.py`, `urls.py` | DG | DG | JB (⟂ sync JH+JB) | JB |
| Presentación | `templates/<app>/` + `partials/` | YE | YE | AT{+YE} (salvo `review/` y `cash_session_close.html`: YE) | YE |
| Prueba unitaria | `tests.py` | DG | DG (+JH) | JB (+JH) | JB (+JH) |
| Prueba E2E | `tests_e2e/` | — | — | YE{+JB} | YE{+JB} |

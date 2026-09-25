# Matriz WBS → ubicación → responsables (distribución por capas)

**Base:** `WBS-SGFT.md` Revisión 3 (24-sep-2026). La columna "Responsable(s)" de esa revisión era **sugerida**; esta matriz la reemplaza aplicando la distribución por capas acordada por el equipo, y es la fuente de la **WBS Revisión 4** (DEC-11). Incluye los paquetes nuevos de DEC-07 (3.3.8, 3.4.9, 3.5.7) y DEC-14 (3.1.5), marcados con `🆕`; el código 3.3.2 está retirado (fusionado en 3.3.1, DEC-12). La vista de cocina 3.3.7 está en evaluación (sección 8) y no suma a la carga:

| Integrante | Capa |
|---|---|
| Alejandro Tarín | Frontend |
| Yahir Enríquez | Frontend |
| Jesús Hernández | Backend + base de datos |
| Diego Galindo | Backend |
| Jared Beltrán | Backend |

**Cómo leer las columnas:** *Dueño* aprueba y responde por el entregable. *Pareja / colabora* escribe parte del entregable. *Revisor* debe aprobar el PR aunque no escriba código. *Cambio* compara contra la Rev. 3: `=` sin cambio · `Δ` cambió el responsable · `+` se agregó alguien · `📍` ubicación que la Rev. 3 no definía (aprobada, DEC-09) · `🆕` paquete nuevo (DEC-07).

Cuando un paquete tiene parte backend y parte frontend, se lista en dos renglones con el sufijo **(B)** y **(F)**.

## Contenido

1. Documentación y especificación técnica
2. Diseño de interfaz (UI/UX)
3.1 M-USR · 3.2 M-INV · 3.3 M-PDV · 3.4 Offline · 3.5 M-REP
4. Control de calidad
5. Integración, CI/CD y despliegue
6. Resumen de cambios frente a la Rev. 3 y su justificación
7. Carga resultante por integrante

---

## 1. Documentación y especificación técnica

Los paquetes de documentación no forman parte de la división backend/frontend; se conservan los responsables de la Rev. 3 salvo donde se indica.

| WBS | Paquete | Ubicación del entregable | Dueño | Pareja / colabora | Revisor | Cambio |
|---|---|---|---|---|---|---|
| 1.1.1 | Propósito, alcance y visión general | `docs/SRS.md` §1 | Diego | — | Tarín | = |
| 1.1.2 | Definiciones, acrónimos y LEL | `docs/SRS.md` §1 | Diego | — | Tarín | = |
| 1.2.1 | Perspectiva del producto | `docs/SRS.md` §2 | Diego | — | Yahir | = |
| 1.2.2 | Funciones del producto | `docs/SRS.md` §2 | Diego | — | Yahir | = |
| 1.2.3 | Características del usuario | `docs/SRS.md` §2 | Diego | — | Yahir | = |
| 1.2.4 | Restricciones | `docs/SRS.md` §2 | Diego | — | Tarín | = |
| 1.2.5 | Suposiciones y dependencias | `docs/SRS.md` §2 | Diego | — | Tarín | = |
| 1.3.1 | Catálogo formal de requisitos | `docs/SRS.md` §3 | Diego | Jesús | — | = |
| 1.4.1 | Diagrama de procesos propuesto | `docs/diagramas/procesos/` + Apéndice A del SRS | Diego | — | Jesús (consistencia con SADT) | 📍 |
| 1.5.1 | Diagramas SADT del sistema | `docs/diagramas/*.drawio` + PNG/PDF | Jesús | — | Diego | = |
| 1.6.1 | Diagrama ER y diccionario de datos | `docs/diagramas/` + Apéndice C del SRS | Jesús | — | Diego | 📍 |
| 1.7 | Manual de usuario | `docs/manual-usuario.md` (si es Word: espacio compartido, no el repo) | Diego | Tarín, Yahir | — | + Yahir |

## 2. Diseño de interfaz (UI/UX)

| WBS | Paquete | Ubicación del entregable | Dueño | Pareja / colabora | Revisor | Cambio |
|---|---|---|---|---|---|---|
| 2.1 | Estructura base del sistema (app) | `apps/core/templates/base.html`, `docs/decisiones/convencion-htmx-alpine-SGFT.md` | Tarín | — | Yahir | Δ `apps/core/mixins.py` sale de 2.1 y queda solo en 3.1.3 (Jesús) |
| 2.2.1 | Mockup M-PDV (venta) | `docs/prototipos/pdv-venta/index.html` | Tarín | — | — | = |
| 2.2.2 | Mockup M-USR (inicio de sesión) | `docs/prototipos/usr-acceso/index.html` | Yahir | — | Tarín | Δ antes Tarín |
| 2.2.3 | Mockup M-INV (inventario) | `docs/prototipos/inv-catalogo/index.html` | Yahir | — | Tarín | Δ antes Tarín |
| 2.2.4 | Mockup M-REP (caja/reportes) | `docs/prototipos/rep-caja/index.html` | Yahir | Tarín (pantallas de turno) | Tarín | Δ antes Tarín |

## 3.1 Módulo M-USR — Inicio de sesión

| WBS | Paquete | Ubicación del entregable | Dueño | Pareja / colabora | Revisor | Cambio |
|---|---|---|---|---|---|---|
| 3.1.1 | Modelo de usuario y rol | `apps/accounts/models.py` + `migrations/` | Jesús | — | Diego | = |
| 3.1.2 (B) | Autenticación — backend | `apps/accounts/services.py`, `views.py`, `urls.py` | Diego | — | Jesús | Δ antes Jesús + Jared |
| 3.1.2 (F) | Autenticación — plantilla | `apps/accounts/templates/accounts/login.html` | Yahir | — | Tarín | + |
| 3.1.3 | RBAC por rol | `apps/core/mixins.py`; aplicado por cada dueño de `views.py` | Jesús | Diego, Jared (aplican) | — | = |
| 3.1.4 | Pruebas unitarias M-USR | `apps/accounts/tests.py` | Diego | — | Jared | Δ antes Jared |
| 3.1.5 (B) | Administración de cuentas de personal | `apps/accounts/services.py` (`create_user`, `change_role`, desactivación), `views.py`, `urls.py` | Diego | — | Jesús | 🆕 (DEC-14) |
| 3.1.5 (F) | Administración de cuentas — pantallas | `apps/accounts/templates/accounts/partials/` | Yahir | — | Tarín | 🆕 (DEC-14) |

## 3.2 Módulo M-INV — Catálogo, recetas e inventario

| WBS | Paquete | Ubicación del entregable | Dueño | Pareja / colabora | Revisor | Cambio |
|---|---|---|---|---|---|---|
| 3.2.1 (B-datos) | Catálogo de platillos y precios — modelo | `apps/catalog/models.py` (`Dish`) | Jesús | — | Diego | = |
| 3.2.1 (B) | Catálogo de platillos y precios — administración | `apps/catalog/admin.py` | Diego | — | Jesús | + Diego |
| 3.2.2 | Catálogo de insumos | `apps/catalog/models.py` (`Ingredient`, Jesús) + `admin.py` (Diego) | Jesús | Diego | — | + Diego |
| 3.2.3 | Definición de recetas | `apps/catalog/models.py` (`Recipe`, Jesús) + inline en `admin.py` (Diego) | Jesús | Diego | — | + Diego |
| 3.2.4 | Niveles mínimos de stock | campo `min_stock` en `models.py` | Jesús | — | Diego | = |
| 3.2.5 (B) | Entrada de insumos comprados | `apps/inventory/services.py` (`register_purchase`), `views.py`, `urls.py` | Diego | — | Jared | Δ antes Jesús |
| 3.2.5 (F) | Entrada de insumos — pantalla | `apps/inventory/templates/inventory/` | Yahir | — | Tarín | + |
| 3.2.6 | Descuento de insumos por venta | `apps/inventory/services.py` (`deduct_for_sale`) | Jesús | — | Diego | = |
| 3.2.7 (B) | Registro de mermas y faltantes | `apps/inventory/services.py` (`register_waste`), `views.py` | Diego | — | Jared | Δ antes Jesús |
| 3.2.7 (F) | Mermas — pantalla | `apps/inventory/templates/inventory/` | Yahir | — | Tarín | + |
| 3.2.8 (B) | Alerta de stock crítico — cálculo | `apps/inventory/services.py` (`check_min_stock`) | Diego | — | Jared | Δ antes Jesús |
| 3.2.8 (F) | Alerta de stock crítico — insignia | `apps/inventory/templates/inventory/partials/stock_alert_badge.html` | Yahir | — | Tarín | Δ antes Tarín |
| 3.2.9 | Pruebas unitarias M-INV | `apps/inventory/tests.py`, `apps/catalog/tests.py` | Diego | Jesús (pruebas de `deduct_for_sale`) | Jared | Δ antes Yahir |

## 3.3 Módulo M-PDV — Punto de venta

| WBS | Paquete | Ubicación del entregable | Dueño | Pareja / colabora | Revisor | Cambio |
|---|---|---|---|---|---|---|
| 3.3.1 (B) | Selección de platillos y armado del pedido — vistas | `apps/pos/views.py` (`dish_list`, `order_builder`, `add_item`, `remove_item`), `urls.py` | Jared | — | Jesús | + Jared; fusiona 3.3.2 (DEC-12) |
| 3.3.1 (F) | Selección de platillos y armado del pedido — pantalla | `apps/pos/templates/pos/order_builder.html`, `partials/dish_list.html` | Tarín | — | Yahir | = |
| 3.3.3 (B-datos) | Aplicar modificadores — modelo | `apps/pos/models.py` (`Modifier`) | Jesús | — | Jared | Δ antes Tarín |
| 3.3.3 (B) | Aplicar modificadores — endpoints | `apps/pos/views.py` | Jared | — | Jesús | + |
| 3.3.3 (F) | Aplicar modificadores — interfaz | `apps/pos/templates/pos/` (+ `partials/`) | Tarín | — | Yahir | = |
| 3.3.4 | Calcular total | `apps/pos/services_pricing.py` (`calcular_total`, DEC-01) | Jesús | — | Tarín | = |
| 3.3.5 (B-regla) | Confirmar venta — servicio | `apps/pos/services.py` (`confirm_sale`) | Jesús | — | Jared | = |
| 3.3.5 (B) | Confirmar venta — vista | `apps/pos/views.py` (`confirm_sale`) | Jared | — | Jesús | + Jared |
| 3.3.5 (F) | Confirmar venta — fragmento | `apps/pos/templates/pos/partials/order_summary.html` | Tarín | — | Yahir, Jared (controles HATEOAS) | = |
| 3.3.6 | Pruebas unitarias M-PDV | `apps/pos/tests.py` (cubre también 3.3.8, y 3.3.7 si se aprueba) | Jared | Jesús (servicios y paridad) | Jesús | = |
| 3.3.8 (B-regla) | Ajuste y cancelación — servicio | `apps/pos/services.py` (`cancel_sale`, `adjust_sale` con motivo; regla 11) + `SaleAdjustment` en `models.py` | Jesús | — | Jared | 🆕 |
| 3.3.8 (B) | Ajuste y cancelación — vista | `apps/pos/views.py` | Jared | — | Jesús | 🆕 |
| 3.3.8 (F) | Ajuste y cancelación — control y formulario | control "Cancelar / ajustar" en `partials/order_summary.html` + formulario de motivo en `apps/pos/templates/pos/` | Tarín | — | Yahir | 🆕 |

## 3.4 Operación offline y sincronización

> Todo paquete de este bloque exige programación en pareja y lectura previa completa de `ADR-02-operacion-offline-SGFT.md`. ADR-02 §6 pide además que el integrante con experiencia en JavaScript no sea el único autor: con Tarín como conductor y Yahir como segundo autor se cumple sin sacar a un backend de su capa.

| WBS | Paquete | Ubicación del entregable | Dueño | Pareja / colabora | Revisor | Cambio |
|---|---|---|---|---|---|---|
| 3.4.1 | PWA shell | `static/pos/manifest.json`, registro de `sw.js` en la plantilla del PDV | Tarín | Yahir | Jared | Δ pareja antes Jared |
| 3.4.2 | Cacheo con Workbox | `static/pos/sw.js` | Tarín | Yahir | Jared | Δ pareja antes Jared |
| 3.4.3 | Almacén local IndexedDB/Dexie | `static/pos/db.js` | Tarín | Yahir | Jared (forma de las colas = contrato de sync) | Δ pareja antes Jared |
| 3.4.4 | Lógica de pedido en cliente | `static/pos/pricing.js`, `x-data` en `apps/pos/templates/pos/` | Tarín | Yahir | Jesús | Δ pareja antes Jared |
| 3.4.5 | Prueba de paridad Python/JS | `tests_fixtures/pricing_cases.json` (JH+AT), `PricingParityTest` en `apps/pos/tests.py` (JH), `tests_e2e/parity/test_pricing.mjs` (AT), job en `.github/workflows/` (JB) | Jesús | Tarín, Jared (job CI) | — | + Jared |
| 3.4.6 | Endpoint POST /pos/sync/ | `apps/pos/views.py` (`sync_operations`) según `docs/decisiones/contrato-sync-pdv.md` v1 + campos nuevos de `Sale` | Jesús | Jared | Tarín (contrato) | 📍 contrato aprobado (DEC-02 a DEC-06) |
| 3.4.7 | Apertura de turno de caja offline (renombrado, DEC-07) | `apps/pos/services_cash_session.py` (JH), cola de aperturas en `static/pos/db.js` y UI de apertura en `apps/pos/templates/pos/` (AT) | Jesús | Tarín | Jared | = |
| 3.4.8 | Pruebas E2E offline | `tests_e2e/test_pos_sale.py`, `tests_e2e/test_cash_session_open.py` | Yahir | Jared | — | = |
| 3.4.9 (B-regla) | Bandeja de revisión — resolución | `apps/pos/services.py` (aplicar con catálogo actual / aplicar sin descontar / descartar; marcar revisado) | Jesús | Jared | — | 🆕 |
| 3.4.9 (B) | Bandeja de revisión — vistas | `apps/pos/views.py` (solo Administrador, en línea) | Jared | Jesús | — | 🆕 |
| 3.4.9 (F) | Bandeja de revisión — pantallas | `apps/pos/templates/pos/review/` | Yahir | — | Tarín | 🆕 |

## 3.5 Módulo M-REP — Caja y reportes

| WBS | Paquete | Ubicación del entregable | Dueño | Pareja / colabora | Revisor | Cambio |
|---|---|---|---|---|---|---|
| 3.5.1 (B-regla) | Abrir turno — servicio | `apps/pos/services_cash_session.py` (`open_session`) | Jesús | — | Jared | = |
| 3.5.1 (B) | Abrir turno — vista | `apps/pos/views.py` (`open_cash_session`) | Jared | — | Jesús | + |
| 3.5.1 (F) | Abrir turno — pantalla | plantilla de apertura en `apps/pos/templates/pos/` + `partials/cash_session_banner.html` | Tarín | — | Yahir | + |
| 3.5.2 (B-regla) | Calcular corte — servicio | `apps/reports/services.py` (`cash_close`; lee el `cash_difference` que registra 3.5.7) | Jesús | — | Jared | = |
| 3.5.2 (B) | Calcular corte — vista | `apps/reports/views.py` | Jared | — | Jesús | + |
| 3.5.2 (F) | Calcular corte — pantalla | `apps/reports/templates/reports/cash_close.html` | Yahir | — | Tarín | + |
| 3.5.3 (B) | Ventas por periodo | `apps/reports/services.py` (`sales_by_period`), `views.py` | Jared | — | Jesús | Δ antes Yahir |
| 3.5.3 (F) | Ventas por periodo — pantalla | `apps/reports/templates/reports/` | Yahir | — | Tarín | = (cambia de capa) |
| 3.5.4 (B) | Productos más vendidos | `apps/reports/services.py` (`top_dishes`), `views.py` | Jared | — | Jesús | Δ antes Yahir |
| 3.5.4 (F) | Más vendidos — pantalla | `apps/reports/templates/reports/` | Yahir | — | Tarín | = (cambia de capa) |
| 3.5.5 (B) | Exportar ventas del día a PDF | `apps/reports/services.py` (`export_daily_sales_pdf`), `views.py` | Jared | — | Jesús | Δ antes Yahir; alcance redefinido (DEC-13) |
| 3.5.5 (F) | Exportar ventas del día — botón | `apps/reports/templates/reports/` | Yahir | — | Tarín | = (cambia de capa) |
| 3.5.6 | Pruebas unitarias M-REP | `apps/reports/tests.py` | Jared | Jesús (pruebas de `cash_close`) | — | Δ antes Yahir |
| 3.5.7 (B-regla) | Cerrar turno — servicio | `apps/pos/services_cash_session.py` (`close_session`: se niega con operaciones pendientes; registra `cash_difference` sin bloquear) | Jesús | — | Jared | 🆕 |
| 3.5.7 (B) | Cerrar turno — vista | `apps/pos/views.py` (`close_cash_session`, solo en línea) | Jared | — | Jesús | 🆕 |
| 3.5.7 (F) | Cerrar turno — pantalla | `apps/pos/templates/pos/cash_session_close.html` + estado en `partials/cash_session_banner.html` (Tarín) | Yahir | Tarín (banner) | Tarín | 🆕 |

**Nota sobre 3.5.5 (DEC-13):** exporta a PDF las ventas de una jornada: detalle de ventas, ajustes con motivo, y totales por método de pago y general. Se atribuye por la marca de tiempo del dispositivo y se niega a generarse con operaciones pendientes de sincronizar (regla 5, como el corte). Es solo para el Administrador. Generar PDF requiere una dependencia nueva que se justifica en el PR (`CLAUDE.md` §11) y aprueba Jesús; se recomienda ReportLab (BSD, sin dependencias del sistema). El paquete aún no tiene RF confirmado.

## 4. Control de calidad

| WBS | Paquete | Ubicación del entregable | Dueño | Pareja / colabora | Revisor | Cambio |
|---|---|---|---|---|---|---|
| 4.1 | Cobertura de pruebas consolidada | `docs/calidad/cobertura-sprint-N.md` + artefacto del job de CI | Jared | Yahir | — | 📍 |
| 4.2 | Revisión de código (PR obligatorio) | Historial de PR; `.github/CODEOWNERS` (con Tarín en todas las rutas), `.github/pull_request_template.md`, rulesets de `main` y revisión de rutas con `--revisar` | Tarín (integrador: aprueba y fusiona) | Dueño de cada ruta (revisión solicitada, no exigida) | Diego (cambios al mapa) | Δ antes Equipo (DEC-16, DEC-18) |
| 4.3 | Matriz de trazabilidad RF → prueba | Apéndice de `docs/SRS.md` | Jesús | — | Diego | = |
| 4.4 | Verificación de seguridad | `docs/calidad/checklist-seguridad.md` | Jesús | — | Diego | 📍 |
| 4.5 | Datos de prueba ficticios | `apps/<app>/fixtures/*.json` | Yahir | — | Jesús (coherencia con modelos) | 📍 |
| 4.6 | Pruebas E2E críticas en CI | Job de Playwright en `.github/workflows/` + `tests_e2e/test_cash_close.py` | Yahir | Jared (workflow) | — | = |

## 5. Integración, CI/CD y despliegue

| WBS | Paquete | Ubicación del entregable | Dueño | Pareja / colabora | Revisor | Cambio |
|---|---|---|---|---|---|---|
| 5.1 | Pipeline de GitHub Actions | `.github/workflows/` | Jared | — | Jesús | Δ antes Jesús |
| 5.2 | Entornos gestionados (PostgreSQL, variables) | `.env.example`, `config/settings.py` (`DATABASE_URL`) | Jesús | — | Jared | = |
| 5.3 | Despliegue en Render/Railway | Archivo del proveedor en la raíz + servicio desplegado | Jesús | Tarín | — | = |
| 5.4 | Spike de validación offline | `docs/decisiones/spike-offline-sprint1.md`; código en rama `spike/offline-workbox` (no se fusiona) | Tarín | Jared | — | 📍 |

## 6. Resumen de cambios frente a la Rev. 3 y su justificación

1. **Todo `models.py` y `migrations/` quedan con Jesús** (se mueve `Modifier` de 3.3.3, antes en Tarín). Motivo: la capa de base de datos se asignó explícitamente a Jesús, y las migraciones de Django concurrentes de varios autores son la fuente más común de conflictos irresolubles en equipos pequeños. Un solo dueño del esquema elimina ese riesgo.
2. **Los servicios de reportes (3.5.3–3.5.6) pasan de Yahir a Jared**, y Yahir conserva la parte visible de esos mismos paquetes. Motivo: Yahir pasó a frontend; así mantiene continuidad con M-REP sin salir de su capa.
3. **Los servicios no transaccionales de M-INV y M-USR (3.1.2, 3.2.5, 3.2.7, 3.2.8) pasan de Jesús a Diego.** Motivo: Jesús concentraba casi todo el backend en la Rev. 3; Diego aporta capacidad backend y se le asignan los módulos de menor riesgo transaccional, mientras Jesús conserva lo que corre dentro de `transaction.atomic()`.
4. **Las vistas de M-PDV pasan a Jared**; los servicios transaccionales de M-PDV (`services.py`, `services_pricing.py`, `services_cash_session.py`) se quedan con Jesús. Motivo: separar HTTP de regla de negocio, tal como lo pide `estructura-y-flujo-datos-SGFT.md` §2.
5. **Las parejas de 3.4.1–3.4.4 pasan de Tarín + Jared a Tarín + Yahir**; Jared queda como revisor de `db.js`. Motivo: son archivos de cliente; con dos integrantes de frontend, la mitigación de ADR-02 §6 se cumple dentro de la capa. Jared revisa `db.js` porque la forma de las colas es el contrato con su endpoint de sincronización.
6. **Mockups 2.2.2–2.2.4 pasan de Tarín a Yahir.** Motivo: quien implementa la plantilla real hace el prototipo desechable (no hay pérdida en la entrega de diseño), y libera a Tarín en el Sprint 1, donde también lleva el spike 5.4 y la base 2.1.
7. **`apps/core/mixins.py` aparecía en 2.1 (Tarín) y en 3.1.3 (Jesús).** Se resuelve a favor de Jesús: es control de acceso en servidor, no presentación.
8. **Pruebas unitarias:** pasan al dueño backend de cada app (quien implementa un servicio escribe su prueba). La independencia de verificación se conserva en 4.1 (Jared + Yahir revisan cobertura de todos) y en 4.2 (nadie aprueba su propio PR).
9. **5.1 (CI) pasa de Jesús a Jared** para equilibrar la carga de Jesús, que conserva 5.2 y 5.3.
10. **Paquetes nuevos (DEC-07).** Siguen el mismo reparto por capas: regla transaccional para Jesús, vista para Jared y pantalla para frontend. La pantalla de ajuste queda con Tarín, por vivir en el flujo del cajero; la vista de cocina (3.3.7) también, si se aprueba. La bandeja de revisión y el cierre de turno, que son solo en línea y del Administrador, van con Yahir, que ya lleva las pantallas administrativas y el mockup 2.2.4; así no se recarga a Tarín. Las pruebas de los paquetes nuevos entran en `pos/tests.py` (3.3.6).

11. **Ajustes del mismo día (DEC-12 a DEC-14).** 3.3.1 absorbe 3.3.2 con los mismos responsables. 3.5.5 queda como exportación a PDF de las ventas del día, con el mismo reparto: servicio de Jared y botón de Yahir. 3.1.5, administración de cuentas, sigue el reparto de M-USR: backend de Diego y pantallas de Yahir.

12. **Tarín como integrador (DEC-16).** Tarín valida las rutas y es el único que fusiona en `main`; los code owners siguen aprobando el contenido. Pasan de Diego a Tarín la estructura del repositorio (CODEOWNERS, plantilla de PR, la skill versionada y las rutas sin regla) y las acciones de configuración P1 a P3. Diego queda como segundo aprobador de esos cambios, por su impacto en los responsables del WBS.

13. **Tarín aprueba todos los PR (DEC-18).** Tarín pasa a figurar en todas las rutas de `CODEOWNERS`, así que su aprobación basta para cualquier archivo. Los dueños siguen recibiendo la solicitud de revisión, pero ya no es obligatoria. Sus propios PR los aprueba otra persona de la ruta.

## 7. Carga resultante por integrante

Conteo de renglones de las secciones 1 a 5 de esta matriz donde la persona aparece como dueño (D), pareja/colaborador (P) o revisor (R). Es un indicador de reparto, no una estimación de horas (el WBS aún no tiene estimación).

| Integrante | D | P | R | Observación |
|---|---|---|---|---|
| Jesús | 24 | 5 | 18 | Mayor carga y mayor concentración de conocimiento (esquema, transacciones, sync). Mitigación: todo su código transaccional tiene revisor y el sync es en pareja. En un borrador previo figuraba como revisor en 26 renglones; se movieron las revisiones de bajo riesgo (secciones descriptivas del SRS a Tarín/Yahir, servicios no transaccionales de inventario a Jared) para que la revisión no se vuelva cuello de botella. |
| Diego | 18 | 3 | 9 | Doble función PO/analista + backend M-USR/M-INV. Vigilar en el Sprint Planning que la documentación no desplace sus entregables de backend. |
| Jared | 15 | 7 | 17 | Backend M-PDV (vistas) y M-REP, CI; revisor natural del contrato de sincronización y del backend de Diego. |
| Tarín | 13 | 6 | 20 | Scrum Master + integrador (aprueba y fusiona todos los PR; carga de revisión alta: todo el repositorio pasa por él) + frontend M-PDV + conductor del módulo offline. Sus revisiones son sobre todo de plantillas de Yahir (coherencia visual con `base.html`), de bajo costo; si en la práctica la frenan, Yahir y Tarín pueden alternarse como revisores entre sí por Sprint. |
| Yahir | 17 | 6 | 9 | Frontend M-USR/M-INV/M-REP, E2E y datos demo; segundo autor del módulo offline. |

## 8. Paquetes en evaluación (fuera de la línea base, no suman a la carga)

| WBS | Paquete | Ubicación del entregable | Dueño | Pareja / colabora | Revisor | Estado |
|---|---|---|---|---|---|---|
| 3.3.7 (B-datos) | Consulta de cocina — estado "preparado" | `apps/pos/models.py` (`Order.status`) | Jesús | — | Diego | ⏸ en evaluación (DEC-15) |
| 3.3.7 (B) | Consulta de cocina — vistas | `apps/pos/views.py` (`kitchen_queue`, `mark_prepared`) | Jared | — | Jesús | ⏸ en evaluación (DEC-15) |
| 3.3.7 (F) | Consulta de cocina — pantalla | `apps/pos/templates/pos/kitchen_queue.html`, `partials/kitchen_order.html`; lectura de la cola local en `static/pos/db.js` sin conexión | Tarín | Yahir (parte offline) | Yahir | ⏸ en evaluación (DEC-15) |

La vista de cocina es una sección más de la app, como Punto de venta o Inventario. El equipo aún no decide si se implementará (DEC-15), así que sus rutas y responsables quedan reservados, pero sus archivos no se crean. Si se aprueba, las tres filas vuelven a la sección 3.3 y se recalcula la sección 7. Si se descarta, el cambio de alcance debe decidir también qué pasa con el rol de Cocinero (ver supuesto 9 del WBS).

Si el equipo ajusta un responsable, se cambia en `assets/ownership.json`, se corre `python scripts/dueno_de_ruta.py --verificar`, se regenera CODEOWNERS y se actualiza esta tabla y la columna de responsables del WBS en el mismo PR.

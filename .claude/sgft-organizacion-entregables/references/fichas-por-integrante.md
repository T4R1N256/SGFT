# Fichas por integrante

Cada ficha responde cinco preguntas: qué archivos posee, qué escribe dentro de archivos de otros, con quién trabaja en pareja, qué revisa y qué no debe tocar sin PR del dueño. La lista completa y siempre actualizada se obtiene con:

```bash
python scripts/dueno_de_ruta.py --persona <diego|jesus|jared|tarin|yahir>
```

## Contenido

1. Jesús Hernández — Backend + base de datos
2. Diego Galindo — Backend (y PO / analista)
3. Jared Beltrán — Backend
4. Alejandro Tarín — Frontend (y Scrum Master)
5. Yahir Enríquez — Frontend
6. Puntos de coordinación obligatoria entre capas

---

## 1. Jesús Hernández — Backend + base de datos

**Responsabilidad central:** el esquema de datos y todo lo que corre dentro de `transaction.atomic()`. Es el único que genera migraciones.

**Dueño de**
- Todos los `apps/*/models.py` y `apps/*/migrations/` (3.1.1, 3.2.1–3.2.4, modelos de `pos` incluidos `Modifier`, `CashRegisterSession`, `QuarantinedSale`, `QuarantinedCashSession`).
- `apps/pos/services.py`: `confirm_sale` (3.3.5), `cancel_sale` / `adjust_sale` con motivo (3.3.8, regla 11) y la resolución de cuarentena y revisiones (3.4.9).
- `apps/pos/services_pricing.py`: `calcular_total()` (3.3.4, nombres en español por DEC-01).
- `apps/pos/services_cash_session.py`: `open_session`, `close_session`, `current_session` (3.5.1, 3.4.7, 3.5.7).
- En `models.py`, lo que exigen los paquetes nuevos: estado "preparado" de `Order` (3.3.7, ⏸ solo si se aprueba), `SaleAdjustment` (3.3.8) y los campos de `Sale` del contrato de sincronización (total cobrado, total del servidor, indicador de diferencia, dos marcas de tiempo, UUID único).
- `apps/core/mixins.py` — RBAC (3.1.3).
- `config/`, `manage.py`, `requirements.txt`, `.env.example`, `.gitignore` (5.2); despliegue (5.3, con Tarín).
- `tests_fixtures/pricing_cases.json` (3.4.5, codueño con Tarín).
- `docs/diagramas/` (1.5.1, 1.6.1), `docs/decisiones/contrato-sync-pdv.md` v1 y `nombres-modulo-precios.md`, `docs/calidad/checklist-seguridad.md` (4.4), matriz de trazabilidad en `docs/SRS.md` (4.3).

**Escribe dentro de archivos ajenos**
- `apps/inventory/services.py` → `deduct_for_sale()` (3.2.6) — dueño del archivo: Diego.
- `apps/reports/services.py` → `cash_close(session)` (3.5.2) — dueño: Jared.
- `apps/pos/views.py` → `sync_operations()` en pareja con Jared (3.4.6) — dueño: Jared.
- Las pruebas de esas funciones en los `tests.py` correspondientes, más `PricingParityTest`.

**Pareja:** Jared en el endpoint de sincronización (3.4.6) y en la bandeja de revisión (3.4.9); Tarín en la paridad de precios y en la apertura de turno offline.

**Revisa:** las vistas de Jared (llaman a sus servicios), el backend de autenticación de Diego (seguridad), `pricing.js` (espejo de su `services_pricing.py`), plantillas-tag de Tarín (que no calculen dinero), fixtures demo de Yahir (coherencia con los modelos), workflows de CI.

**Cómo recibe pedidos de otros:** cualquier campo nuevo lo solicita el interesado con un issue o un PR a `models.py` que Jesús aprueba; Jesús genera la migración. Nadie más corre `makemigrations` sobre la rama principal.

---

## 2. Diego Galindo — Backend (y PO / analista)

**Responsabilidad central:** backend de M-USR y M-INV fuera de la transacción de venta, más la documentación formal del SRS y el mantenimiento del mapa de propiedad.

**Dueño de**
- `apps/accounts/` salvo modelos y plantillas: `services.py`, `views.py`, `urls.py`, `admin.py`, `tests.py` (3.1.2, 3.1.4, y 3.1.5 administración de cuentas: alta, cambio de rol y desactivación).
- `apps/catalog/admin.py` y `tests.py` (3.2.1–3.2.3, 3.2.9) — la interfaz del catálogo es Django Admin.
- `apps/inventory/` salvo modelos y plantillas: `services.py` (`register_purchase`, `register_waste`, `check_min_stock`), `views.py`, `urls.py`, `tests.py` (3.2.5, 3.2.7, 3.2.8, 3.2.9).
- `docs/SRS.md` (1.1.1–1.3.1), `docs/diagramas/procesos/` (1.4.1), `docs/manual-usuario.md` (1.7), `docs/entregas/`, `docs/decisiones/` (salvo los documentos técnicos de Jesús y el de organización, que lleva Tarín), `CLAUDE.md`.
- Las acciones P4 a P6 de `decisiones-y-pendientes.md`: corregir `CLAUDE.md`, `estructura-y-flujo-datos` y `revision-tecnica`, y publicar la WBS Rev. 4 (también en Word).
- Es segundo aprobador de CODEOWNERS, de la plantilla de PR, de la skill y de las rutas sin regla: revisa los cambios del integrador que alteran responsables del WBS.

**Pareja / colabora:** Jesús en el catálogo de requisitos (1.3.1); Tarín y Yahir en el manual.

**Revisa:** modelos de `accounts` y `catalog` (que reflejen el SRS), `deduct_for_sale()` cuando Jesús la modifica (Diego es dueño del archivo), diagramas de Jesús contra el SRS.

**Cuidado:** `inventory` nunca importa de `pos`. Si una función de inventario "necesita saber de la venta", la está pidiendo el lugar equivocado.

---

## 3. Jared Beltrán — Backend

**Responsabilidad central:** la capa HTTP de M-PDV y M-REP, los servicios de reportes y la integración continua.

**Dueño de**
- `apps/pos/views.py`, `urls.py`, `tests.py` y el Python no transaccional de `pos` (3.3.1–3.3.3, 3.3.5 vista, 3.3.6, 3.5.1 vista), más las vistas de los paquetes nuevos: `kitchen_queue` / `mark_prepared` (3.3.7, ⏸ solo si se aprueba), cancelar / ajustar (3.3.8), bandeja de revisión (3.4.9, en pareja con Jesús) y `close_cash_session` (3.5.7).
- `apps/reports/services.py` (`sales_by_period`, `top_dishes`, `export_daily_sales_pdf` — ventas del día a PDF, DEC-13), `views.py`, `urls.py`, `tests.py` (3.5.3–3.5.6, 3.5.2 vista).
- `.github/workflows/` (5.1; incluye el job de `node --test` de 3.4.5).
- `docs/calidad/cobertura-sprint-N.md` (4.1, con Yahir).

**Pareja:** Jesús en `sync_operations()` (3.4.6) y en la bandeja de revisión (3.4.9); Yahir en E2E offline (3.4.8); Tarín en el spike offline (5.4).

**Revisa:** `static/pos/db.js` (la forma de las colas es su contrato de sincronización), servicios de Jesús que sus vistas consumen, backend de inventario de Diego, pruebas de M-USR y M-INV, y el fragmento `order_summary.html` (controles HATEOAS según el estado que su vista entrega).

**Regla de sus vistas:** validan rol con el mixin de Jesús, verifican turno de caja abierto cuando aplica, eligen plantilla completa o fragmento con `request.htmx`, llaman al servicio y renderizan. Ninguna regla de negocio vive en la vista.

---

## 4. Alejandro Tarín — Frontend, Scrum Master e integrador

**Responsabilidad central:** la base visual de todo el sistema, la interfaz del punto de venta y el cliente offline. Además, como **integrador** (DEC-16, DEC-18), aprueba todos los PR, valida que sus rutas estén en la estructura aprobada y es el único que fusiona en `main`.

**Como integrador**
- Revisa cada PR con `--revisar` o con el job de CI y resuelve los bloqueos: una ruta fuera de la estructura se ubica en `assets/ownership.json` (con Diego como segundo aprobador) o se mueve.
- Revisa el contenido, aprueba y, con el CI en verde, fusiona. Figura en todas las rutas de `CODEOWNERS`, así que su aprobación basta para cualquier archivo. Los dueños reciben la solicitud de revisión, pero su aprobación ya no se exige.
- Es dueño de `.github/CODEOWNERS`, `.github/pull_request_template.md`, `.claude/skills/` (la skill versionada), `docs/decisiones/organizacion-repositorio.md` y de toda ruta sin regla.
- Tiene a su cargo las acciones P1 a P3: copiar el kit, dar permisos y configurar los dos rulesets de `main`. Debe ser el único administrador del repositorio.
- Sus propios PR los aprueba otra de las personas listadas en la ruta (normalmente Yahir en frontend; Diego o Jesús en documentación), porque GitHub no deja aprobar el PR propio.

**Dueño de**
- `apps/core/templates/base.html` y `apps/core/templatetags/` (2.1).
- `apps/pos/templates/pos/` salvo `review/` y `cash_session_close.html`: `order_builder.html`, `partials/dish_list.html`, `partials/order_summary.html` (con el control "Cancelar / ajustar" y su formulario de motivo, 3.3.8), `partials/cash_session_banner.html`, pantalla de apertura de turno (3.3.1–3.3.5, 3.5.1), y, si se aprueba 3.3.7 (⏸ en evaluación, DEC-15), la vista de cocina `kitchen_queue.html` + `partials/kitchen_order.html` (sin red lee la cola local, en pareja con Yahir).
- `static/pos/` completo — `manifest.json`, `sw.js`, `db.js`, `pricing.js` (3.4.1–3.4.4) — siempre en pareja con Yahir.
- `tests_e2e/parity/test_pricing.mjs` (3.4.5), `tests_fixtures/pricing_cases.json` (codueño con Jesús).
- `docs/decisiones/convencion-htmx-alpine-SGFT.md` (2.1), `docs/prototipos/pdv-venta/` (2.2.1), `docs/decisiones/spike-offline-sprint1.md` (5.4), `static/core/` si llegara a existir CSS propio.

**Pareja:** Yahir en todo `static/pos/` y en las plantillas con `x-data` offline; Jesús en paridad y apertura offline; Jared en el spike.

**Revisa:** los mockups y todas las plantillas de Yahir (coherencia visual con `base.html`; son revisiones de presentación, ligeras), y `services_pricing.py` (espejo de su `pricing.js`).

**Regla de dinero en sus plantillas:** en línea, el total se muestra tal como llega del servidor. Sin conexión, el único cálculo permitido es el de `pricing.js`, en enteros de centavos y cubierto por la prueba de paridad. Alpine nunca calcula dinero por su cuenta.

---

## 5. Yahir Enríquez — Frontend

**Responsabilidad central:** la interfaz de M-USR, M-INV y M-REP, las pruebas de extremo a extremo y los datos demo.

**Dueño de**
- `apps/accounts/templates/accounts/` (`login.html` 3.1.2; `partials/` de administración de cuentas 3.1.5).
- `apps/inventory/templates/inventory/` incluido `partials/stock_alert_badge.html` (3.2.5, 3.2.7, 3.2.8).
- `apps/reports/templates/reports/` incluido `cash_close.html` y el botón "Exportar ventas del día (PDF)" (3.5.2–3.5.5).
- En `apps/pos/templates/pos/`: la bandeja de revisión del Administrador `review/` (3.4.9) y la pantalla de cierre de turno `cash_session_close.html` (3.5.7). Son pantallas solo en línea y de administración, como las demás que lleva.
- `tests_e2e/` (3.4.8, 4.6) salvo `parity/`.
- `apps/<app>/fixtures/` — datos demo ficticios coherentes con el menú real (4.5).
- `docs/prototipos/usr-acceso/`, `inv-catalogo/`, `rep-caja/` (2.2.2–2.2.4).

**Pareja:** Tarín en todo `static/pos/` (segundo autor obligatorio, ADR-02 §6) y, si se aprueba 3.3.7, en la parte offline de la vista de cocina; Jared en las E2E offline.

**Revisa:** `base.html` y plantillas del PDV de Tarín; secciones descriptivas del SRS (1.2.1–1.2.3).

**Coordinación especial:** su mockup 2.2.4 incluye apertura y cierre de turno. La apertura la implementa Tarín, porque debe funcionar sin conexión; el cierre lo implementa Yahir, porque es solo en línea. El indicador de estado del turno (`cash_session_banner.html`) es de Tarín y refleja ambos.

---

## 6. Puntos de coordinación obligatoria entre capas

| Costura | Lado A | Lado B | Artefacto que los une | Dónde se documenta |
|---|---|---|---|---|
| Vista ↔ plantilla (todas las apps) | Dueño de `views.py` (DG / JB) | Dueño de `templates/` (AT / YE) | Contrato vista–plantilla en el docstring de la vista | `contrato-vista-plantilla.md` |
| Servicio ↔ vista en `pos` y `reports` | Jesús (servicio) | Jared (vista) | Firma y excepciones del servicio | Docstring del servicio |
| Precios en línea ↔ offline | Jesús (`calcular_total`) | Tarín (`calcularTotal`) | `tests_fixtures/pricing_cases.json` | Prueba de paridad (3.4.5); nombres en DEC-01 |
| Cola local ↔ sincronización | Tarín + Yahir (`db.js`) | Jesús + Jared (`sync_operations`) | Lote único con `tipo`, llaves en español, 200 con estado por UUID | `docs/decisiones/contrato-sync-pdv.md` v1 (aprobado) |
| Venta ↔ inventario | Jesús (`confirm_sale`) | Jesús (`deduct_for_sale`, en archivo de Diego) | Misma `transaction.atomic()` | `estructura-y-flujo-datos-SGFT.md` §5 |
| Modelo ↔ todos | Jesús | Cualquiera que necesite un campo | Issue o PR a `models.py` aprobado por Jesús | Historial del PR |
| Todo PR ↔ `main` | Autor (dueño avisado por CODEOWNERS) | Tarín, integrador (aprueba y fusiona) | `--revisar`, CODEOWNERS y rulesets de `main` | `organizacion-repositorio.md` (DEC-16, DEC-18) |

# WBS (EDT) — Sistema de Gestión de Food Truck (SGFT)

**Elaborado por:** analista de sistemas (asistido por IA).
**Fecha:** 4 de octubre de 2026. **Revisión 5**, reconstruida a partir del diagrama de la WBS del equipo.
**Estado:** borrador para validación. Las decisiones que tomé donde el diagrama era ambiguo están en la sección 4; no se incluye cronograma ni estimación de horas.

**Cómo leer los responsables:**

- _(modelo)_ o _(servicio)_: capa de datos y reglas transaccionales;
- _(B)_: vistas y servicios no transaccionales;
- _(F)_: plantillas, cliente y diseño.

En todos los casos, Alejandro Tarín aprueba y fusiona los Pull Requests.

## Cambios frente a la Revisión 4

1. **Rama 1** pasa a llamarse **"Herramientas técnicas"** y conserva solo 1.6 (Apéndice C, modelo de datos). Salen 1.1 a 1.5 y el manual de usuario (1.7). La numeración 1.6 se mantiene como en el diagrama.
2. **Rama 2.2** pasa de "mockups" a **"Interfaces de pantalla"**, y su orden cambia:
   - 2.2.1 es M-USR, con acceso por PIN;
   - 2.2.2 es M-PDV.

   El entregable son las pantallas de alta fidelidad en Figma con el sistema de diseño PuntoVenta.

3. **3.3.1 "Selección de platillos" y 3.3.2 "Armar pedido"** vuelven a ser paquetes separados. Esto revierte la fusión de la Revisión 4 (DEC-12).
4. **El diagrama no incluye cuatro paquetes de la Revisión 4 que están dentro del alcance.** Su trabajo se integra en el paquete más cercano (duda 4):

   | Paquete de la Rev. 4                        | Se integra en                                          |
   | ------------------------------------------- | ------------------------------------------------------ |
   | 3.1.5 Administración de cuentas             | 3.1.1                                                  |
   | 3.3.8 Ajuste y cancelación de venta         | 3.3.5                                                  |
   | 3.4.9 Bandeja de revisión del Administrador | 3.4.6                                                  |
   | 3.5.7 Cerrar turno de caja                  | 3.4.7, cuyo nombre en el diagrama ya incluye el cierre |

5. **3.3.7 (vista de cocina)** sale de la WBS. Queda registrada como supuesto, en evaluación.
6. **Rama 3.5 renumerada:** 3.5.4 Productos más vendidos, 3.5.5 Exportar reportes y 3.5.6 Pruebas unitarias M-REP. El diagrama repetía el código 3.5.5.
7. **5.3:** el despliegue es **solo en Railway**.
8. **Endpoint de sincronización:** se nombra `POST /pos/sync/`, por el renombrado de la app (DEC-17), aunque el diagrama dice `/pdv/`.
9. **Entregables documentales sin rutas `docs/`:** el repositorio no contiene el SRS ni los documentos de decisiones (DEC-22).
10. **El spike offline (5.4)** usa la convención de ramas vigente (DEC-23): `tarin/spike-offline`.

## 1. Esquema jerárquico

```
SGFT
1. Herramientas técnicas
   1.6 Apéndice C — Modelo de datos
       1.6.1 Diagrama entidad-relación y diccionario de datos
2. Diseño de interfaz (UI/UX)
   2.1 Estructura base del sistema (app)
   2.2 Interfaces de pantalla
       2.2.1 Interfaz de M-USR (acceso con PIN)
       2.2.2 Interfaz de M-PDV (punto de venta)
       2.2.3 Interfaz de M-INV (inventario/productos)
       2.2.4 Interfaz de M-REP (caja/reportes)
3. Desarrollo del sistema
   3.1 Módulo M-USR — Inicio de sesión
       3.1.1 Modelo de usuario y rol
       3.1.2 Autenticación de usuario
       3.1.3 RBAC por rol
       3.1.4 Pruebas unitarias M-USR
   3.2 Módulo M-INV — Catálogo, recetas e inventario
       3.2.1 Catálogo de platillos y precios
       3.2.2 Catálogo de insumos
       3.2.3 Definición de recetas
       3.2.4 Niveles mínimos de stock
       3.2.5 Entrada de insumos comprados
       3.2.6 Descuento de insumos por venta
       3.2.7 Registro de mermas y faltantes
       3.2.8 Alerta de stock crítico
       3.2.9 Pruebas unitarias M-INV
   3.3 Módulo M-PDV — Punto de venta
       3.3.1 Selección de platillos
       3.3.2 Armar pedido
       3.3.3 Aplicar modificadores
       3.3.4 Calcular total
       3.3.5 Confirmar venta
       3.3.6 Pruebas unitarias M-PDV
   3.4 Operación offline y sincronización
       3.4.1 PWA shell (manifest + registro del service worker)
       3.4.2 Cacheo de la aplicación con Workbox
       3.4.3 Almacén local IndexedDB/Dexie
       3.4.4 Lógica de pedido en cliente (Alpine.js)
       3.4.5 Prueba de paridad de precios Python/JS
       3.4.6 Endpoint de sincronización POST /pos/sync/
       3.4.7 Apertura/cierre de turno de caja offline
       3.4.8 Pruebas E2E offline (Playwright)
   3.5 Módulo M-REP — Caja y reportes (A5)
       3.5.1 Abrir turno de caja
       3.5.2 Calcular corte de caja
       3.5.3 Reporte de ventas por periodo
       3.5.4 Productos más vendidos
       3.5.5 Exportar reportes
       3.5.6 Pruebas unitarias M-REP
4. Control de calidad
   4.1 Cobertura de pruebas unitarias consolidada
   4.2 Revisión de código
   4.3 Matriz de trazabilidad de requisitos a casos de prueba
   4.4 Verificación de seguridad
   4.5 Datos de prueba ficticios y coherentes con el menú real
   4.6 Pruebas E2E críticas (venta PDV, corte de caja)
5. Integración, CI/CD y despliegue
   5.1 Pipeline de GitHub Actions
   5.2 Entornos gestionados (PostgreSQL Neon/Supabase, variables de entorno)
   5.3 Despliegue en Railway
   5.4 Spike de validación offline
```

## 2. Diccionario del WBS

> Columnas: Código | Nombre | Descripción | Entregable verificable | RF/RNF | Responsable(s) | Dependencias

### 1. Herramientas técnicas

| Código | Nombre                                           | Descripción                                                                                                                                                                     | Entregable verificable                                   | RF/RNF | Responsable(s)  | Dependencias                                              |
| ------ | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ------ | --------------- | --------------------------------------------------------- |
| 1.6.1  | Diagrama entidad-relación y diccionario de datos | Formalizar el modelo de datos como diagrama ER y diccionario de campos y tipos. Incluye `User` con rol y PIN, catálogo, inventario, venta, ajustes, cuarentena y turno de caja. | Diagrama ER y diccionario de datos (Apéndice C del SRS). | —      | Jesús Hernández | Ninguna (requisitos y SADT ya cerrados fuera de esta WBS) |

### 2. Diseño de interfaz (UI/UX)

| Código | Nombre                                   | Descripción                                                                                                                                                                                                                                                  | Entregable verificable                                                           | RF/RNF | Responsable(s)  | Dependencias |
| ------ | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- | ------ | --------------- | ------------ |
| 2.1    | Estructura base del sistema (app)        | Plantilla base compartida (Bootstrap, HTMX y Alpine por CDN, token CSRF en `hx-headers`) con los tokens del sistema de diseño PuntoVenta, más la convención de integración HTMX/Alpine: `partials/`, nombres de vistas por acción, contrato vista–plantilla. | `apps/core/templates/base.html` y convención HTMX/Alpine acordada por el equipo. | RES-04 | Alejandro Tarín | Ninguna      |
| 2.2.1  | Interfaz de M-USR (acceso con PIN)       | Diseño del acceso del personal y del modal de PIN de administrador que desbloquea los módulos protegidos (Productos, Inventario, Caja y Reportes), incluido el candado del menú lateral.                                                                     | Pantallas en el archivo de Figma del SGFT, con el sistema PuntoVenta.            | A1     | Alejandro Tarín | 2.1          |
| 2.2.2  | Interfaz de M-PDV (punto de venta)       | Diseño del panel principal y de la pantalla de nueva venta: selección de platillos, ticket, modificadores, cobro y estado de sincronización.                                                                                                                 | Pantallas «Panel principal» y «Nueva venta» en Figma.                            | A3     | Alejandro Tarín | 2.1          |
| 2.2.3  | Interfaz de M-INV (inventario/productos) | Diseño del catálogo de platillos, del inventario de insumos y de las alertas de stock.                                                                                                                                                                       | Pantallas «Productos» e «Inventario» en Figma.                                   | A2, A4 | Yahir Enríquez  | 2.1          |
| 2.2.4  | Interfaz de M-REP (caja/reportes)        | Diseño de la apertura y el cierre de turno, el corte de caja y los reportes, incluido «Exportar PDF».                                                                                                                                                        | Pantallas «Caja» y «Reportes» en Figma.                                          | A5     | Yahir Enríquez  | 2.1          |

### 3.1 Módulo M-USR — Inicio de sesión

| Código | Nombre                   | Descripción                                                                                                                                                                                                                                                   | Entregable verificable                                                                                                        | RF/RNF | Responsable(s)                                                                               | Dependencias |
| ------ | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------- | ------------ |
| 3.1.1  | Modelo de usuario y rol  | `User` como `AbstractUser` con `role` (`admin` / `cashier`) y PIN guardado con hash. Incluye la administración de cuentas por el Administrador: alta, cambio de rol y de PIN, y desactivación sin borrado, para conservar la autoría de ventas y movimientos. | `apps/accounts/models.py` + migración; `apps/accounts/services.py` (`create_user`, `change_role`); administración de cuentas. | A1     | Jesús Hernández (modelo) + Diego Galindo (B, administración de cuentas) + Yahir Enríquez (F) | 1.6.1        |
| 3.1.2  | Autenticación de usuario | Inicio y cierre de sesión del personal, y verificación del PIN de administrador antes de entrar a los módulos protegidos. El PIN se valida en el servidor y los intentos fallidos se limitan.                                                                 | `apps/accounts/views.py`, `templates/accounts/login.html` y `pin.html`.                                                       | A1     | Diego Galindo (B) + Yahir Enríquez (F)                                                       | 3.1.1        |
| 3.1.3  | RBAC por rol             | Mixins que restringen cada vista según el rol y, en los módulos protegidos, exigen el PIN de administrador. Todo se valida en el servidor; el candado de la interfaz es solo informativo.                                                                     | `apps/core/mixins.py`, aplicado en las vistas de los 4 módulos.                                                               | A1     | Jesús Hernández                                                                              | 3.1.2, 2.1   |
| 3.1.4  | Pruebas unitarias M-USR  | Casos de prueba de inicio de sesión, PIN (correcto, incorrecto, bloqueo por intentos), administración de cuentas y restricción de acceso por rol.                                                                                                             | `apps/accounts/tests.py`.                                                                                                     | —      | Diego Galindo (+ Jesús Hernández en pruebas del modelo y de los mixins)                      | 3.1.1–3.1.3  |

### 3.2 Módulo M-INV — Catálogo, recetas e inventario

| Código | Nombre                          | Descripción                                                                                                                                  | Entregable verificable                                                    | RF/RNF | Responsable(s)                                                    | Dependencias       |
| ------ | ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------- | ------------------ |
| 3.2.1  | Catálogo de platillos y precios | Alta y edición de platillos con nombre, categoría y precio.                                                                                  | `apps/catalog/models.py` (`Dish`), Django Admin.                          | A21    | Jesús Hernández (modelo) + Diego Galindo (B)                      | 3.1.3              |
| 3.2.2  | Catálogo de insumos             | Alta y edición de insumos con su unidad de medida.                                                                                           | `apps/catalog/models.py` (`Ingredient`).                                  | A22    | Jesús Hernández (modelo) + Diego Galindo (B)                      | 3.1.3              |
| 3.2.3  | Definición de recetas           | Asociación platillo–insumo–cantidad.                                                                                                         | `apps/catalog/models.py` (`Recipe`).                                      | A23    | Jesús Hernández (modelo) + Diego Galindo (B)                      | 3.2.1, 3.2.2       |
| 3.2.4  | Niveles mínimos de stock        | Mínimo deseado por insumo.                                                                                                                   | Campo `min_stock`.                                                        | A24    | Jesús Hernández                                                   | 3.2.2              |
| 3.2.5  | Entrada de insumos comprados    | Registro de compras que incrementan las existencias.                                                                                         | `apps/inventory/services.py` (`register_purchase`).                       | A41    | Diego Galindo (B) + Yahir Enríquez (F)                            | 3.2.2              |
| 3.2.6  | Descuento de insumos por venta  | Descuento automático de existencias por receta al confirmarse la venta, en línea o al sincronizar. Un solo paquete, usado por ambos caminos. | `apps/inventory/services.py` (`deduct_for_sale`).                         | RF-04  | Jesús Hernández                                                   | 3.2.3, 3.3.4       |
| 3.2.7  | Registro de mermas y faltantes  | Registro de merma con motivo, restringido al Administrador.                                                                                  | `apps/inventory/services.py` (`register_waste`).                          | A43    | Diego Galindo (B) + Yahir Enríquez (F)                            | 3.2.2, 3.1.3       |
| 3.2.8  | Alerta de stock crítico         | Alerta visual cuando `existencia <= min_stock`; no bloquea la venta.                                                                         | `templates/inventory/partials/stock_alert_badge.html`, `check_min_stock`. | A44    | Diego Galindo (B) + Yahir Enríquez (F)                            | 3.2.4, 3.2.5–3.2.7 |
| 3.2.9  | Pruebas unitarias M-INV         | Casos de prueba de descuento, compra, merma y alerta.                                                                                        | `apps/inventory/tests.py`, `apps/catalog/tests.py`.                       | —      | Diego Galindo (+ Jesús Hernández en pruebas de `deduct_for_sale`) | 3.2.1–3.2.8        |

### 3.3 Módulo M-PDV — Punto de venta

| Código | Nombre                  | Descripción                                                                                                                                                                                                                                                     | Entregable verificable                                                                                                  | RF/RNF                   | Responsable(s)                                                                | Dependencias               |
| ------ | ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------ | ----------------------------------------------------------------------------- | -------------------------- |
| 3.3.1  | Selección de platillos  | Listado de los platillos disponibles por categoría para agregarlos al pedido.                                                                                                                                                                                   | `apps/pos/views.py` (`dish_list`), `templates/pos/partials/dish_list.html`.                                             | A31                      | Jared Beltrán (B) + Alejandro Tarín (F)                                       | 3.2.1, 2.1                 |
| 3.3.2  | Armar pedido            | Construcción del pedido en curso: agregar y quitar líneas, ajustar cantidades y ver el resumen que actualiza el servidor.                                                                                                                                       | `apps/pos/views.py` (`order_builder`, `add_item`, `remove_item`), `templates/pos/order_builder.html`.                   | A31                      | Jared Beltrán (B) + Alejandro Tarín (F)                                       | 3.3.1                      |
| 3.3.3  | Aplicar modificadores   | Exclusión o adición de ingredientes por línea de pedido.                                                                                                                                                                                                        | `apps/pos/models.py` (`Modifier`), endpoints en `views.py`, interfaz en `templates/pos/`.                               | A32                      | Jesús Hernández (modelo) + Jared Beltrán (B) + Alejandro Tarín (F)            | 3.3.2                      |
| 3.3.4  | Calcular total          | Cálculo del total del pedido con modificadores, en el servidor.                                                                                                                                                                                                 | `apps/pos/services_pricing.py` (`calcular_total`, DEC-01).                                                              | A33; RF-12               | Jesús Hernández                                                               | 3.3.3                      |
| 3.3.5  | Confirmar venta         | Registro del cobro con su método de pago (requiere turno abierto) e inmutabilidad de la venta confirmada. Incluye el ajuste o la cancelación posterior con motivo (`error_captura`, `devolucion`, `correccion_pago`), que deja rastro y decide qué se revierte. | `apps/pos/services.py` (`confirm_sale`, `cancel_sale`, `adjust_sale`), `SaleAdjustment`, `partials/order_summary.html`. | A34; regla de negocio 11 | Jesús Hernández (servicio y modelo) + Jared Beltrán (B) + Alejandro Tarín (F) | 3.3.4, 3.1.3, 3.5.1, 3.2.6 |
| 3.3.6  | Pruebas unitarias M-PDV | Casos de prueba de selección, armado, modificadores, cálculo, confirmación y ajustes.                                                                                                                                                                           | `apps/pos/tests.py`.                                                                                                    | —                        | Jared Beltrán (+ Jesús Hernández en servicios y paridad)                      | 3.3.1–3.3.5                |

### 3.4 Operación offline y sincronización

> Todos los paquetes de esta rama se programan en pareja. Los invariantes no se simplifican: un solo camino de escritura, UUID por operación, cuarentena en lugar de rechazo y dinero en enteros.

| Código | Nombre                                             | Descripción                                                                                                                                                                                                                                                                                                                                           | Entregable verificable                                                                                                                                           | RF/RNF                              | Responsable(s)                                                                                              | Dependencias        |
| ------ | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------- |
| 3.4.1  | PWA shell (manifest + registro del service worker) | Manifiesto web y registro del service worker para instalar el SGFT en la pantalla de inicio. El service worker debe controlar las rutas `/pos/`.                                                                                                                                                                                                      | `static/pos/manifest.json`, registro de `sw.js`.                                                                                                                 | RNF-08                              | Alejandro Tarín + Yahir Enríquez                                                                            | 3.3.6               |
| 3.4.2  | Cacheo de la aplicación con Workbox                | Precaching del HTML, CSS y JS del punto de venta con Workbox cargado por CDN.                                                                                                                                                                                                                                                                         | `static/pos/sw.js`.                                                                                                                                              | RNF-08                              | Alejandro Tarín + Yahir Enríquez                                                                            | 3.4.1               |
| 3.4.3  | Almacén local IndexedDB/Dexie                      | Copia local del catálogo, recetas y precios; cola única de operaciones (ventas y aperturas, con campo `tipo`); estado del turno.                                                                                                                                                                                                                      | `static/pos/db.js`.                                                                                                                                              | RF-07                               | Alejandro Tarín + Yahir Enríquez                                                                            | 3.4.1               |
| 3.4.4  | Lógica de pedido en cliente (Alpine.js)            | Armado del pedido sin servidor: estado de la interfaz en Alpine y total con `calcularTotal()` en enteros de centavos.                                                                                                                                                                                                                                 | `static/pos/pricing.js`, plantillas del punto de venta con `x-data`.                                                                                             | RF-07                               | Alejandro Tarín + Yahir Enríquez                                                                            | 3.4.3, 3.3.3        |
| 3.4.5  | Prueba de paridad de precios Python/JS             | Fixture compartido y pruebas en ambos lenguajes que garantizan que `calcular_total()` y `calcularTotal()` dan lo mismo al centavo. Se escribe antes de la primera línea de precios offline.                                                                                                                                                           | `tests_fixtures/pricing_cases.json`, `PricingParityTest`, `tests_e2e/parity/test_pricing.mjs`, job en CI.                                                        | ADR-02                              | Jesús Hernández + Alejandro Tarín (+ Jared Beltrán, job de CI)                                              | 3.3.4, 3.4.4        |
| 3.4.6  | Endpoint de sincronización POST /pos/sync/         | Recepción del lote, idempotencia por UUID, aplicación en transacción atómica, cuarentena y respuesta por UUID según el contrato v1. Incluye la **bandeja de revisión del Administrador**: resolver cuarentenas (aplicar con el catálogo actual, aplicar sin descontar o descartar) y revisar existencias negativas y ventas con diferencia de precio. | `apps/pos/views.py` (`sync_operations`), campos de `Sale` del contrato, resolución en `apps/pos/services.py`, `templates/pos/review/`.                           | RF-07, RNF-08; reglas 8, 9, 10 y 14 | Jesús Hernández + Jared Beltrán (pareja, B) + Yahir Enríquez (F, bandeja)                                   | 3.4.5, 3.2.6, 3.1.3 |
| 3.4.7  | Apertura/cierre de turno de caja offline           | **Apertura** operable sin conexión, con UUID propio y sincronizada como una venta. **Cierre** solo en línea: efectivo final contado, esperado y diferencia (se registra sin bloquear); se niega a cerrar con operaciones pendientes de sincronizar.                                                                                                   | `apps/pos/services_cash_session.py` (`open_session`, `close_session`), `CashRegisterSession`, `QuarantinedCashSession`, `templates/pos/cash_session_close.html`. | A51; reglas 5, 12 y 13              | Jesús Hernández (servicio) + Jared Beltrán (B) + Alejandro Tarín (F, apertura) + Yahir Enríquez (F, cierre) | 3.4.6, 3.5.1        |
| 3.4.8  | Pruebas E2E offline (Playwright)                   | Venta con y sin conexión, y apertura de caja sin conexión.                                                                                                                                                                                                                                                                                            | `tests_e2e/test_pos_sale.py`, `tests_e2e/test_cash_session_open.py`.                                                                                             | —                                   | Yahir Enríquez + Jared Beltrán                                                                              | 3.4.6, 3.4.7        |

### 3.5 Módulo M-REP — Caja y reportes (A5)

| Código | Nombre                        | Descripción                                                                                                                                                                                                                                                    | Entregable verificable                                                          | RF/RNF          | Responsable(s)                                                       | Dependencias        |
| ------ | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | --------------- | -------------------------------------------------------------------- | ------------------- |
| 3.5.1  | Abrir turno de caja           | Declaración del efectivo inicial y validación de que no haya otro turno abierto (en línea).                                                                                                                                                                    | `apps/pos/services_cash_session.py` (`open_session`), vista de apertura.        | A51             | Jesús Hernández (servicio) + Jared Beltrán (B) + Alejandro Tarín (F) | 3.1.3               |
| 3.5.2  | Calcular corte de caja        | Consolidado de ventas del turno por método de pago. Reporta el descuadre sin bloquear y exige la cola de sincronización vacía.                                                                                                                                 | `apps/reports/services.py` (`cash_close`), `templates/reports/cash_close.html`. | A52             | Jesús Hernández (servicio) + Jared Beltrán (B) + Yahir Enríquez (F)  | 3.5.1, 3.4.7, 3.4.6 |
| 3.5.3  | Reporte de ventas por periodo | Consulta de ventas filtrable por periodo, restringida al Administrador.                                                                                                                                                                                        | `apps/reports/services.py` (`sales_by_period`).                                 | A53             | Jared Beltrán (B) + Yahir Enríquez (F)                               | 3.3.5               |
| 3.5.4  | Productos más vendidos        | Platillos con mayor volumen de venta en un periodo.                                                                                                                                                                                                            | `apps/reports/services.py` (`top_dishes`).                                      | A54             | Jared Beltrán (B) + Yahir Enríquez (F)                               | 3.3.5, 3.2.6        |
| 3.5.5  | Exportar reportes             | Exportación de las ventas del día a PDF (DEC-13): detalle de ventas, ajustes con motivo y totales por método de pago. Se atribuyen al día por la hora del dispositivo, solo el Administrador las exporta y se niega con operaciones pendientes de sincronizar. | `apps/reports/services.py` (`export_daily_sales_pdf`), botón «Exportar PDF».    | Pendiente de RF | Jared Beltrán (B) + Yahir Enríquez (F)                               | 3.3.5, 3.5.1        |
| 3.5.6  | Pruebas unitarias M-REP       | Casos de prueba de apertura, corte, descuadre, reportes y exportación.                                                                                                                                                                                         | `apps/reports/tests.py`.                                                        | —               | Jared Beltrán (+ Jesús Hernández en pruebas de `cash_close`)         | 3.5.1–3.5.5         |

### 4. Control de calidad

| Código | Nombre                                                  | Descripción                                                                                                                                                                                                         | Entregable verificable                                                              | RF/RNF                    | Responsable(s)                             | Dependencias                      |
| ------ | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------- | ------------------------------------------ | --------------------------------- |
| 4.1    | Cobertura de pruebas unitarias consolidada              | Revisión de que cada RF implementado tenga al menos un caso de prueba.                                                                                                                                              | Resumen de cobertura por módulo y reporte del job de CI.                            | —                         | Jared Beltrán + Yahir Enríquez             | 3.1.4, 3.2.9, 3.3.6, 3.4.8, 3.5.6 |
| 4.2    | Revisión de código                                      | Ningún push directo a `main`. Cada PR lleva título `WBS-x.y.z: descripción`, revisión de rutas y CI en verde. El integrador aprueba y fusiona con _Squash and merge_.                                               | Historial de PR; `CODEOWNERS`; rulesets de `main`; revisión de rutas en CI.         | `CLAUDE.md` §8            | Alejandro Tarín (integrador)               | Continuo, desde el primer PR      |
| 4.3    | Matriz de trazabilidad de requisitos a casos de prueba  | Verificar que cada RF y RNF tenga al menos un caso de prueba que lo cubra.                                                                                                                                          | Matriz RF/RNF → caso de prueba (anexo del SRS).                                     | —                         | Jesús Hernández                            | 4.1                               |
| 4.4    | Verificación de seguridad                               | Contraseñas y PIN con hash; límite de intentos del PIN; CSRF activo; autorización revalidada en el servidor, incluidas las operaciones sincronizadas; secretos fuera del repositorio. Alineado a OWASP Top 10:2021. | Checklist de seguridad firmado antes del despliegue.                                | RES-07; OWASP Top 10:2021 | Jesús Hernández                            | 3.1.2, 3.1.3, 3.4.6               |
| 4.5    | Datos de prueba ficticios y coherentes con el menú real | Datos ficticios pero coherentes con el menú real (burritos, guisados, bebidas) para desarrollo y demostración.                                                                                                      | Fixtures en `apps/<app>/fixtures/*.json` (repositorio público: nunca datos reales). | `CLAUDE.md` §10           | Yahir Enríquez                             | 3.1.1, 3.2.1–3.2.3                |
| 4.6    | Pruebas E2E críticas (venta PDV, corte de caja)         | Los dos flujos de punta a punta acordados, ejecutados en el pipeline.                                                                                                                                               | Job de Playwright en GitHub Actions; `tests_e2e/test_cash_close.py`.                | ADR-01                    | Yahir Enríquez (+ Jared Beltrán, workflow) | 3.4.8, 5.1                        |

### 5. Integración, CI/CD y despliegue

| Código | Nombre                                                                | Descripción                                                                                                                                       | Entregable verificable                                                                       | RF/RNF         | Responsable(s)                    | Dependencias              |
| ------ | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | -------------- | --------------------------------- | ------------------------- |
| 5.1    | Pipeline de GitHub Actions                                            | `manage.py test`, `node --test` y revisión de rutas (`--revisar`) en cada Pull Request.                                                           | `.github/workflows/`.                                                                        | `CLAUDE.md` §6 | Jared Beltrán                     | 3.1.4 (ver duda 10)       |
| 5.2    | Entornos gestionados (PostgreSQL Neon/Supabase, variables de entorno) | PostgreSQL en Neon o Supabase y variables de entorno, sin valores reales en el repositorio.                                                       | `.env.example`, `DATABASE_URL` configurada en el proveedor.                                  | RES-02         | Jesús Hernández                   | 3.1.1                     |
| 5.3    | Despliegue en Railway                                                 | Servicio Django con Gunicorn y WhiteNoise, `collectstatic` y migraciones automatizadas al fusionar a `main`.                                      | Servicio desplegado en Railway y accesible por URL.                                          | RES-05         | Jesús Hernández + Alejandro Tarín | 5.1, 5.2, 3.4.6           |
| 5.4    | Spike de validación offline                                           | Prueba de concepto con Workbox: catálogo en caché, pedido sin red, cola persistente, sincronización con UUID y descuento aplicado en el servidor. | Resultado documentado del spike; código en la rama `tarin/spike-offline`, que no se fusiona. | ADR-02         | Alejandro Tarín + Jared Beltrán   | 3.4.1–3.4.3 (ver duda 10) |

## 3. Supuestos

1. **Requisitos y SADT cerrados.** El catálogo de requisitos y los diagramas SADT ya están terminados fuera de esta WBS; la rama 1 solo conserva el modelo de datos.
2. **Vista de cocina fuera de la línea base.** La vista de cocina (antes 3.3.7) está en evaluación (DEC-15). Si se aprueba, entra por control de cambios con un código nuevo. El sistema tiene solo dos roles (DEC-21), así que la usarían Administrador o Cajero.
3. **3.5.5 sin RF.** Exportar reportes todavía no tiene RF asignado. Su alcance está definido por DEC-13.
4. **Sin estimación.** No hay estimación de tiempos ni PERT; es el paso siguiente tras validar esta revisión.

## 4. Dudas de esta revisión

Cada duda indica qué asumí para poder escribir la revisión completa.

1. **¿El PIN reemplaza al usuario y contraseña, o es un segundo paso?** Asumí lo segundo, como en el sistema de diseño: el personal inicia sesión, y el PIN de administrador desbloquea Productos, Inventario y Reportes. Si el PIN es el único acceso, cambian 3.1.1, 3.1.2, 3.1.3 y 4.4. Un PIN de 4 a 6 dígitos solo es seguro si se limitan los intentos fallidos.
2. **Numeración de 3.5.** El diagrama repite 3.5.5 y pone «Exportar» antes que «Más vendidos». Asumí 3.5.4 Productos más vendidos, 3.5.5 Exportar reportes y 3.5.6 Pruebas.
3. **¿Separar de nuevo 3.3.1 y 3.3.2 es intencional?** Revierte la fusión de la Revisión 4 (DEC-12). Los separé, como en el diagrama.
4. **Trabajo dentro del alcance que el diagrama no tiene.** Lo integré en el paquete más cercano. ¿Prefieren paquetes propios?
   - administración de cuentas → 3.1.1;
   - ajuste y cancelación de venta → 3.3.5;
   - bandeja de revisión del Administrador → 3.4.6;
   - cierre de turno → 3.4.7.
5. **¿Se descarta la vista de cocina?** La dejé fuera, como supuesto en evaluación. RF-17 está en el alcance que validó el cliente.
6. **¿Desaparece el manual de usuario (antes 1.7) como entregable?** No está en el diagrama.
7. **Endpoint `/pdv/sync/` del diagrama.** Lo escribí como `/pos/sync/`, que es como se llama en el código desde DEC-17.
8. **Pantallas de Figma por paquete.**
   - _Panel principal:_ lo asigné a M-PDV (2.2.2), pero muestra datos de varios módulos.
   - _Acceso con PIN (2.2.1):_ resuelto; el modal está en Figma (página «04 · Componentes · Rev. 1.2», «Diálogo · PIN de administrador»).
9. **Documentos fuera del repositorio.** Prototipos, checklist de seguridad, resumen de cobertura y resultado del spike van sin ruta `docs/` (DEC-22). ¿Dónde deben quedar?
10. **Dependencias de 5.1 y 5.4 (pendiente desde antes).** El CI espera las pruebas de usuarios y el spike espera el punto de venta terminado, cuando ambos deberían arrancar justo después del esqueleto.
11. **Choque de numeración de decisiones.** La skill de diseño ya usa **DEC-24** para el PIN de administrador, y el registro de la skill de organización iba a usar ese mismo número para la siguiente decisión. Al sincronizar la skill, el siguiente número libre será DEC-25.

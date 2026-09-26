# WBS (EDT) — Sistema de Gestión de Food Truck (SGFT)

**Elaborado por:** analista de sistemas (asistido por IA), a partir de la documentación ratificada del proyecto.
**Fecha:** 24 de septiembre de 2026. **Revisión 4** — se asignan los responsables conforme a la distribución del equipo por capas (Alejandro Tarín y Yahir Enríquez en frontend; Jesús Hernández en backend y base de datos; Diego Galindo y Jared Beltrán en backend) y se dan de alta cuatro paquetes que estaban dentro del alcance sin paquete propio. Se conserva el principio MECE y la exclusión de tareas administrativas.
**Fuentes consultadas:** las de la Revisión 3, más las decisiones del 24-sep-2026 registradas en `docs/decisiones/organizacion-repositorio.md` (DEC-07 a DEC-11), `docs/decisiones/contrato-sync-pdv.md` (DEC-02 a DEC-06) y `docs/decisiones/nombres-modulo-precios.md` (DEC-01).
**Estado:** responsables validados por el equipo el 24-sep-2026; pendiente la estimación de tiempos (no se incluye cronograma ni horas, por instrucción explícita).
**Ajuste posterior el mismo día:** se resolvieron los supuestos 3, 5 y 6 de la sección 3 y el supuesto 9 se sustituyó por la vista de cocina (3.3.7), que pasa a evaluación — ver los puntos 7 a 13 de la lista de cambios.

## Cambios de esta revisión frente a la Revisión 3

1. **Responsables por capas.** La columna "Responsable(s)" deja de ser sugerida y refleja la distribución por capas. Cuando un paquete cruza capas, se indica quién lleva cada parte: *(modelo)* / *(servicio)* para la capa de datos y reglas transaccionales, *(B)* para vistas y servicios no transaccionales, *(F)* para plantillas y cliente. El detalle por archivo, revisores y la justificación de cada cambio están en la skill `sgft-organizacion-entregables` (`references/matriz-wbs-responsables.md`).
2. **Cambios de responsable más relevantes:**
   - todos los modelos y migraciones pasan a Jesús Hernández;
   - los servicios de reportes (3.5.3–3.5.6) pasan de Yahir Enríquez a Jared Beltrán, y Yahir conserva sus pantallas;
   - los servicios no transaccionales de M-USR y M-INV pasan a Diego Galindo;
   - las vistas de M-PDV pasan a Jared Beltrán;
   - las parejas del módulo offline 3.4.1–3.4.4 pasan a Alejandro Tarín + Yahir Enríquez;
   - los mockups 2.2.2–2.2.4 pasan a Yahir Enríquez;
   - el pipeline de CI (5.1) pasa a Jared Beltrán;
   - las pruebas unitarias las escribe el dueño backend de cada módulo.
3. **Paquetes nuevos (DEC-07), sin renumerar los existentes:** 3.3.7 Consulta de pedidos en cocina (RF-17; después pasó a evaluación, ver punto 10), 3.3.8 Ajuste y cancelación de venta (regla de negocio 11), 3.4.9 Bandeja de revisión del Administrador (reglas 9 y 10, DEC-02) y 3.5.7 Cerrar turno de caja (reglas 5 y 13).
4. **3.4.7** se renombra "Apertura de turno de caja offline": el cierre es solo en línea y ahora es el paquete 3.5.7. **3.5.2** agrega la dependencia de 3.5.7, porque el corte lee la diferencia de caja registrada al cerrar.
5. **Se corrige 2.1:** `apps/core/mixins.py` deja de listarse como entregable de 2.1 y queda solo en 3.1.3.
6. **Entregables con ubicación definida (DEC-09):** 1.4.1, 1.7, 4.1, 4.4, 4.5 y 5.4 indican ahora la ruta del repositorio donde se entregan. 3.4.6 incluye el contrato de sincronización aprobado (versión 1). 4.2 incluye CODEOWNERS y la protección de `main` (DEC-10).

7. **Fusión de 3.3.1 y 3.3.2 (DEC-12).** "Selección de platillos" y "Armar pedido" se fusionan en **3.3.1 Selección de platillos y armado del pedido**. Seleccionar un platillo es agregarlo al pedido, así que la selección sola no produce un entregable verificable por el usuario. Además, ambos viven en la misma pantalla (`order_builder.html` incluye `partials/dish_list.html`), tienen los mismos responsables, se prueban en el mismo flujo y corresponden a una sola caja del SADT (A31). El código **3.3.2 queda retirado y no se reutiliza**, para no renumerar paquetes ya citados en la documentación.
8. **3.5.5 se redefine (DEC-13)** como **Exportar ventas del día a PDF**, según la definición del equipo. Deja de cubrir el reporte por periodo y el de productos más vendidos. Sus dependencias pasan a ser las de las ventas del día (3.3.5, 3.3.8, 3.5.1) en lugar de 3.5.3 y 3.5.4.
9. **Nuevo 3.1.5 Administración de cuentas de personal (DEC-14).** El SADT declara dos actividades en A1 (administrar cuentas; autenticar y restringir por rol), pero el WBS solo tenía paquete para la segunda. La caja A1 del SADT sigue sin abrirse (ver supuesto 6).
10. **Vista de cocina en evaluación (DEC-15).** La consulta de pedidos pendientes en cocina (3.3.7) es una sección más de la aplicación, como Punto de venta o Inventario. Como el equipo aún no decide si la implementará, sale de la línea base y pasa a la sección 2-bis, con prioridad candidata "Debería" (SRS 1.1.3). No suma a la estimación hasta que se apruebe. Sustituye al supuesto 9 anterior.

11. **Integrador (DEC-16).** 4.2 deja de ser responsabilidad genérica del equipo. Alejandro Tarín valida las rutas de cada PR y es el único que fusiona en `main`, y los code owners siguen aprobando el contenido. `main` se protege con dos rulesets.

12. **Nombres de código en inglés (DEC-17).** La app del punto de venta pasa de `pdv` a `pos` en todas las rutas de entregables de esta WBS (`apps/pos/`, `static/pos/`, `templates/pos/`, `POST /pos/sync/`), y las pruebas E2E se renombran en inglés. El nombre del módulo (M-PDV) no cambia.

13. **Tarín aprueba todos los PR (DEC-18).** 4.2 queda a cargo del integrador, que aprueba y fusiona. Los dueños de cada ruta reciben la solicitud de revisión, pero su aprobación ya no es obligatoria.

## Historial — cambios de la Revisión 3 frente a la Revisión 2

1. **Apartado 1** se desglosó con mayor granularidad: 1.1 "SRS — Introducción" y 1.2 "SRS — Descripción general" ahora tienen hijos explícitos por numeral (propósito/alcance/visión, definiciones y LEL, perspectiva del producto, funciones del producto, características del usuario, restricciones, suposiciones y dependencias), en vez de un solo paquete consolidado por apartado. Los apéndices se renombraron como **A** (Diagrama de Proceso), **B** (SADT/IDEF0) y **C** (Modelo de datos).
2. **Se retiró el nodo "Decisiones técnicas (ADR)"** (antes 1.7, con ADR-01 y ADR-02 como paquetes de trabajo propios) — las decisiones de arquitectura siguen vigentes y documentadas en `ADR-01-arquitectura-SGFT.md`/`ADR-02-operacion-offline-SGFT.md`, pero ya no se registran como entregables pendientes del WBS por estar completadas y ratificadas. El **manual de usuario** se conservó, ahora como 1.7.
3. **Apartado 2** fusionó "Convención HTMX/Alpine" y "Plantilla base y componentes compartidos" en un solo paquete: **2.1 Estructura base del sistema (app)**. Los mockups se renumeraron de 2.3.x a 2.2.x.
4. **Apartado 3** eliminó los prefijos de código SADT (A21, A34, A51…) de los nombres de los paquetes, dejando la referencia funcional solo a nivel de módulo. En M-PDV, "Armar pedido" (antes A31, un solo paquete) se dividió en dos paquetes de trabajo diferenciados: **3.3.1 Selección de platillos** y **3.3.2 Armar pedido**; "Confirmar cobro y orden a cocina" se renombró a **3.3.5 Confirmar venta**.
5. **En 3.5 (Módulo M-REP) se agregó un paquete nuevo, "Exportar reportes"**, y se corrigió una inconsistencia de numeración detectada en la lista entregada por el equipo (el código 3.5.5 aparecía dos veces — en "Productos más vendidos" y en "Pruebas unitarias M-REP" — y "Exportar reportes" estaba fuera de secuencia). Se renumeró de forma consecutiva: 3.5.1 Abrir turno de caja, 3.5.2 Calcular corte de caja, 3.5.3 Reporte de ventas por periodo, 3.5.4 Productos más vendidos, 3.5.5 Exportar reportes, 3.5.6 Pruebas unitarias M-REP.
6. **"Control de calidad transversal" se renombró a "Control de calidad"** (apartado 4); su contenido no cambió.
7. El diccionario del WBS que respalda esta jerarquía también se entregó como documento de Word (`WBS-SGFT-Diccionario-Niveles.docx`), en una vista por niveles (1/2/3) con columnas WBS Level | WBS Code | WBS Name | WBS Description | Responsable | Dependencia, sin color.

---

## 1. Esquema jerárquico

```
1. Documentación y especificación técnica
   1.1 SRS — Introducción
       1.1.1 Consolidación formal de propósito, alcance y visión general
       1.1.2 Definiciones, acrónimos y Léxico Extendido de Lenguaje
   1.2 SRS — Descripción general
       1.2.1 Consolidación formal de perspectiva del producto
       1.2.2 Consolidación formal de funciones del producto
       1.2.3 Consolidación formal de características del usuario
       1.2.4 Consolidación formal de restricciones
       1.2.5 Consolidación formal de suposiciones y dependencias
   1.3 SRS — Requisitos específicos
       1.3.1 Catálogo formal de requisitos
   1.4 Apéndice A — Diagrama de Proceso
       1.4.1 Diagrama de procesos propuesto
   1.5 Apéndice B — Descomposición SADT/IDEF0
       1.5.1 Diagramas SADT del sistema propuesto
   1.6 Apéndice C — Modelo de datos
       1.6.1 Diagrama entidad-relación y diccionario de datos
   1.7 Manual de usuario

2. Diseño de interfaz (UI/UX)
   2.1 Estructura base del sistema (app)
   2.2 Mockups por pantalla
       2.2.1 Mockup M-PDV (venta)
       2.2.2 Mockup M-USR (inicio de sesión)
       2.2.3 Mockup M-INV (inventario)
       2.2.4 Mockup M-REP (caja/reportes)

3. Desarrollo del sistema
   3.1 Módulo M-USR — Inicio de sesión
       3.1.1 Modelo de usuario y rol
       3.1.2 Autenticación de usuario
       3.1.3 RBAC por rol
       3.1.4 Pruebas unitarias M-USR
       3.1.5 Administración de cuentas de personal
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
       3.3.1 Selección de platillos y armado del pedido
       3.3.3 Aplicar modificadores
       3.3.4 Calcular total
       3.3.5 Confirmar venta
       3.3.6 Pruebas unitarias M-PDV
       3.3.8 Ajuste y cancelación de venta
   3.4 Operación offline y sincronización
       3.4.1 PWA shell (manifest + registro del service worker)
       3.4.2 Cacheo de la aplicación con Workbox
       3.4.3 Almacén local IndexedDB/Dexie
       3.4.4 Lógica de pedido en cliente (Alpine.js)
       3.4.5 Prueba de paridad de precios Python/JS
       3.4.6 Endpoint de sincronización POST /pos/sync/
       3.4.7 Apertura de turno de caja offline
       3.4.8 Pruebas E2E offline (Playwright)
       3.4.9 Bandeja de revisión del Administrador
   3.5 Módulo M-REP — Caja y reportes (A5)
       3.5.1 Abrir turno de caja
       3.5.2 Calcular corte de caja
       3.5.3 Reporte de ventas por periodo
       3.5.4 Productos más vendidos
       3.5.5 Exportar ventas del día a PDF
       3.5.6 Pruebas unitarias M-REP
       3.5.7 Cerrar turno de caja

4. Control de calidad
   4.1 Cobertura de pruebas unitarias consolidada
   4.2 Revisión de código (PR obligatorio)
   4.3 Matriz de trazabilidad de requisitos a casos de prueba
   4.4 Verificación de seguridad
   4.5 Datos de prueba ficticios y coherentes con el menú real
   4.6 Pruebas E2E críticas en CI (venta PDV, corte de caja)

5. Integración, CI/CD y despliegue
   5.1 Pipeline de GitHub Actions
   5.2 Entornos gestionados (PostgreSQL Neon/Supabase, variables de entorno)
   5.3 Despliegue en Render/Railway
   5.4 Spike de validación offline (Sprint 1)
```

---

## 2. Diccionario del WBS

> Columnas: Código | Nombre | Descripción | Entregable verificable | RF/RNF relacionado(s) | Responsable(s) (distribución por capas) | Dependencias
> Notación de responsables: *(modelo)* / *(servicio)* = capa de datos y reglas transaccionales · *(B)* = vistas y servicios no transaccionales · *(F)* = plantillas y cliente.
> **Nota sobre RF/RNF:** la documentación consultada no incluye todavía el apartado 3 del SRS (catálogo formal, paquete 1.3.1). Donde no hay un código RF-nn/RNF-nn confirmado, se referencia el módulo o se deja como vacío pendiente de la sección 3.

### 1. Documentación y especificación técnica

| Código | Nombre | Descripción | Entregable verificable | RF/RNF | Responsable(s) | Dependencias |
|---|---|---|---|---|---|---|
| 1.1.1 | Consolidación formal de propósito, alcance y visión general | Trasladar el contenido ya ratificado de `SRS-SGFT-01-Proposito-y-Alcance.md` al apartado de introducción formal del SRS. | Numerales de propósito, alcance y visión general en `docs/SRS.md`. | — | Diego Galindo | Ninguna (contenido ya redactado) |
| 1.1.2 | Definiciones, acrónimos y Léxico Extendido de Lenguaje | Completar el numeral de definiciones, acrónimos y LEL, pendiente en la fuente. | Numeral de definiciones redactado en `docs/SRS.md`. | — | Diego Galindo | 1.1.1 |
| 1.2.1 | Consolidación formal de perspectiva del producto | Redactar la perspectiva del producto (relación con el negocio actual, interfaces externas) a partir de `SRS-SGFT-insumos-apartado-2.md`. | Numeral de perspectiva del producto en `docs/SRS.md`. | — | Diego Galindo | 1.1.1 |
| 1.2.2 | Consolidación formal de funciones del producto | Trasladar la tabla de funciones por módulo (M-USR/M-INV/M-PDV/M-REP) al apartado 2 formal. | Numeral de funciones del producto en `docs/SRS.md`. | — | Diego Galindo | 1.2.1 |
| 1.2.3 | Consolidación formal de características del usuario | Redactar los perfiles de usuario (Administrador, Cajero, Cocinero) y su nivel de experiencia técnica esperado. | Numeral de características del usuario en `docs/SRS.md`. | — | Diego Galindo | 1.2.2 |
| 1.2.4 | Consolidación formal de restricciones | Formalizar las restricciones (RES-nn) ya identificadas: Sprints de dos semanas, dedicación parcial del equipo, alcance académico. | Numeral de restricciones en `docs/SRS.md`. | — | Diego Galindo | 1.2.2 |
| 1.2.5 | Consolidación formal de suposiciones y dependencias | Formalizar los supuestos (SUP-nn) y dependencias externas del proyecto. | Numeral de suposiciones y dependencias en `docs/SRS.md`. | — | Diego Galindo | 1.2.2 |
| 1.3.1 | Catálogo formal de requisitos | Redactar RI-nn, RF-nn, RNF-nn, RN-nn, RT-nn y RL-nn a partir de las capacidades por módulo y de las tablas ICOM del SADT. | Apartado de requisitos específicos completo en `docs/SRS.md`. | Genera la trazabilidad para el resto del WBS | Diego Galindo + Jesús Hernández | 1.2.2, 1.5.1 |
| 1.4.1 | Diagrama de procesos propuesto | Documentar el flujo operativo una vez implantado el SGFT, como Apéndice A del SRS. | Apéndice A con el diagrama de procesos, en `docs/diagramas/procesos/`. | — | Diego Galindo | 1.2.2 |
| 1.5.1 | Diagramas SADT del sistema propuesto | Revisión visual final y exportación de las 7 láminas IDEF0 a PNG/PDF. | 7 láminas en `docs/diagramas/`, Apéndice B del SRS. | — | Jesús Hernández | Ninguna (láminas ya validadas) |
| 1.6.1 | Diagrama entidad-relación y diccionario de datos | Formalizar el modelo de datos preliminar (definido en ADR-01 sección 6) como diagrama ER y diccionario de campos/tipos. | Diagrama ER y diccionario de datos, Apéndice C del SRS. | — | Jesús Hernández | 1.3.1, 1.5.1 |
| 1.7 | Manual de usuario | Documento de uso por rol (Administrador, Cajero, Cocinero), incluida la instalación de la PWA. | Manual de usuario en español: `docs/manual-usuario.md` (si se redacta en Word, en el espacio compartido del equipo, no en el repositorio). | RES-05 | Diego Galindo + Alejandro Tarín + Yahir Enríquez | 3.1–3.5 completos |

### 2. Diseño de interfaz (UI/UX)

| Código | Nombre | Descripción | Entregable verificable | RF/RNF | Responsable(s) | Dependencias |
|---|---|---|---|---|---|---|
| 2.1 | Estructura base del sistema (app) | Convención de integración HTMX/Alpine (CSRF, estructura de `partials/`, nomenclatura de endpoints) y plantilla base compartida con Bootstrap/HTMX/Alpine por CDN y mixins de permiso por rol. | `convencion-htmx-alpine-SGFT.md`, `apps/core/templates/base.html` (los mixins de permiso son entregable de 3.1.3). | RES-04 | Alejandro Tarín | Ninguna |
| 2.2.1 | Mockup M-PDV (venta) | Prototipo desechable HTML/CSS/JS del armado de pedido, modificadores y cobro. | `docs/prototipos/pdv-venta/index.html`. | A3 | Alejandro Tarín | 2.1 |
| 2.2.2 | Mockup M-USR (inicio de sesión) | Prototipo de la pantalla de inicio de sesión. | `docs/prototipos/usr-acceso/index.html`. | A1 | Yahir Enríquez | 2.1 |
| 2.2.3 | Mockup M-INV (inventario) | Prototipo de listados y formularios CRUD de platillos, insumos y alertas. | `docs/prototipos/inv-catalogo/index.html`. | A2, A4 | Yahir Enríquez | 2.1 |
| 2.2.4 | Mockup M-REP (caja/reportes) | Prototipo de apertura/cierre de turno y reportes. | `docs/prototipos/rep-caja/index.html`. | A5 | Yahir Enríquez | 2.1 |

### 3.1 Módulo M-USR — Inicio de sesión

| Código | Nombre | Descripción | Entregable verificable | RF/RNF | Responsable(s) | Dependencias |
|---|---|---|---|---|---|---|
| 3.1.1 | Modelo de usuario y rol | `User` como `AbstractUser` extendido con campo `role` (admin/cajero/cocinero). | `apps/accounts/models.py` + migración. | A1 (M-USR) | Jesús Hernández | 1.3.1 |
| 3.1.2 | Autenticación de usuario | Inicio y cierre de sesión, validación de credenciales por rol. | `apps/accounts/views.py`, `services.py`, `templates/accounts/login.html`. | A1 (M-USR) | Diego Galindo (B) + Yahir Enríquez (F) | 3.1.1 |
| 3.1.3 | RBAC por rol | Decoradores/mixins que restringen cada vista según el rol, validados en servidor. | `RoleRequiredMixin` en `apps/core/mixins.py`, aplicado en las vistas de los 4 módulos. | A1 (M-USR) | Jesús Hernández | 3.1.2, 2.1 |
| 3.1.4 | Pruebas unitarias M-USR | Casos de prueba de autenticación, administración de cuentas, asignación de rol y restricción de acceso. | `apps/accounts/tests.py`, corriendo en `manage.py test`. | — | Diego Galindo | 3.1.1–3.1.3, 3.1.5 |
| 3.1.5 | Administración de cuentas de personal | Alta, edición y desactivación de cuentas del personal y asignación de su rol, exclusiva del Administrador. Las cuentas se desactivan, no se borran, para conservar la autoría de ventas y movimientos ya registrados. | `apps/accounts/services.py` (`create_user`, `change_role`, desactivación), vistas en `apps/accounts/views.py`, `templates/accounts/partials/`. | A1 (M-USR) | Diego Galindo (B) + Yahir Enríquez (F) | 3.1.1, 3.1.3 |

### 3.2 Módulo M-INV — Catálogo, recetas e inventario

| Código | Nombre | Descripción | Entregable verificable | RF/RNF | Responsable(s) | Dependencias |
|---|---|---|---|---|---|---|
| 3.2.1 | Catálogo de platillos y precios | Alta/edición de platillos con nombre, categoría y precio. | `apps/catalog/models.py` (`Dish`), pantalla Django Admin. | A21 | Jesús Hernández (modelo) + Diego Galindo (B, Django Admin) | 3.1.3 |
| 3.2.2 | Catálogo de insumos | Alta/edición de insumos con su unidad de medida. | `apps/catalog/models.py` (`Ingredient`). | A22 | Jesús Hernández (modelo) + Diego Galindo (B, Django Admin) | 3.1.3 |
| 3.2.3 | Definición de recetas | Asociación platillo–insumo–cantidad. | `apps/catalog/models.py` (`Recipe`). | A23 | Jesús Hernández (modelo) + Diego Galindo (B, Django Admin) | 3.2.1, 3.2.2 |
| 3.2.4 | Niveles mínimos de stock | Definición de mínimo deseado por insumo. | Campo `min_stock` en el modelo de insumo o inventario. | A24 | Jesús Hernández | 3.2.2 |
| 3.2.5 | Entrada de insumos comprados | Registro de compras que incrementan existencias. | `apps/inventory/services.py` (`register_purchase`). | A41 | Diego Galindo (B) + Yahir Enríquez (F) | 3.2.2 |
| 3.2.6 | Descuento de insumos por venta | Descuento automático de existencias por receta al confirmarse la venta (en línea o al sincronizar). Paquete único, reutilizado por ambos caminos. | `inventory.services.deduct_for_sale()`. | RF-04 | Jesús Hernández | 3.2.3, 3.3.4 |
| 3.2.7 | Registro de mermas y faltantes | Registro de merma con motivo, restringido al Administrador. | `apps/inventory/services.py` (`register_waste`). | A43 | Diego Galindo (B) + Yahir Enríquez (F) | 3.2.2, 3.1.3 |
| 3.2.8 | Alerta de stock crítico | Alerta visual cuando `existencia <= nivel_mínimo`. | `templates/inventory/partials/stock_alert_badge.html`. | A44 | Diego Galindo (B) + Yahir Enríquez (F) | 3.2.4, 3.2.5–3.2.7 |
| 3.2.9 | Pruebas unitarias M-INV | Casos de prueba de descuento, compra, merma y alerta. | `apps/inventory/tests.py`, `apps/catalog/tests.py`. | — | Diego Galindo (+ Jesús Hernández en pruebas de `deduct_for_sale`) | 3.2.1–3.2.8 |

### 3.3 Módulo M-PDV — Punto de venta

| Código | Nombre | Descripción | Entregable verificable | RF/RNF | Responsable(s) | Dependencias |
|---|---|---|---|---|---|---|
| 3.3.1 | Selección de platillos y armado del pedido | Listado de los platillos disponibles por categoría y construcción del pedido en curso a partir de ellos: agregar y quitar líneas, ajustar cantidades y ver el resumen actualizado por el servidor. Fusiona los antiguos 3.3.1 y 3.3.2 (DEC-12). | `apps/pos/views.py` (`dish_list`, `order_builder`, `add_item`, `remove_item`), `templates/pos/order_builder.html`, `partials/dish_list.html`. | A31 | Jared Beltrán (B) + Alejandro Tarín (F) | 3.2.1, 2.1 |
| 3.3.3 | Aplicar modificadores | Exclusión/adición de ingredientes por línea de pedido. | `apps/pos/models.py` (`Modifier`), endpoints en `apps/pos/views.py`, interfaz en `templates/pos/`. | A32 | Jesús Hernández (modelo) + Jared Beltrán (B) + Alejandro Tarín (F) | 3.3.1 |
| 3.3.4 | Calcular total | Cálculo del importe total del pedido aplicando modificadores, en el servidor (Python). | `apps/pos/services_pricing.py` (`calcular_total`, nombres en español por DEC-01). | A33; ligado a RF-12 | Jesús Hernández | 3.3.3 |
| 3.3.5 | Confirmar venta | Registro del cobro (requiere turno de caja abierto), inmutabilidad de la venta confirmada y generación de la orden para cocina. | `apps/pos/services.py` (`confirm_sale`), `partials/order_summary.html`. | A34 | Jesús Hernández (servicio) + Jared Beltrán (B) + Alejandro Tarín (F) | 3.3.4, 3.1.3, 3.5.1 |
| 3.3.6 | Pruebas unitarias M-PDV | Casos de prueba de selección, armado, modificadores, cálculo, confirmación y ajustes. | `apps/pos/tests.py`. | — | Jared Beltrán (+ Jesús Hernández en pruebas de servicios y paridad) | 3.3.1, 3.3.3–3.3.5, 3.3.8 |
| 3.3.8 | Ajuste y cancelación de venta | Ajuste o cancelación con motivo (`error_captura`, `devolucion`, `correccion_pago`) que deja rastro y referencia a la venta original. El motivo decide si se revierten dinero y/o inventario. | `apps/pos/services.py` (`cancel_sale`, `adjust_sale`), `SaleAdjustment`, control "Cancelar / ajustar" en `partials/order_summary.html`. | Regla de negocio 11 | Jesús Hernández (servicio y modelo) + Jared Beltrán (B) + Alejandro Tarín (F) | 3.3.5, 3.2.6 |

> **Código retirado:** 3.3.2 ("Armar pedido") se fusionó en 3.3.1 el 24-sep-2026 (DEC-12). El código no se reutiliza.
> **En evaluación:** 3.3.7 (vista de cocina) está fuera de la línea base; ver la sección 2-bis (DEC-15).

### 3.4 Operación offline y sincronización

> **Todo paquete de este bloque requiere programación en pareja obligatoria** (mitigación de concentración de conocimiento, ADR-02 sección 6) y debe leerse `ADR-02-operacion-offline-SGFT.md` completo antes de tocar código aquí. En 3.4.9 la pareja aplica a la parte backend; su pantalla es solo en línea y no toca `static/pos/`.

| Código | Nombre | Descripción | Entregable verificable | RF/RNF | Responsable(s) | Dependencias |
|---|---|---|---|---|---|---|
| 3.4.1 | PWA shell (manifest + registro del service worker) | Manifiesto web y registro del service worker para instalar SGFT en pantalla de inicio. | `static/pos/manifest.json`, registro de `sw.js`. | RNF-08 | Alejandro Tarín + Yahir Enríquez | 3.3.6 |
| 3.4.2 | Cacheo de la aplicación con Workbox | Precaching de HTML/CSS/JS del PDV vía Workbox cargado por CDN dentro del service worker. | `static/pos/sw.js` con `workbox.precaching.precacheAndRoute(...)`. | RNF-08 | Alejandro Tarín + Yahir Enríquez | 3.4.1 |
| 3.4.3 | Almacén local IndexedDB/Dexie | Copia local del catálogo, recetas, precios, cola de ventas y de aperturas pendientes, estado de turno cacheado. | `static/pos/db.js` (cola única de operaciones con campo `tipo`, DEC-03). | RF-07 | Alejandro Tarín + Yahir Enríquez | 3.4.1 |
| 3.4.4 | Lógica de pedido en cliente (Alpine.js) | Armado de pedido, modificadores y cálculo del total sin servidor. | `pricing.js` (parte del cliente), plantillas del PDV con `x-data`. | RF-07 | Alejandro Tarín + Yahir Enríquez | 3.4.3, 3.3.3 |
| 3.4.5 | Prueba de paridad de precios Python/JS | Fixture compartido y pruebas en ambos lenguajes que garantizan que `pricing.js` y `services_pricing.py` calculan lo mismo al centavo. | `tests_fixtures/pricing_cases.json`, `apps/pos/tests.py` (`PricingParityTest`), `tests_e2e/parity/test_pricing.mjs`, job en GitHub Actions. | ADR-02 acción 6 (obligatoria antes de escribir la primera línea de precios offline) | Jesús Hernández + Alejandro Tarín (+ Jared Beltrán, job de CI) | 3.3.4, 3.4.4 |
| 3.4.6 | Endpoint de sincronización POST /pos/sync/ | Recepción del lote, validación de UUID, aplicación en transacción atómica, cuarentena, respuesta al dispositivo. | `apps/pos/views.py` (`sync_operations`) conforme a `docs/decisiones/contrato-sync-pdv.md` versión 1; campos nuevos de `Sale` (total cobrado, total del servidor, indicador de diferencia de precio). | RF-07, RNF-08 | Jesús Hernández + Jared Beltrán | 3.4.5, 3.2.6 |
| 3.4.7 | Apertura de turno de caja offline | Apertura de turno con UUID propio, operable sin conexión, sincronizada por el mismo mecanismo que una venta. El cierre, solo en línea, es el paquete 3.5.7. | `apps/pos/services_cash_session.py` (`open_session`), `CashRegisterSession`, `QuarantinedCashSession`. | A51 | Jesús Hernández (servicio) + Alejandro Tarín (F) | 3.4.6, 3.5.1 |
| 3.4.8 | Pruebas E2E offline (Playwright) | Flujo crítico de venta con y sin conexión, y apertura de caja sin conexión. | `tests_e2e/test_pos_sale.py`, `tests_e2e/test_cash_session_open.py`. | — | Yahir Enríquez + Jared Beltrán | 3.4.6, 3.4.7 |
| 3.4.9 | Bandeja de revisión del Administrador | Resolución en línea de ventas y aperturas en cuarentena (aplicar con el catálogo actual, aplicar sin descontar inventario o descartar) y revisión de insumos en existencia negativa y de ventas con diferencia de precio. | `apps/pos/services.py` (resolución), vistas en `apps/pos/views.py`, `templates/pos/review/`. | Reglas de negocio 9 y 10; DEC-02 | Jesús Hernández + Jared Beltrán (pareja, B) + Yahir Enríquez (F) | 3.4.6, 3.2.6, 3.1.3 |

### 3.5 Módulo M-REP — Caja y reportes (A5)

> **Nota de renumeración:** la lista entregada por el equipo repetía el código 3.5.5 en dos paquetes distintos ("Productos más vendidos" y "Pruebas unitarias M-REP") y ubicaba "Exportar reportes" fuera de secuencia. Se renumeró de forma consecutiva a continuación; el contenido y alcance de cada paquete no cambió.

| Código | Nombre | Descripción | Entregable verificable | RF/RNF | Responsable(s) | Dependencias |
|---|---|---|---|---|---|---|
| 3.5.1 | Abrir turno de caja | Declaración de efectivo inicial, validación de que no haya un turno ya abierto. | `apps/pos/services_cash_session.py` (`open_session`, en línea). | A51 | Jesús Hernández (servicio) + Jared Beltrán (B) + Alejandro Tarín (F) | 3.1.3 |
| 3.5.2 | Calcular corte de caja | Consolidado de ventas del turno por método de pago; reporta descuadre sin bloquear el cierre; exige cola de sincronización vacía. | `apps/reports/services.py` (`cash_close`). | A52 | Jesús Hernández (servicio) + Jared Beltrán (B) + Yahir Enríquez (F) | 3.5.1, 3.5.7, 3.4.6 |
| 3.5.3 | Reporte de ventas por periodo | Consulta de ventas filtrable por periodo, restringida al Administrador. | `apps/reports/services.py` (`sales_by_period`). | A53 | Jared Beltrán (B) + Yahir Enríquez (F) | 3.3.5 |
| 3.5.4 | Productos más vendidos | Identificación de los platillos con mayor volumen de venta en un periodo. | `apps/reports/services.py` (`top_dishes`). | A54 | Jared Beltrán (B) + Yahir Enríquez (F) | 3.3.5, 3.2.6 |
| 3.5.5 | Exportar ventas del día a PDF | Generación de un documento PDF descargable con las ventas de una jornada: encabezado (fecha, turno, quién lo generó y cuándo), detalle de cada venta (hora del dispositivo, platillos y cantidades, método de pago, importe), ajustes y cancelaciones con su motivo, y totales por método de pago y general. Las ventas se atribuyen al día por la marca de tiempo del dispositivo (regla 7). Igual que el corte, se niega a generarse mientras haya operaciones pendientes de sincronizar y muestra cuántas faltan (regla 5). Restringido al Administrador. Solo en línea. | `apps/reports/services.py` (`export_daily_sales_pdf`), botón de exportación en la vista de reportes, dependencia de generación de PDF justificada en el PR. | — (RF pendiente de 1.3.1) | Jared Beltrán (B) + Yahir Enríquez (F) | 3.3.5, 3.3.8, 3.5.1 |
| 3.5.6 | Pruebas unitarias M-REP | Casos de prueba de apertura, corte, descuadre, reportes, exportación y cierre de turno. | `apps/reports/tests.py`. | — | Jared Beltrán (+ Jesús Hernández en pruebas de `cash_close`) | 3.5.1–3.5.5, 3.5.7 |
| 3.5.7 | Cerrar turno de caja | Declaración del efectivo final contado, cálculo del esperado y de la diferencia (se registra sin bloquear el cierre). Se niega a cerrar mientras haya operaciones pendientes de sincronizar. Solo en línea. | `apps/pos/services_cash_session.py` (`close_session`), vista `close_cash_session`, `templates/pos/cash_session_close.html`. | A5; reglas de negocio 5 y 13 | Jesús Hernández (servicio) + Jared Beltrán (B) + Yahir Enríquez (F) | 3.5.1, 3.4.6 |

### 4. Control de calidad

| Código | Nombre | Descripción | Entregable verificable | RF/RNF | Responsable(s) | Dependencias |
|---|---|---|---|---|---|---|
| 4.1 | Cobertura de pruebas unitarias consolidada | Revisión de que cada RF implementado tenga al menos un caso de prueba. | Resumen de cobertura por módulo en `docs/calidad/cobertura-sprint-N.md` + reporte del job de CI. | — | Jared Beltrán + Yahir Enríquez | 3.1.4, 3.2.9, 3.3.6, 3.4.8, 3.5.6 |
| 4.2 | Revisión de código (PR obligatorio) | Ningún push directo a `main`. Todo PR requiere la aprobación del integrador, la revisión de rutas y pruebas en verde. Solo el integrador fusiona. Los dueños de cada ruta reciben la solicitud de revisión automáticamente. | Historial de Pull Requests con aprobación registrada; `.github/CODEOWNERS` con el integrador en todas las rutas; dos rulesets en `main` (solo el integrador fusiona; PR, code owners y CI obligatorios); revisión de rutas con `dueno_de_ruta.py --revisar` en CI (DEC-10, DEC-16, DEC-18). | `CLAUDE.md` sección 8 | Alejandro Tarín (integrador: aprueba y fusiona todos los PR) | Continuo, desde el primer PR |
| 4.3 | Matriz de trazabilidad de requisitos a casos de prueba | Verificar que cada RF-nn/RNF-nn del apartado 3 tenga al menos un caso de prueba que lo cubra — es una actividad de verificación técnica, no de gestión de alcance. | Matriz RF/RNF → caso de prueba, apéndice del SRS. | — | Jesús Hernández | 1.3.1, 4.1 |
| 4.4 | Verificación de seguridad | Confirmar contraseñas hasheadas, CSRF activo, autorización revalidada en servidor (incluidas las operaciones sincronizadas desde offline), variables sensibles fuera del repositorio — checklist contra ADR-01 sección 8 y `CLAUDE.md` sección 10, alineado a OWASP Top 10:2021. | Checklist de seguridad firmado antes del despliegue a producción, en `docs/calidad/checklist-seguridad.md`. | RES-07; OWASP Top 10:2021 | Jesús Hernández | 3.1.2, 3.1.3, 3.4.6 |
| 4.5 | Datos de prueba ficticios y coherentes con el menú real | Conjunto de datos de prueba ficticios pero coherentes con el menú real (burritos, guisados, bebidas), para desarrollo y demostración sin usar datos reales del negocio. | Fixtures en `apps/<app>/fixtures/*.json` (el repositorio es público: nunca datos reales). | `CLAUDE.md` sección 11 | Yahir Enríquez | 3.1.1, 3.2.1–3.2.3 |
| 4.6 | Pruebas E2E críticas en CI (venta PDV, corte de caja) | Ejecución de los dos flujos end-to-end acordados (venta completa en PDV, corte de caja) dentro del pipeline. | Job de Playwright en GitHub Actions. | ADR-01 | Yahir Enríquez (+ Jared Beltrán, workflow) | 3.4.8, 5.1 |

### 5. Integración, CI/CD y despliegue

| Código | Nombre | Descripción | Entregable verificable | RF/RNF | Responsable(s) | Dependencias |
|---|---|---|---|---|---|---|
| 5.1 | Pipeline de GitHub Actions | Ejecución automática de `manage.py test` y `node --test` en cada Pull Request. | Workflow `.github/workflows/`. | `CLAUDE.md` sección 6 | Jared Beltrán | 3.1.4 |
| 5.2 | Entornos gestionados (PostgreSQL Neon/Supabase, variables de entorno) | Configuración de PostgreSQL en Neon/Supabase y variables de entorno (`.env.example`). | `.env.example`, cadena `DATABASE_URL` documentada (sin valores reales en el repo). | RES-02 | Jesús Hernández | 3.1.1 |
| 5.3 | Despliegue en Render/Railway | Servicio Django con Gunicorn + Whitenoise, `collectstatic` y migraciones automatizadas al fusionar a `main`. | Servicio desplegado y accesible por URL. | RES-05 | Jesús Hernández + Alejandro Tarín | 5.1, 5.2, 3.4.6 |
| 5.4 | Spike de validación offline (Sprint 1) | Prueba de concepto con Workbox: catálogo en caché, pedido creado sin red, cola persistente, sincronización con UUID, descuento aplicado en servidor. | Resultado documentado del spike en `docs/decisiones/spike-offline-sprint1.md` (criterio de éxito en `revision-tecnica-offline-SGFT.md`); el código queda en la rama `spike/offline-workbox`. | ADR-02 | Alejandro Tarín + Jared Beltrán | 3.4.1–3.4.3 |

---

## 2-bis. Paquetes en evaluación (fuera de la línea base)

Paquetes definidos y con responsables asignados, pero que **no forman parte del alcance comprometido** ni suman a la estimación mientras el equipo no decida implementarlos. Si se aprueban, entran por control de cambios (lo administra el Scrum Master y lo autoriza el cliente, SRS 1.1.2) con el código ya reservado; si se descartan, el código se retira.

| Código | Nombre | Descripción | Entregable verificable | RF/RNF | Responsable(s) (distribución por capas) | Dependencias |
|---|---|---|---|---|---|---|
| 3.3.7 | Vista de cocina (pedidos pendientes) | Sección de la aplicación, al mismo nivel que Punto de venta o Inventario, donde el Cocinero consulta los pedidos pendientes con sus personalizaciones y los marca como preparados. Si se implementa, sigue lo decidido en ADR-02: se usa en el mismo dispositivo del cajero y también funciona sin conexión, leyendo la cola local. | `apps/pos/views.py` (`kitchen_queue`, `mark_prepared`), `templates/pos/kitchen_queue.html`, `partials/kitchen_order.html`, estado "preparado" en `Order`, lectura de la cola local en `static/pos/db.js`. | RF-17; prioridad candidata "Debería" (SRS 1.1.3) | Jesús Hernández (modelo) + Jared Beltrán (B) + Alejandro Tarín (F, en pareja con Yahir Enríquez para la parte offline) | 3.3.5, 3.4.3 |

## 3. Supuestos y vacíos detectados en la documentación fuente

1. **No existe todavía el apartado 3 del SRS** (catálogo formal de requisitos RI-nn/RF-nn/RNF-nn/RN-nn/RT-nn/RL-nn) entre los documentos consultados. Redactarlo (paquete 1.3.1) sigue siendo la actividad de mayor apalancamiento antes de tomar este WBS como definitivo.
2. **ADR-01 y ADR-02 ya no aparecen como paquetes de trabajo propios** en esta revisión (se retiraron por instrucción del equipo al entregar la nueva jerarquía). Ambos documentos de decisión permanecen ratificados y siguen siendo insumo obligatorio para los paquetes de 3.4 (offline) y 4.4 (seguridad); si el equipo necesita seguimiento explícito de acciones abiertas de ADR-02 (por ejemplo, confirmación de límites de iOS con el cliente), conviene registrarlo fuera del WBS, dado que es coordinación con el cliente y no construcción de producto.
3. ~~**3.3.1 y 3.3.2 como paquetes separados.**~~ **Resuelto (DEC-12):** se fusionaron en 3.3.1 y el código 3.3.2 queda retirado. Ver el punto 7 de la lista de cambios.
4. **La numeración de 3.5 traía una inconsistencia** (código 3.5.5 duplicado, "Exportar reportes" fuera de secuencia) — se corrigió de forma consecutiva en este documento (ver nota en la sección 3.5 del diccionario); vale la pena que el equipo confirme que esta corrección refleja el orden que tenían en mente.
5. **3.5.5 tiene alcance definido (DEC-13)** — exportar las ventas del día a PDF —, pero todavía no tiene RF-nn: su código de requisito lo asigna el apartado 3 del SRS (1.3.1). La biblioteca para generar el PDF es una dependencia nueva que se justifica en el PR (`CLAUDE.md` §11) y aprueba Jesús Hernández como dueño de `requirements.txt`. Se recomienda ReportLab: licencia BSD y sin dependencias del sistema operativo, así que no complica el despliegue en Render o Railway.
6. **A1 (M-USR) sigue sin descomposición de tercer nivel en el SADT, y así debe quedar.** Se revisó de nuevo y la justificación del 11-sep-2026 se sostiene: el módulo tiene dos actividades (administrar cuentas; autenticar y restringir por rol) y la notación exige de tres a seis cajas. Una tercera caja sin salida propia sería artificial. La descomposición que sí faltaba era la del WBS: la administración de cuentas no tenía paquete, y ahora es 3.1.5 (DEC-14). Si en el futuro se agrega una tercera actividad con salida propia, como la recuperación de contraseña o una bitácora de accesos, A1 se abre.
7. **No existe todavía una estimación de tiempos/horas ni un WBS con PERT** — es, precisamente, el paso siguiente ahora que el equipo validó los responsables de esta revisión.
8. **Los paquetes nuevos 3.3.8, 3.4.9 y 3.5.7 se sustentan en reglas de negocio de `CLAUDE.md`, no en RF-nn confirmados.** Igual que 3.5.5, sus códigos de requisito dependen del apartado 3 del SRS (1.3.1).
9. **Vista de cocina (3.3.7) — en evaluación (DEC-15).** Sustituye al supuesto anterior. La vista es una sección más de la aplicación, como Punto de venta o Inventario. Como el equipo aún no decide si la implementará, está en la sección 2-bis, fuera de la línea base.

   **Qué implica no implementarla.** La consulta de órdenes por cocina (RF-17) y el rol de Cocinero están hoy dentro del alcance aprobado (`CLAUDE.md` §3 y §4). Sin esta vista, el Cocinero no tendría ninguna función en el sistema. Por eso la decisión no es solo del equipo:
   - al redactar el catálogo de requisitos (1.3.1), RF-17 se clasifica como "Debería" y no como "Deberá";
   - si al final se descarta, se tramita como cambio de alcance autorizado por el cliente (SRS 1.1.2), y ese mismo cambio decide si el rol de Cocinero se elimina. Eso afecta al modelo de usuario (3.1.1), al RBAC (3.1.3), a las características de usuario del SRS (1.2.3) y al manual (1.7).

   **Recomendación:** decidirlo al redactar 1.3.1, antes de implementar 3.1.1. Así los roles se definen desde el inicio y no hace falta una migración posterior.

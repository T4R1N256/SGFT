# Registro de decisiones y pendientes

Las decisiones que estaban abiertas en la primera versión de esta skill se cerraron el **24 de septiembre de 2026**. Este archivo dice qué se decidió, dónde está documentado y qué acciones quedan por ejecutar (ninguna es una decisión abierta).

Los documentos completos están en `assets/repo/docs/decisiones/`, listos para copiarse a `docs/decisiones/` del repositorio.

## 1. Decisiones vigentes

| ID | Decisión | Documento |
|---|---|---|
| DEC-01 | Módulo de precios y lote de sincronización en español: `calcular_total()` / `calcularTotal()`, llaves `precio_base_centavos`, `ajuste_centavos`, `total_esperado_centavos`… Excepción acotada a `CLAUDE.md` §9; el resto del código sigue en inglés. | `nombres-modulo-precios.md` |
| DEC-02 | Total recalculado ≠ total cobrado al sincronizar → se registra lo cobrado, se guarda el total del servidor y la venta se marca para revisión (no cuarentena). | `contrato-sync-pdv.md` §1 |
| DEC-03 | Lote de sincronización: un solo arreglo `operaciones` con campo `tipo`; el servidor aplica primero aperturas y luego ventas, por marca de tiempo del dispositivo. | `contrato-sync-pdv.md` §1, §3 |
| DEC-04 | Llaves del lote en español, las mismas del pedido que recibe `calcular_total()`. | `contrato-sync-pdv.md` §2 |
| DEC-05 | Cualquier usuario con sesión sincroniza; el servidor revalida el rol del `usuario_id` de cada operación (si no lo tiene → cuarentena). Sin sesión → 401 y la cola se conserva. | `contrato-sync-pdv.md` §3 |
| DEC-06 | Respuesta HTTP 200 con estado por UUID (`aplicada`, `aplicada_con_revision`, `duplicada`, `cuarentena`); 400/401/403/413 solo para errores del lote completo. | `contrato-sync-pdv.md` §4 |
| DEC-07 | Paquetes nuevos: 3.3.8 Ajuste y cancelación de venta · 3.4.9 Bandeja de revisión del Administrador · 3.5.7 Cerrar turno de caja. También se dio de alta 3.3.7 Consulta de pedidos en cocina, que después pasó a evaluación (DEC-15). Sin renumerar los existentes; 3.4.7 pasa a "Apertura de turno de caja offline". | `organizacion-repositorio.md` |
| DEC-08 | Un solo `tests.py` por app; se convierte en paquete `tests/` solo tras dos o más conflictos de fusión en un Sprint. | `organizacion-repositorio.md` |
| DEC-09 | Ubicaciones antes propuestas quedan aprobadas; ramas `feat/WBS-x.y.z-…` y commits `feat(WBS-x.y.z): …` hasta que existan los RF. | `organizacion-repositorio.md` |
| DEC-10 | CODEOWNERS activo con revisión obligatoria de code owners en `main` (repositorio público, GitHub Free); al menos dos personas por ruta. | `organizacion-repositorio.md` |
| DEC-11 | Se publica el WBS Revisión 4 con responsables por capas y los paquetes de DEC-07. | `organizacion-repositorio.md` |
| DEC-12 | 3.3.1 y 3.3.2 se fusionan en **3.3.1 Selección de platillos y armado del pedido**: misma pantalla, mismos responsables, mismo flujo de prueba y una sola caja SADT (A31). El código 3.3.2 queda retirado y no se reutiliza. | `organizacion-repositorio.md` |
| DEC-13 | **3.5.5 = exportar las ventas del día a PDF** (definición del equipo). Contiene el detalle de ventas, los ajustes con motivo y los totales por método de pago; se atribuye por marca de tiempo del dispositivo; se niega con operaciones pendientes de sincronizar (regla 5); solo Administrador. Función `export_daily_sales_pdf()`; biblioteca recomendada ReportLab, a justificar en el PR. | `organizacion-repositorio.md` |
| DEC-14 | La caja A1 del SADT **no se descompone** (dos actividades; la notación exige de tres a seis cajas). Lo que faltaba era un paquete en el WBS para la administración de cuentas: **3.1.5 Administración de cuentas de personal** (Diego B, Yahir F). | `organizacion-repositorio.md` |
| DEC-15 | **Vista de cocina (3.3.7) en evaluación.** Es una sección más de la app, como Punto de venta o Inventario. Queda fuera de la línea base con prioridad candidata "Debería" (SRS 1.1.3); sus rutas y responsables están reservados, pero sus archivos no se crean hasta que se apruebe. Como RF-17 y el rol de Cocinero están en el alcance aprobado, descartarla requiere un cambio de alcance autorizado por el cliente que también decida el destino de ese rol. Se recomienda decidir al redactar 1.3.1, antes de implementar 3.1.1. | `organizacion-repositorio.md`, supuesto 9 del WBS |
| DEC-16 | **Tarín es el integrador:** valida las rutas de cada PR y es el único que fusiona en `main`. Los code owners siguen aprobando el contenido, y Tarín no se agrega como code owner de todo para no sustituir esa revisión. `main` se protege con **dos rulesets**: uno restringe quién actualiza la rama, con excepción *solo mediante PR* para el administrador (Tarín); otro exige PR, aprobación de code owners y CI, sin excepciones. Usuarios de GitHub: Tarín `T4R1N256`, Diego `Diego-Galindo98`, Jesús `EduardGarrido`, Jared `JBeltra16`, Yahir `CodigaBorealis`. | `organizacion-repositorio.md` |
| DEC-17 | **Nombres de archivos y carpetas de código y pruebas en inglés.** La app `pdv` se renombra a **`pos`** (*point of sale*) en carpetas (`apps/pos/`, `static/pos/`, `templates/pos/`), URLs (`/pos/…`, contrato `POST /pos/sync/`) y nombres de URL (`pos:add_item`). `templates/pos/revision/` pasa a `review/` y las pruebas E2E a `test_pos_sale.py`, `test_cash_session_open.py` y `test_cash_close.py`. La documentación (`docs/`) y la skill **conservan sus nombres**; su contenido se actualiza donde cita rutas de código. Se hizo antes de la primera migración de `pos`: después, el nombre de la app quedaría en las tablas (`pos_sale`…) y en las migraciones. No afecta a DEC-01, porque se refiere a identificadores dentro de los archivos. | `organizacion-repositorio.md` |
| DEC-18 | **Tarín aprueba todos los PR.** Figura en todas las rutas de `CODEOWNERS` (campo `aprobador_general` del mapa), así que su aprobación cumple el requisito de code owners para cualquier archivo; los dueños reciben la solicitud de revisión, pero ya no se exige su aprobación. Sus propios PR los aprueba otra persona de la ruta, porque GitHub no deja aprobar el PR propio. Sustituye la parte de DEC-16 que reservaba la aprobación de contenido al dueño; lo demás de DEC-16 (solo Tarín fusiona, dos rulesets) sigue vigente. | `organizacion-repositorio.md` |

Además siguen vigentes las resoluciones de la primera versión: el árbol de `estructura-y-flujo-datos-SGFT.md` es el canónico (no `src/` de `CLAUDE.md` §7); `apps/core/mixins.py` es de Jesús; `static/pos/*.js` son la única excepción a "no hay `.js` propios"; toda app con vistas lleva `urls.py`.

## 2. Acciones pendientes (no son decisiones)

| # | Acción | Responsable |
|---|---|---|
| P1 | Copiar `assets/repo/` al repositorio (`.github/CODEOWNERS`, `.github/pull_request_template.md`, los tres documentos de `docs/decisiones/`) y la skill completa en `.claude/skills/sgft-organizacion-entregables/`. | Tarín |
| P2 | ~~Definir usuarios de GitHub~~ (hecho, DEC-16). Falta dar permiso de escritura a los cinco y asegurar que Tarín sea el único administrador del repositorio. | Tarín |
| P3 | Configurar los dos rulesets de `main` y agregar la revisión de rutas al CI (pasos en `organizacion-repositorio.md`, DEC-16; el paso de CI lo agrega Jared en 5.1). | Tarín (+ Jared) |
| P4 | Corregir `CLAUDE.md` §7 (árbol `apps/`), §8 (`services_pricing.py`) y §9 (excepción DEC-01). | Diego |
| P5 | Corregir `estructura-y-flujo-datos-SGFT.md` §1 (quitar `calculate_total()` de `services.py`) y `revision-tecnica-offline-SGFT.md` §4 (ruta `apps/pos/services_pricing.py`). | Diego |
| P6 | Reemplazar `WBS-SGFT.md` por la Revisión 4 y actualizar el diccionario en Word con los mismos datos. | Diego |
| P7 | Agregar a `Sale` los campos que exige el contrato (total cobrado, total del servidor, indicador de diferencia, dos marcas de tiempo, UUID único). | Jesús (3.4.6) |
| P8 | Definir cómo se guarda la cantidad de insumo de un modificador "agregar" (el lote solo envía `insumo_id`). | Jesús (3.3.3) |
| P9 | Actualizar las rutas `pdv` → `pos` en los documentos del equipo (DEC-17): `estructura-y-flujo-datos-SGFT.md` (22 menciones), `revision-tecnica-offline-SGFT.md` (12), `convencion-htmx-alpine-SGFT.md` (10, incluidos los `{% url 'pdv:…' %}` de los ejemplos), `ADR-02` (3), `CLAUDE.md` (2) y `stack-tecnico-explicacion` (1). Agregar a `CLAUDE.md` §9 la regla de nombres de archivo en inglés y el término `pos` en el glosario. Los nombres de los documentos no cambian. | Diego |

## 3. Acciones abiertas que no pertenecen a esta skill

Siguen abiertas en ADR-02 y no dependen de la organización del repositorio. Las tres son coordinación con el cliente y le corresponden al Product Owner (Diego), que las registra en minuta:

- **Definir con el cliente la vista de cocina (3.3.7).** Hoy está en el alcance que el cliente validó (RF-17). Si el equipo la clasifica como "Debería" o la descarta, el cliente debe autorizarlo, y con eso se decide también si el rol de Cocinero se conserva. Si se implementa, el cliente debe aceptar que se consulta en el mismo teléfono del cajero (ADR-02).
- **Aceptación escrita de las limitaciones de iOS**: sin sincronización en segundo plano, y el almacenamiento local puede desalojarse.
- **Recorte formal** de RF-23, RF-24 y RNF-15.

Si alguien pregunta por ellas, dirígelo a ADR-02 §9 y al supuesto 9 del WBS.

## 4. Cómo registrar una decisión nueva

1. Redacta el documento en `docs/decisiones/` con fecha, contexto, decisión, alternativas y consecuencias.
2. Si cambia un dueño o una ubicación, edita `assets/ownership.json`, corre `python scripts/dueno_de_ruta.py --verificar` y regenera CODEOWNERS.
3. Agrega una fila a la tabla de la sección 1 con el siguiente ID (`DEC-19`…).

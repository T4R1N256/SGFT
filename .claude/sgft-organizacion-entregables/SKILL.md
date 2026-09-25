---
name: sgft-organizacion-entregables
description: Mapa de propiedad y ubicación de entregables del proyecto SGFT (Sistema de Gestión de Food Truck "El Pardo", Django + HTMX + Alpine + PWA offline). Indica la ruta exacta del repositorio donde va cada modelo, servicio, vista, plantilla, parcial, archivo estático, prueba o documento, y qué integrante es dueño, pareja o revisor (Jesús backend y BD; Diego y Jared backend; Tarín y Yahir frontend), ligado al paquete del WBS. Úsala siempre que alguien del equipo pregunte dónde crear o guardar algo, a quién le toca o quién revisa un paquete WBS (por ejemplo 3.3.1 o 3.4.6), qué le corresponde a una persona, cómo repartir un paquete entre backend y frontend, cómo nombrar una rama, cómo configurar CODEOWNERS, qué dice el contrato de sincronización offline o qué se decidió sobre la organización del repositorio, o antes de escribir cualquier código o documento del SGFT, aunque no diga explícitamente entregable, responsable o estructura.
---

# SGFT — Organización de entregables: qué hace cada quien y dónde va

## Propósito

Esta skill convierte tres documentos del proyecto (`estructura-y-flujo-datos-SGFT.md`, `WBS-SGFT.md` Rev. 3 y `convencion-htmx-alpine-SGFT.md`) en una respuesta única y consistente a dos preguntas que el equipo se hará cientos de veces:

1. **¿Dónde va esto?** — la ruta exacta en el repositorio.
2. **¿De quién es?** — dueño, pareja y revisor, bajo la distribución por capas acordada.

Sin una respuesta única, cinco personas trabajando en el mismo repositorio Django producen archivos duplicados, migraciones en conflicto, reglas de negocio escritas en plantillas y PR revisados por quien no conoce el código. La skill existe para evitar esos cuatro problemas.

Todas las decisiones de organización están cerradas desde el 24-sep-2026 (DEC-01 a DEC-23, en `references/decisiones-y-pendientes.md`). La skill trae además un **kit para el repositorio** en `assets/repo/`: CODEOWNERS, la plantilla de PR y los tres documentos de decisión, listos para copiarse.

## Equipo y distribución por capas

| Clave   | Integrante      | Capa                    | Rol Scrum                                                     |
| ------- | --------------- | ----------------------- | ------------------------------------------------------------- |
| `jesus` | Jesús Hernández | Backend + base de datos | Desarrollo                                                    |
| `diego` | Diego Galindo   | Backend                 | Product Owner / analista                                      |
| `jared` | Jared Beltrán   | Backend                 | Desarrollo                                                    |
| `tarin` | Alejandro Tarín | Frontend                | Scrum Master · **integrador**: aprueba y fusiona todos los PR |
| `yahir` | Yahir Enríquez  | Frontend                | Desarrollo                                                    |

Esta distribución es la de la **WBS Revisión 4** (DEC-11), que reemplaza los responsables sugeridos de la Rev. 3. Los cambios y su justificación están en `references/matriz-wbs-responsables.md` §6. Cuando respondas, si el responsable que das difiere del que decía la Rev. 3, dilo: parte del equipo puede tener la versión anterior en la cabeza.

## Principios de propiedad (y por qué existen)

**1. Un archivo, un dueño.** Cada ruta tiene exactamente un dueño que aprueba sus cambios. Otros pueden escribir en ella, pero siempre por PR que el dueño revisa. Sin esto, nadie responde por el estado de un archivo cuando falla.

**2. Dueño del archivo ≠ autor de una función.** Algunas funciones viven, por diseño de la arquitectura, en archivos de otra persona: `deduct_for_sale()` (Jesús) dentro de `inventory/services.py` (Diego); `cash_close()` (Jesús) dentro de `reports/services.py` (Jared); `sync_operations()` (Jesús + Jared) dentro de `pos/views.py` (Jared). El autor escribe la función; el dueño revisa el PR. No se mueven las funciones a otro archivo para "evitar" esto: su ubicación viene de la regla de dependencias entre apps.

**3. El esquema de datos tiene un solo dueño: Jesús.** Todos los `models.py` y `migrations/` son suyos. Las migraciones de Django generadas por varias personas en paralelo son la causa más común de conflictos irresolubles en equipos pequeños. Quien necesite un campo lo pide por issue o por PR a `models.py`; Jesús genera la migración. Nunca se modifica una migración ya aplicada.

**4. Lo transaccional es de Jesús; lo HTTP, del backend de la app; lo visible, del frontend.** Dentro de cada app el reparto sigue la separación de `estructura-y-flujo-datos` §2: `services.py` implementa la regla de negocio (y abre `transaction.atomic()`), `views.py` solo hace HTTP (rol, plantilla, llamada al servicio) y las plantillas solo presentan.

**5. La costura backend↔frontend es un contrato escrito.** La vista declara en su docstring qué plantilla renderiza y con qué contexto; la plantilla solo usa ese contexto. Ver `references/contrato-vista-plantilla.md`. Entre el cliente offline y el servidor, el contrato es `contrato-sync-pdv.md` v1.

**6. El módulo offline nunca tiene un solo autor.** Todo `static/pos/` se programa en pareja (Tarín conduce, Yahir es segundo autor) por la mitigación de concentración de conocimiento de ADR-02 §6. Quien lo toque debe haber leído ADR-02 completo.

**7. Las reglas de dependencia deciden la app, no la conveniencia.** `pos` puede importar de `inventory`; `inventory` nunca importa de `pos`; `reports` solo lee; `catalog` y `accounts` no dependen de nadie. Si una ubicación viola esto, la ubicación está mal aunque "funcione".

**8. Toda ruta tiene al menos dos personas que pueden aprobarla.** Con la revisión obligatoria de code owners en `main` (DEC-10), el autor de un PR no puede aprobarlo; por eso cada ruta lista una segunda persona. En `models.py` esa segunda persona (Diego) solo aprueba los PR de Jesús: nadie más edita el esquema.

**9. Tarín es el integrador: aprueba y fusiona todos los PR (DEC-16, DEC-18).** Figura en todas las rutas de `CODEOWNERS`, así que su aprobación basta para cualquier archivo, y es el único que fusiona en `main`. Los dueños siguen recibiendo la solicitud de revisión automáticamente, pero ya no se exige su aprobación. Los PR que abre el propio Tarín los aprueba otra de las personas listadas, porque GitHub no deja aprobar el PR propio. Toda ruta nueva fuera del mapa se le consulta a él.

## Mapa rápido de propiedad

Siglas: JH Jesús · DG Diego · JB Jared · AT Tarín · YE Yahir. `{+X}` pareja · `(rev X)` revisor obligatorio.

| Ruta                                                                                                | Dueño                                      | Paquetes WBS                                    |
| --------------------------------------------------------------------------------------------------- | ------------------------------------------ | ----------------------------------------------- |
| `config/`, `manage.py`, `requirements.txt`, `.env.example`                                          | JH                                         | 5.2                                             |
| `apps/*/models.py`, `apps/*/migrations/`                                                            | JH                                         | 3.1.1, 3.2.1–3.2.4, modelos de pos              |
| `apps/core/mixins.py`                                                                               | JH                                         | 3.1.3                                           |
| `apps/core/templates/base.html`, `apps/core/templatetags/`                                          | AT (rev YE / JH)                           | 2.1                                             |
| `apps/accounts/` — services, views, urls, admin, tests                                              | DG (rev JH)                                | 3.1.2, 3.1.4, 3.1.5                             |
| `apps/accounts/templates/accounts/`                                                                 | YE (rev AT)                                | 3.1.2, 3.1.5                                    |
| `apps/catalog/admin.py`, `tests.py`                                                                 | DG                                         | 3.2.1–3.2.3, 3.2.9                              |
| `apps/inventory/` — services, views, urls, tests                                                    | DG (rev JB); ⟂ `deduct_for_sale` = JH      | 3.2.5–3.2.9                                     |
| `apps/inventory/templates/inventory/`                                                               | YE (rev AT)                                | 3.2.5, 3.2.7, 3.2.8                             |
| `apps/pos/services.py`, `services_pricing.py` (`calcular_total`), `services_cash_session.py`        | JH                                         | 3.3.4, 3.3.5, 3.3.8, 3.4.9, 3.5.1, 3.4.7, 3.5.7 |
| `apps/pos/views.py`, `urls.py`, `tests.py`                                                          | JB (rev JH); ⟂ `sync_operations` = JH+JB   | 3.3.1–3.3.8, 3.4.6, 3.4.9, 3.5.7                |
| `apps/pos/templates/pos/` (incluye ajuste; cocina ⏸ en evaluación)                                  | AT (rev YE; pareja YE en `x-data` offline) | 3.3.1–3.3.5, 3.3.7, 3.3.8, 3.4.4, 3.5.1         |
| `apps/pos/templates/pos/review/`, `cash_session_close.html`                                         | YE (rev AT)                                | 3.4.9, 3.5.7                                    |
| `apps/reports/` — services, views, urls, tests                                                      | JB (rev JH); ⟂ `cash_close` = JH           | 3.5.2–3.5.6                                     |
| `apps/reports/templates/reports/`                                                                   | YE (rev AT)                                | 3.5.2–3.5.5                                     |
| `static/pos/` (manifest, sw.js, db.js, pricing.js)                                                  | AT {+YE} — pareja obligatoria              | 3.4.1–3.4.5                                     |
| `tests_fixtures/pricing_cases.json`                                                                 | JH + AT                                    | 3.4.5                                           |
| `tests_e2e/parity/`                                                                                 | AT (rev JH)                                | 3.4.5                                           |
| `tests_e2e/*.py`                                                                                    | YE {+JB}                                   | 3.4.8, 4.6                                      |
| `apps/<app>/fixtures/` (datos demo)                                                                 | YE (rev JH)                                | 4.5                                             |
| `.github/workflows/`                                                                                | JB (rev JH)                                | 5.1                                             |
| `docs/SRS.md`, `docs/entregas/`, `docs/decisiones/`                                                 | DG                                         | 1.1–1.4, 1.7                                    |
| `.github/CODEOWNERS`, `.github/pull_request_template.md`, `.claude/skills/`, rutas sin regla (`**`) | AT (rev DG) — integrador                   | 4.2                                             |
| `docs/decisiones/contrato-sync-pdv.md`, `nombres-modulo-precios.md`                                 | JH (+JB, AT)                               | 3.4.6, 3.3.4                                    |
| `docs/diagramas/`, `docs/calidad/checklist-seguridad.md`                                            | JH                                         | 1.5.1, 1.6.1, 4.4                               |
| `docs/prototipos/pdv-venta/`                                                                        | AT                                         | 2.2.1                                           |
| `docs/prototipos/usr-acceso/`, `inv-catalogo/`, `rep-caja/`                                         | YE (rev AT)                                | 2.2.2–2.2.4                                     |

Para el árbol completo con cada archivo: `references/arbol-repositorio-con-duenos.md`. Para la respuesta exacta de una ruta, usa el script (siguiente sección): es la fuente de verdad cuando haya duda.

## Herramienta: `scripts/dueno_de_ruta.py`

Lee `assets/ownership.json` (fuente única de verdad del mapa) y responde de forma determinista. Úsala antes de afirmar un dueño si la ruta no está literalmente en el mapa rápido.

```bash
python scripts/dueno_de_ruta.py apps/pos/views.py static/pos/db.js   # dueño, pareja, revisor, WBS, funciones ajenas
python scripts/dueno_de_ruta.py --persona yahir                       # todo lo que le toca a Yahir
python scripts/dueno_de_ruta.py --wbs 3.4.6                           # rutas y personas del paquete
python scripts/dueno_de_ruta.py --codeowners --salida .github/CODEOWNERS  # genera CODEOWNERS en UTF-8
python scripts/dueno_de_ruta.py --verificar                           # autoprueba del mapa
git diff --name-only --diff-filter=d origin/main...HEAD | python scripts/dueno_de_ruta.py --revisar
                                                                      # revisión de rutas de un PR (integrador)
```

Si el script responde "fuera de la estructura aprobada", no inventes una ubicación como si fuera oficial: aplica el procedimiento siguiente, presenta el resultado como **propuesta** y señala que el integrador (Tarín) debe ratificarla.

## Procedimiento para ubicar cualquier entregable

Sigue estos pasos en orden; cada uno se apoya en el anterior.

1. **Identifica el paquete WBS.** Búscalo en `references/matriz-wbs-responsables.md` (WBS Rev. 4, que ya incluye administración de cuentas 3.1.5, ajuste 3.3.8, bandeja de revisión 3.4.9 y cierre de turno 3.5.7; el código 3.3.2 está retirado y su contenido vive en 3.3.1). **Paquetes en evaluación:** 3.3.7, la vista de cocina (DEC-15), tiene rutas y responsables reservados, pero está fuera de la línea base. Si preguntan por ella, da la ubicación, aclara que no se programa hasta que el equipo la apruebe Si no existe paquete, lo más probable es una ampliación de alcance: dilo y no propongas código hasta que el PO lo dé de alta (`CLAUDE.md` §3 y §11).
2. **Determina el módulo y la app.** M-USR → `accounts`; datos maestros (platillo, insumo, receta, precio) → `catalog`; existencias, compras, mermas, alertas → `inventory`; pedido, venta, modificadores, turno de caja, sincronización → `pos`; corte, reportes, exportación → `reports`; algo que todas las páginas comparten y no tiene RF → `core`. El turno de caja vive en `pos` aunque el WBS lo agrupe en M-REP, porque debe operar sin conexión.
3. **Determina la capa**, y con ella el archivo:

   | Si el entregable…                                             | Va en                                                    | Capa                         |
   | ------------------------------------------------------------- | -------------------------------------------------------- | ---------------------------- |
   | define una tabla o un campo                                   | `apps/<app>/models.py` + migración                       | datos (JH)                   |
   | implementa una regla de negocio o toca varias tablas a la vez | `apps/<app>/services.py` (o `services_<tema>.py` en pos) | backend                      |
   | recibe una petición HTTP                                      | `apps/<app>/views.py` + `urls.py`                        | backend                      |
   | es una página completa                                        | `apps/<app>/templates/<app>/<nombre>.html`               | frontend                     |
   | es la respuesta a una petición HTMX                           | `apps/<app>/templates/<app>/partials/<nombre>.html`      | frontend                     |
   | es interfaz sin servidor (acordeón, stepper)                  | `x-data` dentro de la plantilla, no un `.js` nuevo       | frontend                     |
   | funciona sin conexión                                         | `static/pos/`                                            | frontend en pareja           |
   | es una prueba unitaria                                        | `apps/<app>/tests.py`                                    | quien implementó el servicio |
   | es un flujo E2E crítico                                       | `tests_e2e/`                                             | frontend (YE)                |
   | es documentación                                              | `docs/` en Markdown (Word → espacio compartido)          | según `docs/`                |

4. **Asigna el nombre** con el glosario de `CLAUDE.md` §9 (identificadores en inglés: `dish`, `ingredient`, `order`, `modifier`, `cash_session`, `cash_close`, `waste`…; textos de interfaz en español). Vistas y URLs se nombran por la acción (`add_item`, `mark_prepared`), nunca por ser parciales. **Nombres de archivo (DEC-17):** todo archivo o carpeta de código y pruebas lleva nombre en inglés. La app del punto de venta es `pos`, no `pdv`: `apps/pos/`, `static/pos/`, `templates/pos/`, URLs `/pos/…`, nombres `pos:…`. La documentación en `docs/` conserva sus nombres en español. **Única excepción de identificadores (DEC-01):** el módulo de precios y el lote de sincronización van en español: `calcular_total()`, `calcularTotal()`, `precio_base_centavos`, `ajuste_centavos`, `total_cobrado_centavos`… Modelos, vistas y servicios siguen en inglés aunque reciban un `pedido` con llaves en español.
5. **Obtén el dueño** con el script o el mapa. Si el entregable toca dos capas, sepáralo en dos entregables con dos dueños y un contrato vista–plantilla entre ellos.
6. **Verifica las reglas duras** antes de responder: dependencia entre apps, dinero en `DecimalField` (servidor) o centavos enteros (cliente offline), nada de cálculo de dinero en Alpine en línea, autorización en la vista, pareja en `static/pos/`.

## Formato de respuesta

Cuando te pregunten dónde va algo o quién lo hace, responde con esta estructura (en prosa breve si es una sola ruta; en tabla si son varias):

```
Entregable:      <qué es, en una línea>
Paquete WBS:     <código y nombre>  (o "sin paquete: posible ampliación de alcance")
Ruta(s):         <ruta exacta por cada archivo>
Dueño:           <persona>   Pareja/colabora: <persona o —>   Revisor: <persona o —>
Contrato:        <si hay vista + plantilla: quién escribe el docstring y quién la plantilla>
Rama:            <nombre>/<tema>          Título del PR: WBS-<código>: <descripción>   (DEC-23)
Reglas que aplican: <las 1–3 reglas duras relevantes>
Cambio vs WBS Rev. 3: <"ninguno", qué cambió, o "paquete nuevo de la Rev. 4">
```

Omite los renglones que no apliquen; no rellenes con "N/A".

## Ejemplos

**Ejemplo 1 — un archivo del módulo offline**
Pregunta: "Voy a empezar la cola de ventas pendientes en IndexedDB, ¿dónde la pongo?"
Respuesta esperada: paquete 3.4.3; ruta `static/pos/db.js`; dueño Tarín con Yahir en pareja obligatoria; revisor Jared, porque la forma de la cola es el contrato con `sync_operations()`. La cola es única, con campo `tipo` (`venta` / `apertura_turno`) y llaves en español, según `contrato-sync-pdv.md` v1; `fetch` debe mandar `X-CSRFToken`. Cambio vs Rev. 3: la pareja era Tarín + Jared.

**Ejemplo 2 — un paquete que cruza capas**
Pregunta: "¿Quién hace el reporte de productos más vendidos?"
Respuesta esperada: paquete 3.5.4 partido en dos. Backend: `top_dishes()` en `apps/reports/services.py` + vista en `views.py`, dueño Jared, revisor Jesús. Frontend: plantilla en `apps/reports/templates/reports/`, dueña Yahir. Jared abre primero el PR con el contrato vista–plantilla. `reports` solo lee `pos.Sale` e `inventory.StockMovement`. Cambio vs Rev. 3: antes todo era de Yahir.

**Ejemplo 3 — algo que no tiene paquete**
Pregunta: "El dueño quiere un descuento por combo, ¿dónde lo programo?"
Respuesta esperada: no hay paquete en la WBS Rev. 4 ni aparece en "lo que el sistema hace" (`CLAUDE.md` §3), así que es una ampliación de alcance: no se programa hasta que Diego lo registre por control de cambios. Si se aprueba, la regla toca los dos lados de la paridad: primero se agrega el caso a `tests_fixtures/pricing_cases.json` y luego se cambian `calcular_total()` (Jesús) y `calcularTotal()` (Tarín + Yahir) en el mismo PR.

**Ejemplo 4 — un paquete en evaluación**
Pregunta: "¿Quién hace la pantalla donde se ven los pedidos pendientes de cocina?"
Respuesta esperada: es 3.3.7, la vista de cocina, que está en evaluación y fuera de la línea base (DEC-15). Si se aprueba, el reparto es:

- estado "preparado" en `apps/pos/models.py`, a cargo de Jesús;
- vistas `kitchen_queue` y `mark_prepared` en `apps/pos/views.py`, a cargo de Jared;
- plantillas `pos/kitchen_queue.html` y `partials/kitchen_order.html`, a cargo de Tarín, con Yahir en pareja para la lectura sin red.

Hasta que el equipo lo decida, esos archivos no se crean. El sistema tiene solo dos roles, Administrador y Cajero (DEC-21); si la vista se aprueba, la usan ellos.

## Antes de abrir el PR (checklist)

La plantilla completa está en `assets/repo/.github/pull_request_template.md` y se copia a `.github/` del repositorio. Tiene dos partes.

**Autor**, antes de pedir revisión:

- Cada archivo está en la ruta del mapa; lo comprueba con `--revisar`.
- Nadie más que Jesús tocó `models.py` o `migrations/`, y ninguna migración aplicada fue editada.
- Toda vista nueva trae su contrato vista–plantilla; si tocó `db.js` o `sync_operations()`, respeta `contrato-sync-pdv.md` v1.
- Si tocó precios, cambió `calcular_total()`, `calcularTotal()` y el fixture en el mismo PR, y `node --test` pasa.
- No hay credenciales ni datos reales: el repositorio es público.

**Integrador (Tarín)**, antes de aprobar y fusionar:

- `--revisar` o el job de CI sin bloqueos, y los avisos atendidos (coautoría en `static/pos/`, visto bueno del autor si se tocó una función ajena).
- Revisa el contenido y aprueba. Si el PR es suyo, lo aprueba otra de las personas listadas.
- CI en verde. Entonces fusiona.

## Configuración del repositorio (una sola vez)

Acciones P1 a P3 de `references/decisiones-y-pendientes.md`, a cargo de Tarín como integrador:

1. **Copiar el kit.** Copiar `assets/repo/` sobre la raíz del repositorio (`.github/CODEOWNERS`, `.github/pull_request_template.md`, `docs/decisiones/`) y la carpeta completa de la skill en `.claude/skills/sgft-organizacion-entregables/`.
2. **Permisos.** Los usuarios de GitHub ya están en `assets/ownership.json`: T4R1N256, Diego-Galindo98, EduardGarrido, JBeltra16 y CodigaBorealis. Los cinco necesitan permiso de escritura. **Tarín debe ser el único administrador**; la vía más simple es que el repositorio esté en su cuenta.
3. **Proteger `main` con dos rulesets** (Settings → Rules → Rulesets, DEC-16):
   - **"main — solo el integrador fusiona":** reglas _Restrict updates_, _Restrict deletions_ y _Block force pushes_; en la lista de excepciones, _Repository admin_ en modo _For pull requests only_.
   - **"main — requisitos del PR":** _Require a pull request_ con 1 aprobación, _Require review from Code Owners_, descartar aprobaciones viejas, y _Require status checks_ (CI de 5.1 y la revisión de rutas); **sin excepciones**, para que el integrador también las cumpla. Como Tarín figura en todas las rutas (DEC-18), su aprobación cumple el requisito de code owners.
4. **Revisión de rutas en CI** (Jared lo agrega al workflow de 5.1):

   ```yaml
   - uses: actions/checkout@v4
     with: { fetch-depth: 0 }
   - name: Revisar rutas del PR
     run: git diff --name-only --diff-filter=d origin/${{ github.base_ref }}...HEAD | python .claude/skills/sgft-organizacion-entregables/scripts/dueno_de_ruta.py --revisar
   ```

## Mantenimiento de la skill

La fuente de verdad es `assets/ownership.json`. Para cambiar un responsable: edita el JSON, corre `--verificar` (exige al menos dos personas por ruta), regenera `assets/repo/.github/CODEOWNERS` con `--codeowners` y actualiza la fila correspondiente en `references/matriz-wbs-responsables.md`. Toda decisión nueva se agrega como `DEC-24` en adelante en `references/decisiones-y-pendientes.md`. El mapa lo mantiene el integrador (Tarín); Diego revisa los cambios que alteran responsables del WBS.

## Referencias — cuándo leer cada una

| Archivo                                                       | Léelo cuando…                                                                                      |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `references/arbol-repositorio-con-duenos.md`                  | necesites ver el árbol completo o cómo se reparte una app por capas                                |
| `references/matriz-wbs-responsables.md`                       | pregunten por un paquete WBS, por cambios frente a la Rev. 3 o por la carga de cada persona        |
| `references/fichas-por-integrante.md`                         | pregunten "¿qué me toca?" o qué revisa / no toca una persona                                       |
| `references/contrato-vista-plantilla.md`                      | un paquete cruce backend y frontend, o haya dudas de HTMX vs Alpine                                |
| `references/decisiones-y-pendientes.md`                       | pregunten qué se decidió (DEC-01 a DEC-23), qué acciones faltan o algo contradiga a otro documento |
| `assets/repo/docs/decisiones/contrato-sync-pdv.md`            | pregunten por el lote de sincronización, estados por UUID, cuarentena o diferencias de precio      |
| `assets/repo/docs/decisiones/nombres-modulo-precios.md`       | haya duda sobre nombres en español o inglés                                                        |
| `assets/repo/docs/decisiones/organizacion-repositorio.md`     | pregunten por paquetes nuevos, política de pruebas, ramas, CODEOWNERS o la WBS Rev. 4              |
| `assets/repo/.github/CODEOWNERS` y `pull_request_template.md` | quieran configurar revisores automáticos o la plantilla de PR (reemplazar `@TODO_*`)               |

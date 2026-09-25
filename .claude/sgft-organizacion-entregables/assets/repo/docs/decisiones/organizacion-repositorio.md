# Organización del repositorio y del trabajo por capas (DEC-07 a DEC-18)

**Fecha:** 24 de septiembre de 2026 · **Estado:** aprobada · **Dueño:** Alejandro Tarín (integrador), con Diego Galindo como segundo aprobador · **WBS:** 4.2

## Contexto

El equipo se reorganizó por capas: Alejandro Tarín y Yahir Enríquez en frontend; Jesús Hernández en backend y base de datos; Diego Galindo y Jared Beltrán en backend. Los responsables sugeridos del WBS Rev. 3 no seguían esa división, y la estructura del proyecto no fijaba dueño ni ubicación para varios entregables. El mapa completo de propiedad vive en la skill `sgft-organizacion-entregables` (`assets/ownership.json`); este documento registra las decisiones que lo sustentan.

## Decisiones

### DEC-07 — Cuatro paquetes nuevos en el WBS

Se dan de alta cuatro funciones que estaban dentro del alcance (`CLAUDE.md` §3 y §5) pero sin paquete. Los códigos existentes **no se renumeran**, para no invalidar ramas ni commits que ya los citen.

| Código | Paquete | Fuente |
|---|---|---|
| 3.3.7 | Consulta de pedidos en cocina — pasó a evaluación (DEC-15) | RF-17; `CLAUDE.md` §4 |
| 3.3.8 | Ajuste y cancelación de venta | Regla 11 |
| 3.4.9 | Bandeja de revisión del Administrador (cuarentena, existencias negativas, diferencias de precio) | Reglas 9 y 10; DEC-02 |
| 3.5.7 | Cerrar turno de caja | Reglas 5 y 13; `estructura-y-flujo-datos` §5-bis |

3.4.7 se renombra a "Apertura de turno de caja offline", porque el cierre es solo en línea y ahora tiene su propio paquete.

### DEC-08 — Pruebas con varios autores

Cada app conserva un solo `tests.py`, con un dueño y autores de clases de prueba (quien implementa un servicio escribe su prueba). El `tests.py` de una app se convierte en paquete `tests/` (`test_services.py`, `test_views.py`, `test_parity.py`) solo si en un mismo Sprint aparecen dos o más conflictos de fusión en ese archivo. La conversión se registra en `docs/decisiones/`.

### DEC-09 — Ubicaciones y convención de ramas

Se aprueban las ubicaciones que la estructura base no definía:

- `apps/<app>/fixtures/` para datos demo;
- `docs/calidad/` para checklist de seguridad y cobertura;
- `docs/diagramas/procesos/` para el Apéndice A;
- `docs/manual-usuario.md`;
- `docs/decisiones/contrato-sync-pdv.md`, `nombres-modulo-precios.md` y `spike-offline-sprint1.md`;
- `static/core/` para CSS propio;
- archivo del proveedor de despliegue en la raíz;
- `apps/pos/templates/pos/review/` y `cash_session_close.html`.

Mientras no exista el catálogo de requisitos (WBS 1.3.1):

- rama `feat/WBS-3.3.1-seleccion-platillos` o `fix/WBS-3.3.4-redondeo-extras`;
- commit `feat(WBS-3.3.1): lista platillos activos`.

Cuando existan los RF-nn, las ramas nuevas usan `feat/RF-nn-…` (`CLAUDE.md` §8).

### DEC-10 — CODEOWNERS y protección de `main`

El repositorio es público en GitHub Free, donde los code owners y la protección de ramas están disponibles sin costo.

- `.github/CODEOWNERS` se **genera** con `python scripts/dueno_de_ruta.py --codeowners` (skill) y no se edita a mano.
- Cada ruta lista al menos dos personas, porque el autor de un PR no puede aprobarlo.
- En las rutas de un solo dueño (por ejemplo `models.py`), la segunda persona existe solo para aprobar los PR del dueño.

**Configuración de `main`:** la reemplazan los dos rulesets de DEC-16. Los usuarios de GitHub ya están definidos en `assets/ownership.json` de la skill.

**Limitación conocida:** basta una aprobación de cualquiera de los listados. El revisor específico se verifica con el checklist de `.github/pull_request_template.md`.

**Por ser un repositorio público:** `.env` nunca se sube y los datos demo son ficticios (`CLAUDE.md` §10 y §11). Todo lo que entra al repositorio es visible para cualquiera.

### DEC-11 — WBS Revisión 4

Se publica la Revisión 4 del WBS con la columna de responsables por capas y los paquetes de DEC-07. El diccionario en Word (`WBS-SGFT-Diccionario-Niveles.docx`) debe actualizarse con los mismos datos.

### DEC-12 — Fusión de 3.3.1 y 3.3.2 (ajuste del mismo día)

"Selección de platillos" y "Armar pedido" se fusionan en **3.3.1 Selección de platillos y armado del pedido**, por cuatro razones:

- seleccionar un platillo es agregarlo al pedido, así que la selección sola no produce un entregable que el usuario pueda verificar;
- ambos viven en la misma pantalla (`order_builder.html` incluye `partials/dish_list.html`);
- tienen los mismos responsables (Jared en backend, Tarín en frontend) y se prueban en el mismo flujo;
- corresponden a una sola caja del SADT (A31).

Por separado, la selección sería un paquete demasiado pequeño para estimarse con sentido. El código 3.3.2 queda **retirado y no se reutiliza**: renumerar seis paquetes para cerrar el hueco solo mejoraría la apariencia y arriesgaría inconsistencias en los documentos que ya los citan.

### DEC-13 — Alcance de 3.5.5: ventas del día a PDF

Por definición del equipo, 3.5.5 exporta las ventas de una jornada a un documento PDF. Ya no cubre el reporte por periodo ni el de productos más vendidos.

**Contenido:**
- encabezado: fecha, turno, quién lo generó y cuándo;
- detalle de cada venta: hora del dispositivo, platillos y cantidades, método de pago, importe;
- ajustes y cancelaciones con su motivo;
- totales por método de pago y total general.

**Reglas que hereda:**
- atribución al día por la marca de tiempo del dispositivo (regla 7);
- se niega a generarse mientras haya operaciones pendientes de sincronizar y muestra cuántas faltan, igual que el corte (regla 5);
- solo el Administrador, como el resto de M-REP;
- solo en línea.

**Implementación:**
- backend: `export_daily_sales_pdf()` en `apps/reports/services.py`, a cargo de Jared;
- frontend: botón en la vista de reportes, a cargo de Yahir;
- dependencias del paquete: 3.3.5, 3.3.8 y 3.5.1.

Generar PDF requiere una biblioteca nueva, que se justifica en el PR (`CLAUDE.md` §11) y aprueba Jesús. Se recomienda **ReportLab**: licencia BSD y sin dependencias del sistema operativo, a diferencia de WeasyPrint, que necesita bibliotecas del sistema y complicaría el despliegue en Render o Railway.

### DEC-14 — A1 no se descompone; el WBS gana 3.1.5

Se revisó de nuevo la caja A1 (M-USR) del SADT y la conclusión del 11-sep-2026 se sostiene. El módulo tiene dos actividades, administrar cuentas y autenticar y restringir por rol, y la notación IDEF0 exige de tres a seis cajas. Una tercera caja sin salida propia sería artificial.

La descomposición que sí faltaba era la del WBS: la administración de cuentas no tenía paquete. Se agrega **3.1.5 Administración de cuentas de personal**, con Diego en backend y Yahir en frontend. Cubre alta, cambio de rol y desactivación, sin borrado, para conservar la autoría de ventas y movimientos ya registrados.

A1 se abriría solo si se agrega una tercera actividad con salida propia, como la recuperación de contraseña o una bitácora de accesos.

### DEC-15 — Vista de cocina en evaluación

La consulta de pedidos pendientes en cocina (3.3.7) es una sección más de la aplicación, al mismo nivel que Punto de venta o Inventario, donde el Cocinero ve los pedidos con sus personalizaciones y los marca como preparados. El equipo aún no decide si la implementará, así que queda **en evaluación, fuera de la línea base**:

- prioridad candidata "Debería" (SRS 1.1.3);
- rutas y responsables reservados (Jesús en el modelo, Jared en las vistas, Tarín en las pantallas con Yahir en pareja para la parte offline);
- sus archivos no se crean hasta que se apruebe.

Si se implementa, sigue lo decidido en ADR-02: se usa en el mismo dispositivo del cajero y también funciona sin conexión, leyendo la cola local.

**Qué implica no implementarla.** RF-17 y el rol de Cocinero están hoy en el alcance aprobado (`CLAUDE.md` §3 y §4). Sin esta vista, el Cocinero no tendría ninguna función en el sistema, así que la decisión no es solo del equipo:

- al redactar el catálogo de requisitos (1.3.1), RF-17 se clasifica como "Debería";
- si se descarta, se tramita como cambio de alcance autorizado por el cliente (SRS 1.1.2), y ese cambio decide si el rol de Cocinero se elimina. Eso afecta a 3.1.1, 3.1.3, 1.2.3 y 1.7.

**Recomendación:** decidirlo al redactar 1.3.1, antes de implementar el modelo de usuario (3.1.1), para que los roles se definan correctamente desde el inicio.

### DEC-16 — Tarín es el integrador (la aprobación de contenido cambió en DEC-18)

Alejandro Tarín valida que las rutas de cada PR estén en la estructura aprobada y es **el único que fusiona** en `main`. El trabajo se divide en dos revisiones:

- **Contenido:** lo aprueban los code owners de cada ruta, como hasta ahora.
- **Estructura y fusión:** lo resuelve el integrador. Para eso usa `python .claude/skills/sgft-organizacion-entregables/scripts/dueno_de_ruta.py --revisar` o el job equivalente de CI. El comando marca como bloqueo toda ruta fuera de la estructura o de un paquete en evaluación, y como aviso las rutas con pareja obligatoria o con funciones de otro autor.

Tarín **no** se agrega como code owner de todos los archivos. Como GitHub se conforma con la aprobación de cualquiera de los listados, su aprobación bastaría para cualquier archivo y se perdería la revisión del dueño.

**Cambios de dueño.** Pasan de Diego a Tarín:
- la estructura del repositorio: `.github/CODEOWNERS`, `.github/pull_request_template.md`, la skill versionada en `.claude/skills/`, este documento y toda ruta sin regla;
- las acciones de configuración P1 a P3.

Diego queda como segundo aprobador de esos cambios, porque alteran los responsables del WBS.

**Usuarios de GitHub:**

| Integrante | Usuario |
|---|---|
| Alejandro Tarín | `T4R1N256` |
| Diego Galindo | `Diego-Galindo98` |
| Jesús Hernández | `EduardGarrido` |
| Jared Beltrán | `JBeltra16` |
| Yahir Enríquez | `CodigaBorealis` |

**Protección de `main` con dos rulesets** (Settings → Rules → Rulesets):

1. **"main — solo el integrador fusiona":**
   - reglas *Restrict updates*, *Restrict deletions* y *Block force pushes*;
   - lista de excepciones: *Repository admin*, en modo *For pull requests only*.

   Con *Restrict updates* solo quien está en la lista de excepciones puede actualizar la rama, así que nadie más puede fusionar. El modo *For pull requests only* obliga al integrador a pasar siempre por un PR.
2. **"main — requisitos del PR":**
   - *Require a pull request before merging* con 1 aprobación, *Require review from Code Owners* y descarte de aprobaciones cuando lleguen commits nuevos;
   - *Require status checks to pass*: el CI de 5.1 y la revisión de rutas;
   - **sin lista de excepciones.**

Se separan en dos porque la excepción de un ruleset lo cubre completo. Si fuera uno solo, el integrador podría fusionar sin la aprobación del dueño ni el CI en verde.

**Condición:** Tarín debe ser el **único administrador** del repositorio; el esquema se apoya en el rol *Repository admin*. Lo más simple es que el repositorio esté en su cuenta. Los demás integrantes necesitan permiso de escritura.

**Revisión de rutas en CI** (la agrega Jared al workflow de 5.1):

```yaml
- uses: actions/checkout@v4
  with: { fetch-depth: 0 }
- name: Revisar rutas del PR
  run: git diff --name-only --diff-filter=d origin/${{ github.base_ref }}...HEAD | python .claude/skills/sgft-organizacion-entregables/scripts/dueno_de_ruta.py --revisar
```

### DEC-17 — Nombres de archivo en inglés en código y pruebas; `pdv` pasa a `pos`

**Alcance.** Los nombres de archivos y carpetas de **código y pruebas** van en inglés. La documentación (`docs/`) y la skill conservan sus nombres, y su contenido sigue en español.

La app `pdv` se renombra a **`pos`** (*point of sale*):
- carpetas: `apps/pos/`, `static/pos/`, `apps/pos/templates/pos/`;
- URLs: prefijo `/pos/` y endpoint de sincronización `POST /pos/sync/` (contrato v1 actualizado);
- nombres de URL: `pos:add_item`, `pos:confirm_sale`…;
- la carpeta `templates/pos/revision/` pasa a `review/`;
- las pruebas E2E se llaman `test_pos_sale.py`, `test_cash_session_open.py` y `test_cash_close.py`.

**Por qué ahora.** La app todavía no tiene modelos ni migraciones. Después de la primera migración, el nombre de la app queda como prefijo de las tablas (`pos_sale`, `pos_order`…) y dentro de las migraciones, y renombrarla sería costoso.

**Qué no cambia:**
- el código del módulo en el SRS y la WBS (M-PDV) y los textos de la interfaz ("Punto de venta");
- los identificadores en español del módulo de precios (DEC-01), porque son contenido de los archivos, no nombres.

### DEC-18 — Tarín aprueba todos los PR

Tarín es quien aprueba los PR, no solo quien los fusiona. Para que GitHub cuente su aprobación, figura en **todas las rutas** de `CODEOWNERS`. En el mapa de la skill se declara una sola vez, con el campo `aprobador_general`, y el generador lo agrega a cada línea.

**Efectos:**
- La aprobación de Tarín cumple por sí sola el requisito de code owners del ruleset "main — requisitos del PR", sobre cualquier archivo.
- Los dueños de cada ruta siguen recibiendo la solicitud de revisión automáticamente, pero su aprobación ya no se exige.
- Los PR que abre Tarín los aprueba otra de las personas listadas en la ruta, porque GitHub no permite aprobar el PR propio. El mapa garantiza que cada ruta tenga al menos otra persona.
- Sigue vigente de DEC-16: solo Tarín fusiona, y `main` se protege con dos rulesets.

**Alternativas consideradas:**
- *Mantener DEC-16*, en la que el dueño aprueba el contenido y Tarín valida y fusiona.
- *Esquema mixto*, en el que la aprobación de Jesús o Jared seguiría siendo obligatoria en modelos, migraciones y sincronización.

El equipo eligió que la aprobación sea siempre de Tarín.

**Riesgo aceptado:** un cambio al esquema de datos o a la lógica transaccional podría fusionarse sin que lo apruebe quien lo mantiene, y una migración aplicada no se deshace. Mitigación recomendada, no obligatoria: en PR que toquen `models.py`, `migrations/`, `services*.py` de `pos` o `sync_operations()`, esperar el comentario de Jesús antes de aprobar.

## Alternativas consideradas

- **Mantener los responsables de la Rev. 3:** asignaba servicios de backend a integrantes que ahora son de frontend (por ejemplo, `reports/services.py` a Yahir) y concentraba casi todo el backend en Jesús.
- **CODEOWNERS solo como sugerencia, sin bloqueo:** deja el cumplimiento a la memoria del equipo. Se descartó porque el costo es cero en un repositorio público y protege el esquema de datos y el módulo offline.
- **Convertir todos los `tests.py` en paquetes desde el inicio:** evita conflictos, pero se aparta de la estructura aprobada antes de que exista el problema.

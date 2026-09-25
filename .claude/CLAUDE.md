# CLAUDE.md — Sistema de Gestión de Food Truck (SGFT)

> Contexto y reglas de trabajo para agentes y personas. Actualizado el 24-sep-2026 (DEC-01 a DEC-23).
> Dónde va cada archivo y de quién es: skill `.claude/skills/sgft-organizacion-entregables/`, que se consulta con `scripts/dueno_de_ruta.py <ruta>`. Las decisiones `DEC-nn` están registradas en `references/decisiones-y-pendientes.md` de la misma skill.
>
> **No modifiques este archivo sin comentarlo antes con el usuario** y sin su aprobación explícita.

## 1. Proyecto

Aplicación web responsiva (PWA) para el food truck **"El Pardo"** (Ciudad Juárez). Reemplaza el cuaderno con punto de venta, inventario, accesos y reportes.

- **Cliente:** Alejandro Cárdenas de la Mora. Negocio de 3 colaboradores; menú de burritos, desayunos, guisados por porción y bebidas.
- **Contexto:** proyecto académico de la UACJ, sin costo para el cliente ni soporte después del semestre. Scrum con Sprints de 2 semanas.

| Integrante      | GitHub            | Rol                                                                                                                      |
| --------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Diego Galindo   | `Diego-Galindo98` | Product Owner · back-end (usuarios, inventario)                                                                          |
| Jesús Hernández | `EduardGarrido`   | Back-end y BD (modelos, migraciones, servicios transaccionales, despliegue)                                              |
| Jared Beltrán   | `JBeltra16`       | Back-end (vistas del punto de venta, reportes, CI)                                                                       |
| Alejandro Tarín | `T4R1N256`        | Scrum Master · front-end (base visual, punto de venta, cliente offline) · **integrador: aprueba y fusiona todos los PR** |
| Yahir Enríquez  | `CodigaBorealis`  | Front-end (usuarios, inventario, reportes) · pruebas E2E                                                                 |

## 2. Por qué existe

Hoy todo es manual: pedidos en cuaderno, totales mentales, conteo visual del inventario y corte de caja a mano. Eso produce errores de cobro, desabasto, mermas y **cero visibilidad del margen**. Entre dos implementaciones, elige la que reduzca pasos para el operador: se atiende con fila.

## 3. Alcance

| Módulo                | Hace                                                                                                                                                                                                                                                                                                                    |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **M-PDV** (app `pos`) | Catálogo con precios, pedidos, personalización (quitar o agregar ingredientes), total automático, cobro con método de pago, ajuste o cancelación con motivo, bandeja de revisión del Administrador. **Funciona con y sin internet.** La consulta de órdenes por cocina está **en evaluación** (DEC-15): no implementar. |
| **M-INV**             | Insumos con unidad de medida, recetas, descuento automático al vender, mínimos y alertas, compras y mermas, catálogo de platillos y precios. Solo en línea.                                                                                                                                                             |
| **M-USR**             | Cuentas del personal (alta, cambio de rol, desactivación; nunca borrado), autenticación, roles Administrador y Cajero. Solo en línea.                                                                                                                                                                                   |
| **M-REP**             | Apertura y cierre de turno de caja, corte automatizado, ventas por periodo, más vendidos, **PDF de las ventas del día**. La apertura funciona sin conexión; lo demás requiere red.                                                                                                                                      |

**Fuera de alcance:** pagos con tarjeta o pasarelas (solo se _registra_ el método), pedidos a domicilio, CFDI/SAT, nómina y contabilidad, app de tienda (es PWA), varias sucursales, lealtad/CRM, digitalizar el cuaderno histórico.

> Si algo no aparece en esta sección, está fuera. No lo implementes: pregunta.

## 4. Actores

Hay **dos roles**: Administrador y Cajero.

| Rol                             | Puede                                                                                                     | No puede                                                                |
| ------------------------------- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Administrador** (propietario) | Todo, incluidas la resolución de cuarentenas y la revisión de diferencias de precio e insumos en negativo | —                                                                       |
| **Cajero**                      | Tomar pedidos, cobrar (con o sin red), ver sus ventas del día, abrir y cerrar su turno                    | Tocar inventario, precios, recetas o usuarios; ver reportes financieros |

El comensal no es actor: no tiene cuenta y no se guardan sus datos.

## 5. Reglas de negocio (no negociables)

1. **El inventario se descuenta cuando la venta llega al servidor.** En línea, al confirmar; sin conexión, al sincronizar. Ocurre en la misma transacción atómica que registra la venta, recorriendo la receta (insumo × cantidad × unidades).
2. **Las personalizaciones ajustan el descuento.** Quitar un ingrediente no lo descuenta; un extra descuenta la cantidad adicional y puede cambiar el precio de la línea.
3. **Alerta de stock** cuando `existencia <= min_stock` (el mínimo se configura por insumo). Es visual; no bloquea la venta.
4. **Pago: solo efectivo o transferencia.** Se registra como atributo de la venta; nunca se ejecuta ni se concilia.
5. **El corte de caja** consolida las ventas del turno por método de pago, a partir de lo registrado. **No se genera si hay ventas sin sincronizar**: se niega y muestra cuántas faltan. La diferencia de efectivo se anexa como dato informativo y no bloquea.
6. **Precios, recetas y mínimos** solo los define el Administrador.
7. **Una venta es inmutable desde que se confirma el cobro**, también en la cola offline. Se corrige con un ajuste o una cancelación que deja rastro y referencia a la original. Guarda dos marcas de tiempo: la del dispositivo y la del servidor.
8. **Toda operación offline lleva un UUID** generado en el dispositivo (ventas y aperturas de turno). El servidor descarta los UUID repetidos; la garantía es una restricción de unicidad en la base de datos, no una comprobación en el código.
9. **Lo que el servidor no puede aplicar va a cuarentena; nunca se rechaza.** El Administrador la resuelve en línea con una de tres salidas: aplicar con el catálogo actual, aplicar sin descontar inventario, o descartar si era un duplicado real.
10. **Una existencia puede quedar negativa tras sincronizar.** Se registra, se marca para revisión y la venta no se revierte.
11. **El motivo del ajuste decide qué se revierte:**
    - `error_captura` revierte dinero e inventario;
    - `devolucion` revierte el dinero, y el insumo se registra como merma;
    - `correccion_pago` no revierte nada, solo cambia a qué método se atribuye en el corte.
12. **Toda venta requiere un turno de caja abierto.** Se valida antes de calcular, con o sin red; sin red se usa el estado del turno guardado en el dispositivo.
13. **Un turno por jornada:** una apertura y un cierre, un solo dispositivo; puede abrirlo o cerrarlo el Cajero o el Administrador. Una diferencia de efectivo se registra y no bloquea.
14. **Si al sincronizar el total del catálogo vigente difiere de lo cobrado, manda lo cobrado** (DEC-02). Se registra el total del servidor y la venta se marca para revisión, sin ir a cuarentena. Si lo cobrado ni siquiera corresponde a las líneas de su propio pedido, entonces sí va a cuarentena.

Si una instrucción contradice estas reglas, **detente y avisa**: vienen del cliente, no del equipo.

## 5-bis. Operación offline

- **Qué funciona sin red:** solo M-PDV, incluida la apertura del turno. Un solo dispositivo: no se programa resolución de conflictos entre varios.
- **Sincronización:** `POST /pos/sync/`, contrato v1:
  - Lote único `operaciones` con campo `tipo`, llaves en español e importes en centavos.
  - Respuesta 200 con un estado por UUID.
  - Sin sesión, 401 y la cola se conserva.
  - Cambiar la forma del lote sube `version_contrato` y requiere a Jesús, Jared y Tarín.
- **Paridad de precios:** `calcular_total()` y `calcularTotal()` deben dar lo mismo; lo comprueba la prueba de paridad.
- **Invariantes que no se simplifican:** un solo camino de escritura, UUID por operación, cuarentena en lugar de rechazo y dinero en enteros.

## 6. Stack y comandos

```
Python 3.12 · Django 5.2 LTS (versiones fijas en requirements.txt) · PostgreSQL 16+ (Neon/Supabase en producción)
Django Templates + Bootstrap 5 + HTMX 2 + Alpine.js 3 por CDN — sin npm, sin build
Offline: manifest + service worker (Workbox por importScripts) + Dexie.js
Pruebas: django.test.TestCase · node --test (paridad) · Playwright (venta con y sin red, apertura, corte)
Despliegue: Render o Railway con Gunicorn + WhiteNoise · CI: GitHub Actions
```

**Todo gratuito o de código abierto:** el cliente no paga nada. Node solo corre en CI.

```bash
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt   # Windows/Git Bash: venv/Scripts/activate
cp .env.example .env                     # DJANGO_SECRET_KEY y DATABASE_URL
python manage.py migrate
python manage.py check && python manage.py test
python manage.py runserver
node --test tests_e2e/parity/            # si tocaste precios
python manage.py makemigrations          # SOLO Jesús
git diff --name-only --diff-filter=d origin/main...HEAD | python .claude/skills/sgft-organizacion-entregables/scripts/dueno_de_ruta.py --revisar
```

## 7. Estructura y arquitectura

```
config/            settings, urls, wsgi — sin lógica de negocio
apps/__init__.py   obligatorio (sin él, manage.py test corre 0 pruebas)
apps/core/         base.html, filtros de formato, mixins de rol
apps/accounts/     M-USR       apps/catalog/   platillos, insumos, recetas (Django Admin)
apps/inventory/    M-INV       apps/pos/       M-PDV, turno de caja, sincronización
apps/reports/      M-REP, solo lectura y sin modelos
static/pos/        manifest.json, sw.js, db.js, pricing.js
tests_fixtures/    pricing_cases.json          tests_e2e/   Playwright + parity/
.claude/skills/    mapa de propiedad           .github/     CODEOWNERS (generado), plantilla de PR, CI
```

- **Capas por app:** `urls.py` → `views.py` → `services*.py` → `models.py`, más plantillas en `templates/<app>/` (páginas completas) y `templates/<app>/partials/` (fragmentos HTMX).
  - La **vista** solo hace HTTP: rol, turno, `request.htmx` y llamada al servicio.
  - El **servicio** tiene las reglas y el `transaction.atomic()`.
  - La **plantilla** solo presenta.
- **Dependencias entre apps:** `pos` puede importar de `inventory` y `catalog`; `inventory` **nunca** importa de `pos`; `reports` solo lee; `core`, `accounts` y `catalog` no dependen de otras apps. Si un `import` rompe esto, el código está en la app equivocada.
- **Funciones clave** (si te toca crearlas, usa estos nombres; si existen, no las dupliques):

  | Archivo                        | Funciones                                                                   |
  | ------------------------------ | --------------------------------------------------------------------------- |
  | `pos/services.py`              | `confirm_sale`, `cancel_sale`, `adjust_sale`                                |
  | `pos/services_pricing.py`      | `calcular_total`                                                            |
  | `pos/services_cash_session.py` | `open_session`, `close_session`, `current_session`                          |
  | `pos/views.py`                 | `sync_operations`                                                           |
  | `inventory/services.py`        | `deduct_for_sale`, `register_purchase`, `register_waste`, `check_min_stock` |
  | `reports/services.py`          | `cash_close`, `sales_by_period`, `top_dishes`, `export_daily_sales_pdf`     |
  | `accounts/services.py`         | `create_user`, `change_role`                                                |

## 8. Flujo de trabajo

- **Ramas:** `nombre/tema`, donde `nombre` es tu clave (`diego`, `jesus`, `jared`, `tarin`, `yahir`) y `tema` son 2 a 4 palabras: `diego/login`, `jesus/modelo-venta`. Minúsculas y guiones, sin acentos, `ñ` ni espacios. Una rama por tarea; se borra al fusionar.
- **Título del PR:** lleva el paquete de la WBS, que es lo que liga el cambio con su requisito: `WBS-3.1.2: inicio de sesión con usuario y contraseña`.
- **Commits dentro de la rama:** libres. Los PR se fusionan con _Squash and merge_: a `main` llega un solo commit con el título del PR en la primera línea y los commits, incluido `Co-authored-by`, en el cuerpo.
- **Pull Requests:**
  - nunca push a `main`;
  - `CODEOWNERS` avisa al dueño de cada archivo;
  - **Tarín aprueba y es el único que fusiona**; sus propios PR los aprueba otra persona de la ruta;
  - hay que usar la plantilla de PR y tener el CI en verde.
- **Un archivo, un dueño**, según el mapa de la skill. `CODEOWNERS` se genera con `dueno_de_ruta.py --codeowners --salida .github/CODEOWNERS`; no se edita a mano.
- **`static/pos/` se programa en pareja**, con ambos autores en el commit (`Co-authored-by:`).

## 9. Convenciones de código

- **Idioma:**
  - interfaz, mensajes y errores en español;
  - identificadores, tablas, comentarios y **nombres de archivos y carpetas de código y pruebas** en inglés (DEC-17). La app es `pos`, no `pdv`;
- **Excepción DEC-01:** el módulo de precios y el lote de sincronización van en español: `calcular_total()`, `calcularTotal()`, y llaves como `pedido`, `lineas`, `platillo_id`, `precio_base_centavos`, `ajuste_centavos`, `total_cobrado_centavos`.
- **Glosario:** punto de venta `pos` · venta `sale` · platillo `dish` · insumo `ingredient` · receta `recipe` · pedido `order` · personalización `modifier` · existencia `stock` · nivel mínimo `min_stock` · merma `waste` · corte `cash_close` · turno `cash_session` · roles `admin`/`cashier` · ajuste `sale_adjustment` · cuarentena `quarantined_sale`/`quarantined_cash_session` · efectivo inicial/final/esperado `opening_amount`/`closing_amount`/`expected_amount` · diferencia `cash_difference` · bandeja de revisión `review`.
- **Dinero:**
  - nunca en punto flotante;
  - en el servidor, `DecimalField(max_digits=10, decimal_places=2)`;
  - en el cliente offline, enteros de centavos.

  Las cantidades de insumo siempre llevan unidad de medida.

- **Vistas y plantillas:**
  - una vista por acción sirve página y fragmento según `request.htmx`, y se nombra por la acción (`add_item`, no `partial_x`);
  - cada vista nueva documenta en su docstring el **contrato vista–plantilla**: URL, roles, plantilla, contexto, `hx-target` y controles según el estado. Qué acciones se muestran lo decide el servidor, no la plantilla;
  - el `id` del destino HTMX va en la raíz del fragmento;
  - Alpine solo guarda estado local de la interfaz; nunca calcula dinero, salvo `pricing.js` sin conexión;
  - no hay `.js` propios fuera de `static/pos/`.
- **Autorización:** en el servidor, en cada vista, con el mixin de `apps/core/mixins.py`. Ocultar un botón no es control de acceso. Al sincronizar se revalida el rol de cada operación.
- **Modelos:** solo Jesús edita `models.py` y genera migraciones. Los demás piden el campo por issue. Una migración aplicada nunca se edita.
- **Pruebas:** van en `apps/<app>/tests.py`. Quien implementa un servicio escribe sus pruebas, a partir de los criterios de aceptación del requisito.
- **Dependencias:** una nueva se justifica en el PR y la aprueban Jesús (dueño de `requirements.txt`) y Tarín.

## 10. Seguridad y datos

- **Secretos:** `.env` nunca se sube, y el repositorio es **público**: nada de credenciales ni datos reales. Cada integrante genera su propia `DJANGO_SECRET_KEY` con `python -c "import secrets; print(secrets.token_urlsafe(50))"`. La de producción vive en el panel del proveedor y no se cambia.
- **Contraseñas:** con hash, mediante el sistema de autenticación de Django.
- **CSRF:** siempre activo. `|safe` solo con justificación. `base.html` envía el token en toda petición HTMX (`hx-headers`), y `db.js` lo lee de la cookie `csrftoken`. Por eso `CSRF_COOKIE_HTTPONLY = False` es **intencional**.
- **Datos personales:** solo del personal (nombre, rol, credenciales), conforme a la LFPDPPP (DOF 20-03-2025). Referencia de seguridad: OWASP Top 10:2021.

## 11. Cómo trabajar (incluidos los agentes)

1. **Antes de escribir código:**
   - identifica al desarrollador con `git config user.name`;
   - ubica el paquete de la WBS de la tarea (y su `RF-nn`); si no lo conoces, pregunta;
   - consulta el dueño y la ruta de cada archivo con el script;
   - trabaja en una rama.
2. **No hagas:**
   - ampliar el alcance;
   - crear archivos fuera del mapa o de paquetes en evaluación (hoy: 3.3.7, vista de cocina);
   - correr `makemigrations` si no eres Jesús;
   - hacer push a `main`, usar `--force` o fusionar PR;
   - agregar dependencias sin justificarlas;
   - simplificar el diseño offline;
   - modificar este `CLAUDE.md` sin comentarlo antes con el usuario.
3. **Si tocas un archivo de otra persona,** díselo al desarrollador.
4. **Terminado significa:**
   - `check` y `test` en verde;
   - `makemigrations --check --dry-run` sin cambios, salvo que Jesús genere una migración;
   - `--revisar` sin bloqueos;
   - `.env` fuera de `git status`;
   - aviso al usuario si el comportamiento se aparta de lo que pide el requisito;
   - un resumen de qué cambió y de quién son los archivos tocados.

# SGFT — Sistema de Gestión de Food Truck

Aplicación web progresiva (PWA) para el food truck **«El Pardo»** de Ciudad Juárez: punto de venta que funciona con y sin internet, inventario por recetas, caja y reportes. Proyecto académico de la Universidad Autónoma de Ciudad Juárez (UACJ).

> **Estado (15-nov-2026):** el sistema está desplegado en Railway con PostgreSQL en Neon (`https://sgft-production.up.railway.app`) y el modo sin conexión quedó validado en un iPhone 17 Pro Max con iOS 26 ([resultados del spike](docs/decisiones/spike-offline-resultados.md)). Falta la instalación final en el teléfono del negocio y la primera venta real (WBS 1.4.4).

---

## Tabla de contenido

- [Contexto y problema](#contexto-y-problema)
- [Objetivos](#objetivos)
- [Alcance](#alcance)
- [Pantallas y módulos](#pantallas-y-módulos)
- [Roles y acceso](#roles-y-acceso)
- [Operación sin conexión](#operación-sin-conexión)
- [Stack tecnológico](#stack-tecnológico)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Cómo correrlo en tu computadora](#cómo-correrlo-en-tu-computadora)
- [Pruebas](#pruebas)
- [Despliegue](#despliegue)
- [Flujo de trabajo](#flujo-de-trabajo)
- [Documentación](#documentación)
- [Equipo](#equipo)
- [Referencias](#referencias)
- [Licencia](#licencia)

---

## Contexto y problema

**«El Pardo»** es un food truck fundado en 2026 en Ciudad Juárez, Chihuahua. Vende burritos, desayunos, guisados por porción y bebidas, y lo atienden tres colaboradores sobre la Av. Vicente Guerrero, una zona de mucha demanda por el Hospital General Regional No. 2 del IMSS. La competencia directa opera de manera informal: cobra solo en efectivo o transferencia y no tiene punto de venta ni presencia digital.

Antes del SGFT todo era manual: pedidos en cuaderno, totales calculados de memoria, conteo visual del inventario y corte de caja a mano. Eso producía:

- errores de cobro y en los pedidos;
- desabasto y mermas de materia prima;
- ninguna visibilidad del margen de ganancia ni del desempeño de cada platillo;
- más tiempo de atención con fila.

## Objetivos

**General:** desarrollar e implementar durante el semestre un sistema web para la gestión del food truck, que integre punto de venta, inventario, usuarios y reportes para agilizar la atención y dar control del negocio.

**Específicos:**

- **Punto de venta:** registrar pedidos, personalizaciones y cobros con el menor número de pasos, también sin internet.
- **Inventario:** descontar los insumos de cada venta según su receta y alertar cuando un insumo llega a su mínimo.
- **Usuarios:** restringir las funciones sensibles al Administrador.
- **Reportes:** automatizar el corte de caja y mostrar ventas, ganancias y productos más vendidos.

## Alcance

**Dentro:**
- punto de venta con catálogo, personalización (quitar o agregar ingredientes), total automático y cobro en efectivo o transferencia (solo se registra el método);
- ajuste o cancelación de una venta con motivo;
- inventario de insumos con recetas, compras, mermas, mínimos y alertas;
- turno de caja con corte automatizado, reportes por periodo y PDF de las ventas del día;
- cuentas del personal en Django Admin;
- operación sin conexión con sincronización posterior.

**Fuera:** pagos con tarjeta o pasarelas, pedidos a domicilio, CFDI/SAT, nómina y contabilidad, app de tienda (es PWA), varias sucursales, lealtad/CRM, digitalizar el cuaderno histórico, hardware y soporte después del semestre. La consulta de órdenes por cocina está en evaluación y no se implementó.

## Pantallas y módulos

| Pantalla | Módulo | Qué hace |
|---|---|---|
| **Nueva venta** | M-PDV (`apps/pos`) | Catálogo por categorías con búsqueda, ticket con cantidades y modificadores, total calculado por el servidor, cobro en efectivo o transferencia. Abrir la caja es el primer paso del día. Funciona sin red. |
| **Productos** | `apps/catalog` | Platillos con su precio y su receta, e insumos con su unidad de medida. Con PIN de Administrador. |
| **Inventario** | M-INV (`apps/inventory`) | Existencias y mínimos de cada insumo, compras y mermas con motivo, y la lista de «Insumos bajos». Con PIN de Administrador. |
| **Caja** | M-REP (`apps/reports`) | Total del día por método de pago, ganancias (ventas menos el costo de insumos por receta), mermas y cierre de turno con diferencia de efectivo. Con PIN. |
| **Reportes** | M-REP (`apps/reports`) | Ventas, productos vendidos, insumos usados y mermas por día, semana o mes; exportación del PDF de las ventas del día. Con PIN. |
| **Django Admin** | M-USR (`apps/accounts`) | Alta, cambio de rol y desactivación de cuentas (nunca se borran); bandeja de operaciones en cuarentena y ventas por revisar. Solo con red. |

**Reglas de negocio principales:**
- el inventario se descuenta en la misma transacción que registra la venta;
- una venta confirmada no se modifica: se corrige con un ajuste o una cancelación que deja rastro;
- toda venta requiere un turno de caja abierto, y solo hay un turno por día;
- el corte se niega mientras haya ventas sin sincronizar;
- el dinero nunca se maneja en punto flotante.

La lista completa está en el [SRS](docs/SRS.md).

## Roles y acceso

| Rol | Puede | No puede |
|---|---|---|
| **Administrador** (propietario) | Todo: abrir y cerrar caja, Productos, Inventario, Caja, Reportes, cuentas y resolución de cuarentenas | — |
| **Cajero** | Tomar pedidos, cobrar con o sin red mientras haya un turno abierto y ver las ventas del día | Abrir o cerrar caja; tocar inventario, precios, recetas o usuarios; ver reportes financieros |

**No hay página de inicio de sesión:**
- El teléfono se **activa una sola vez** con el PIN de un Administrador y queda con una sesión permanente de la cuenta de cajero.
- Las pantallas con candado y la apertura y el cierre de caja piden de nuevo el **PIN de Administrador** (6 dígitos, que es la contraseña de su cuenta) y quedan desbloqueadas 30 minutos.
- Cinco PIN incorrectos bloquean el PIN 15 minutos, también en Django Admin.
- Django Admin conserva su propio inicio con usuario y contraseña.

## Operación sin conexión

En el food truck casi siempre se vende sin red y se sincroniza después.

**Qué funciona sin red:**
- **Nueva venta**, con la última copia del catálogo. Cada venta se guarda en el teléfono (IndexedDB) con un UUID propio.
- **Abrir la caja**, con el PIN validado contra un verificador PBKDF2 que el teléfono descarga. Nunca guarda el PIN, y el verificador caduca a los 7 días sin sincronizar.
- **Productos, Inventario, Caja y Reportes**, solo para consulta, con los datos de la última sincronización.

**Cómo se sincroniza:**
- Al volver la red, la cola se envía sola a `POST /pos/sync/` y se reintenta cada 10 s mientras haya pendientes. «Sincronizar» en el menú la envía en cualquier momento.
- El servidor aplica cada operación una sola vez. Lo que no puede aplicar va a **cuarentena**, nunca se rechaza, y el Administrador lo resuelve en Django Admin.
- Si el catálogo cambió, manda lo cobrado y la venta se marca para revisión.

**Recomendaciones para operar:**
- sincronizar antes de cada jornada;
- usar siempre la app instalada en la pantalla de inicio (Safari → Compartir → Agregar a pantalla de inicio): tiene su propia sesión y su propia cola, distintas de las de Safari;
- abrir la caja una vez por día.

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Servidor | Python 3.12 · Django 5.2 LTS · django-htmx · Gunicorn · WhiteNoise · ReportLab (PDF) |
| Base de datos | PostgreSQL 16 (Neon en producción; local o SQLite para pruebas rápidas) |
| Interfaz | Plantillas de Django · HTMX 2 · Alpine.js 3 · Tailwind CSS v4 (CLI autónomo, `app.css` compilado y versionado) |
| Sin conexión | Manifest + service worker con Workbox 7 · Dexie.js 4 sobre IndexedDB |
| Pruebas | `django.test` · `node --test` (paridad de precios Python/JavaScript) · Playwright (E2E) · coverage |
| CI y despliegue | GitHub Actions · Railway |

Todo es gratuito o de código abierto: el cliente no paga nada. No hay npm; Node solo corre en el CI.

## Estructura del repositorio

```
config/            settings, urls, wsgi (sin lógica de negocio)
apps/core/         base.html, componentes de la interfaz, mixins de rol y PIN
apps/accounts/     M-USR: usuario y rol, activación del dispositivo, PIN, Django Admin
apps/catalog/      platillos, insumos y recetas; pantalla Productos; datos ficticios (fixtures/demo.json)
apps/inventory/    M-INV: movimientos, compras, mermas y alertas; pantalla Inventario
apps/pos/          M-PDV: venta, turno de caja, ajustes, sincronización y cuarentena
apps/reports/      M-REP: Caja, Reportes y PDF (solo lectura, sin modelos)
static/core/       css/input.css → app.css (Tailwind), tokens.css, components.css, fuentes
static/pos/        manifest.json, sw.js, db.js, pricing.js, offline.js, pwa.js
tests_fixtures/    pricing_cases.json (casos de la prueba de paridad)
tests_e2e/         pruebas de Playwright y parity/ (Node)
docs/              SRS, calidad, diagramas, decisiones y guías
.github/           CI y CODEOWNERS
```

Cada app sigue las capas `urls.py` → `views.py` (solo HTTP) → `services*.py` (reglas y transacciones) → `models.py`. Las plantillas van en `templates/<app>/` y los fragmentos HTMX en `templates/<app>/partials/`.

## Cómo correrlo en tu computadora

La guía paso a paso está en [`docs/guia-entorno-desarrollo.md`](docs/guia-entorno-desarrollo.md). En resumen:

```bash
python -m venv venv && source venv/bin/activate      # Windows/Git Bash: venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env                                  # pon tu DJANGO_SECRET_KEY y tu DATABASE_URL
python manage.py migrate
python manage.py createcachetable
python manage.py loaddata demo demo_modifiers         # opcional: menú ficticio, solo en una base vacía
python manage.py createsuperuser                      # el Administrador; su contraseña es su PIN de 6 dígitos
python manage.py runserver
```

1. En `http://127.0.0.1:8000/admin/` crea la cuenta de cajero.
2. Abre `http://127.0.0.1:8000/`: te pedirá activar el dispositivo con el PIN del Administrador.

`.env` nunca se sube al repositorio, que es público. Genera tu propia clave con `python -c "import secrets; print(secrets.token_urlsafe(50))"`.

Si cambias clases de Tailwind o tokens, recompila y sube `app.css` en el mismo commit:

```bash
tailwindcss -i static/core/css/input.css -o static/core/css/app.css --minify   # --watch mientras desarrollas
```

## Pruebas

```bash
python manage.py check && python manage.py test        # servicios y vistas de cada app
node --test "tests_e2e/parity/*.mjs"                   # paridad de precios y verificador del PIN
pip install playwright==1.63.0 && python -m playwright install chromium
SGFT_E2E=1 python manage.py test tests_e2e             # E2E: venta con y sin red, apertura y cierre de caja
```

El CI corre todo esto en cada pull request sobre PostgreSQL 16. También revisa que no falte ninguna migración y que cada archivo esté en su lugar según el mapa de propiedad, y falla si la cobertura baja de 90 %; hoy es de 97 % ([`docs/calidad/cobertura.md`](docs/calidad/cobertura.md)).

## Despliegue

Railway despliega cada cambio que llega a `main` (`railway.json`):
- **construcción:** `collectstatic`;
- **antes de arrancar:** migraciones y tabla de caché;
- **servidor:** Gunicorn con 2 workers.

La base es PostgreSQL en Neon, con una rama de producción y otra con los datos ficticios para demostraciones.

Las variables de entorno (`DJANGO_SECRET_KEY`, `DATABASE_URL`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SECURE_HSTS_SECONDS`) viven en el panel de Railway y nunca en el repositorio. Los nombres están en [`.env.example`](.env.example).

## Flujo de trabajo

- **Ramas:** `nombre/tema` (`tarin/rejilla-sin-red`), una por tarea. Nunca se sube nada directo a `main`.
- **Pull requests:**
  - el título lleva el paquete del WBS (`WBS-3.4.4: …`) y la descripción liga un issue con `Closes #n`;
  - se usa la plantilla de PR y se necesita el CI en verde;
  - se fusionan con *Squash and merge*.
- **Revisión:** Alejandro Tarín es el único revisor y quien fusiona.
- **Propiedad:** cada archivo tiene un dueño según el mapa de la skill `sgft-organizacion-entregables`. Se consulta con `python .claude/skills/sgft-organizacion-entregables/scripts/dueno_de_ruta.py <ruta>`.
- **`static/pos/`** se programa en pareja, con ambos autores en el commit (`Co-authored-by:`).
- **Modelos y migraciones:** se avisa a Jesús Hernández, dueño del esquema.
- **Idioma:** la interfaz va en español; el código, los nombres de archivos y los comentarios, en inglés. El módulo de precios y el contrato de sincronización van en español (`calcular_total`, `lineas`, `total_cobrado_centavos`).

El detalle está en [`.claude/CLAUDE.md`](.claude/CLAUDE.md).

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/SRS.md`](docs/SRS.md) | Especificación de requisitos; el apéndice B es la matriz de trazabilidad requisito–prueba |
| [`docs/diagramas/diagrama-er.md`](docs/diagramas/diagrama-er.md) | Diagrama entidad-relación y diccionario de datos |
| [`docs/calidad/checklist-seguridad.md`](docs/calidad/checklist-seguridad.md) | Verificación de seguridad con base en el OWASP Top 10:2021 |
| [`docs/calidad/cobertura.md`](docs/calidad/cobertura.md) | Cobertura de pruebas por módulo |
| [`docs/decisiones/spike-offline-resultados.md`](docs/decisiones/spike-offline-resultados.md) | Validación del modo sin conexión en el iPhone |
| [`docs/convencion-htmx-alpine.md`](docs/convencion-htmx-alpine.md) | Convención de vistas, HTMX y Alpine |
| [`docs/guia-entorno-desarrollo.md`](docs/guia-entorno-desarrollo.md) | Acceso al repositorio y ambiente de desarrollo |

## Equipo

| Integrante | GitHub | Rol |
|---|---|---|
| Diego Adrián Galindo Mora | `Diego-Galindo98` | Product Owner · back-end: usuarios y su Django Admin, servicios de catálogo e inventario |
| Alejandro Tarin Gutiérrez | `T4R1N256` | Scrum Master e integrador · front-end: Nueva venta, Productos, base visual y cliente sin conexión; despliegue |
| Jesús Eduardo Hernández Garrido | `EduardGarrido` | Back-end y base de datos: modelos, migraciones y servicios transaccionales |
| Jared Gustavo Beltrán Herrada | `JBeltran16` | Back-end: servicios de reportes, sincronización y CI |
| Cesar Yahir Enriquez Jasso | `CodigaBorealis` | Front-end: activación y PIN, Inventario, Caja y Reportes · pruebas E2E |

**Cliente:** el propietario de «El Pardo». **Docente asesor:** Mtro. Abraham López Nájera.

## Referencias

1. A. Cisneros, "Ejemplos de Estudios de Mercado," scribd.com, ago. 2011. [En línea]. Disponible: https://www.scribd.com/doc/62644748/Ejemplo-Estudio-de-Mercado
2. Deep Market Insights, "Mexico Food Trucks Market Size, Share & Trends Report By 2034," deepmarketinsights.com, mar. 2026. [En línea]. Disponible: https://deepmarketinsights.com/vista/insights/food-trucks-market/mexico
3. Ingeniería de Software de Élite, "03 - Ingeniería de Requerimientos - Recolección de requerimientos," YouTube, 31 mar. 2021. [En línea]. Disponible: https://www.youtube.com/watch?v=73fuqZ78uhg
4. J. Martins, "Qué es Scrum: marco ágil, sprints, roles y artefactos," Asana, 9 abr. 2026. [En línea]. Disponible: https://asana.com/es/resources/what-is-scrum?exp=mm
5. Miro, "¿Qué es un diagrama de flujo de proceso? | Guía Completa," miro.com. [En línea]. Disponible: https://miro.com/es/diagrama-de-flujo/que-es-diagrama-flujo-proceso/
6. OWASP Foundation, "OWASP Top 10:2021," owasp.org, 2021. [En línea]. Disponible: https://owasp.org/Top10/

## Licencia

Proyecto académico desarrollado para la Universidad Autónoma de Ciudad Juárez (UACJ). Uso educativo, sin licencia comercial definida.

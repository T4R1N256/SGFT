# Handoff: conversación de Claude.ai → Claude Code (SGFT)

**Fecha:** 24 de septiembre de 2026 · **Quién trabaja contigo:** Alejandro Tarín (`T4R1N256`), Scrum Master, frontend e **integrador** del repositorio: aprueba y fusiona todos los PR.
**Uso:** lee este archivo completo antes de tocar nada. No lo subas al repositorio: es un documento de transición.

## 1. Fuentes de verdad (léelas en este orden)

1. `CLAUDE.md` en la raíz del repo: contexto, alcance, reglas de negocio y convenciones.
2. `.claude/skills/sgft-organizacion-entregables/`, la skill del proyecto:
   - `SKILL.md`: principios de propiedad y procedimiento para ubicar archivos;
   - `assets/ownership.json`: mapa de propiedad, la fuente única de dueños por ruta;
   - `scripts/dueno_de_ruta.py`: `--revisar`, `--persona`, `--wbs`, `--codeowners --salida`, `--verificar`;
   - `references/`: árbol del repo, matriz WBS, fichas por integrante, contrato vista–plantilla, decisiones.
3. `docs/decisiones/`: `contrato-sync-pdv.md` (v1), `nombres-modulo-precios.md`, `organizacion-repositorio.md`, ADR-01, ADR-02 y la convención HTMX/Alpine.
4. `WBS-SGFT.md`, Revisión 4 con ajustes del 24-sep.

Si estos archivos contradicen este handoff, manda lo que esté en el repositorio. Si falta alguno, avísalo antes de continuar.

## 2. Equipo y reparto por capas

| Integrante | GitHub | Capa |
|---|---|---|
| Jesús Hernández | `EduardGarrido` | Backend + base de datos: todos los `models.py` y migraciones, servicios transaccionales, configuración, despliegue |
| Diego Galindo | `Diego-Galindo98` | Backend (usuarios, inventario) + Product Owner |
| Jared Beltrán | `JBeltra16` | Backend (vistas del punto de venta, reportes, CI) |
| Alejandro Tarín | `T4R1N256` | Frontend (base visual, punto de venta, cliente offline) + integrador (aprueba y fusiona todos los PR) |
| Yahir Enríquez | `CodigaBorealis` | Frontend (usuarios, inventario, reportes, E2E) |

## 3. Decisiones vigentes (detalle en `references/decisiones-y-pendientes.md`)

- **DEC-01** — El módulo de precios y el lote de sincronización usan nombres en español: `calcular_total()` / `calcularTotal()` y llaves como `precio_base_centavos`. El resto del código va en inglés.
- **DEC-02 a DEC-06** — Contrato `POST /pos/sync/` v1:
  - lote único `operaciones` con campo `tipo` y llaves en español;
  - respuesta 200 con estado por UUID (`aplicada`, `aplicada_con_revision`, `duplicada`, `cuarentena`);
  - 401 conserva la cola;
  - si el precio cambió, se registra lo cobrado y la venta se marca para revisión.
- **DEC-07** — Paquetes nuevos: 3.3.8 ajuste y cancelación, 3.4.9 bandeja de revisión, 3.5.7 cierre de turno.
- **DEC-08** — Un `tests.py` por app; se convierte en paquete solo tras conflictos repetidos.
- **DEC-09** — Ubicaciones aprobadas y ramas `feat/RF-nn-…`, o `feat/WBS-x.y.z-…` si el paquete no tiene RF.
- **DEC-10 y DEC-16** — CODEOWNERS con revisión obligatoria. Dos rulesets en `main`: solo el integrador fusiona, y PR + code owners + CI sin excepciones.
- **DEC-11** — WBS Revisión 4.
- **DEC-12** — 3.3.1 absorbe a 3.3.2, cuyo código queda retirado.
- **DEC-13** — 3.5.5 = exportar las ventas del día a PDF (se recomienda ReportLab).
- **DEC-14** — A1 del SADT no se descompone; se agrega el paquete 3.1.5, administración de cuentas.
- **DEC-15** — La vista de cocina (3.3.7) está **en evaluación**, fuera de la línea base. No crear sus archivos.
- **DEC-17** — Nombres de archivos y carpetas de **código y pruebas en inglés**:
  - la app es **`pos`**, no `pdv`: `apps/pos/`, `static/pos/`, `templates/pos/`, `/pos/…`, `pos:…`;
  - la carpeta `templates/pos/revision/` pasa a `review/`;
  - `docs/` y la skill conservan sus nombres.
- **DEC-18** — Tarín aprueba todos los PR: figura en todas las rutas de `CODEOWNERS` (`aprobador_general` en el mapa). Los dueños reciben la solicitud de revisión, pero no es obligatoria. Sus propios PR los aprueba otra persona de la ruta.

## 4. Estado al cierre de la conversación

- **Repositorio:** creado en la cuenta de Tarín. No se ha confirmado si ya están el kit (`CODEOWNERS`, plantilla de PR, `docs/decisiones/`), la skill actualizada ni los rulesets.
- **Esqueleto de Django:** generado y probado (SQLite, PostgreSQL 16, Gunicorn). Tarín lo estaba reproduciendo a mano con una guía paso a paso. Contiene:
  - Django 5.2.17 LTS, django-htmx 1.29.0, dj-database-url 3.1.2, python-dotenv 1.2.3, psycopg[binary] 3.3.6, gunicorn 26.2.0, whitenoise 6.12.0;
  - `config/settings.py`, que lee todo de variables de entorno;
  - `AUTH_USER_MODEL = "accounts.User"` con `role` (admin/cashier/cook), una migración inicial y 4 pruebas;
  - las apps `core`, `accounts`, `catalog`, `inventory`, `pos` y `reports` dentro de `apps/`, con `apps/__init__.py`, que es obligatorio: sin él, `manage.py test` corre 0 pruebas.
- **Orden de fusión acordado:** primero el PR de Tarín con la skill y el `CODEOWNERS` actualizados; después el PR del esqueleto (paquete 3.1.1, dueño Jesús).
- **Última duda resuelta:** la `SECRET_KEY` que generó `startproject` sale de `settings.py` y va a `.env` como `DJANGO_SECRET_KEY`. Se recomendó generar una nueva con `python -c "import secrets; print(secrets.token_urlsafe(50))"`.

## 5. Lo primero que debes hacer en el repo local

Solo inspecciona y reporta; no cambies nada todavía.

1. `git status`, `git branch` y `git log --oneline -10`: en qué rama y estado está.
2. Secretos:
   - `git check-ignore .env` debe responder `.env`;
   - `git log --all -S "django-insecure" --oneline` debe salir vacío. Si hay resultados, la clave se publicó y hay que rotarla.
3. Estructura contra el esqueleto:
   - `apps/pos/`, no `pdv`;
   - `apps/__init__.py` presente;
   - cada `apps/<app>/apps.py` con `name = "apps.<app>"`;
   - `settings.py` sin claves escritas;
   - `AUTH_USER_MODEL` definido antes de cualquier `migrate`.
4. `python manage.py check`, `python manage.py makemigrations --check --dry-run` y `python manage.py test`.
5. Rutas contra el mapa:
   `git diff --name-only --diff-filter=d origin/main...HEAD | python .claude/skills/sgft-organizacion-entregables/scripts/dueno_de_ruta.py --revisar`
6. Reporta las diferencias y propón correcciones, indicando de quién es cada archivo según el mapa.

## 6. Reglas de trabajo

- Un archivo, un dueño. Solo Jesús crea o edita `models.py` y migraciones; nadie más corre `makemigrations`.
- Vistas: solo HTTP (rol, plantilla con `request.htmx`, llamada al servicio). La regla de negocio va en `services*.py`; el dinero lo calcula siempre el servidor, salvo `static/pos/pricing.js` sin conexión.
- Toda vista nueva lleva el contrato vista–plantilla en su docstring (`references/contrato-vista-plantilla.md`).
- Idioma: identificadores y comentarios en inglés (salvo DEC-01); textos de interfaz y documentos en español.
- Repositorio público: nunca `.env`, credenciales ni datos reales.

## 7. Pendientes abiertos

- **P1–P3 (Tarín):** copiar el kit, dar permisos y configurar los rulesets. La verificación de CI se activa cuando exista el workflow de Jared.
- **P4–P6 y P9 (Diego):** corregir `CLAUDE.md`, `estructura-y-flujo-datos`, `revision-tecnica-offline`, la convención HTMX/Alpine y ADR-02 (rutas `pdv` → `pos` y `calculate_total`); publicar la WBS Rev. 4 en Word.
- **P7–P8 (Jesús):** los campos de `Sale` que exige el contrato y la cantidad de insumo de los modificadores.
- **Pregunta sin respuesta de Tarín:** ¿se corrigen en la WBS las dependencias de 5.1 (CI) y 5.4 (spike offline) a "Ninguna, tras el esqueleto"? Hoy retrasan el CI y el spike del Sprint 1.
- **DEC-15:** decidir si la vista de cocina (3.3.7) entra; eso define si el rol `cook` se conserva.
- **Aviso técnico para 3.4.1 (Tarín):** un `sw.js` servido desde `/static/pos/` solo controla `/static/pos/`. Habrá que servirlo bajo `/pos/`, con una vista o con el encabezado `Service-Worker-Allowed`.

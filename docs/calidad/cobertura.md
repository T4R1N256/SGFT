# Cobertura de pruebas unitarias (WBS 4.1)

**Medición:** 12-nov-2026, sobre `main` con la E2E (T25) y sin el simulacro (T18). La misma medición corre en cada PR (paso «3. Pruebas (con PostgreSQL) y cobertura» del CI) y deja su resumen en la pestaña del job y el reporte HTML como artefacto `cobertura-html`.

**Cómo se mide:** `coverage run --branch --source=apps,config` sobre `python manage.py test`, por línea y por rama. No cuentan las migraciones, los archivos de pruebas ni `config/wsgi.py`/`asgi.py`. El CI falla si el total baja de **90 %**.

```bash
pip install coverage==7.17.2
coverage run --branch --source=apps,config --omit="*/migrations/*,*/tests*.py,config/wsgi.py,config/asgi.py" manage.py test
coverage report --skip-empty --sort=cover
```

## Resultado

332 pruebas de Django en verde, más las 6 E2E (que se corren aparte con `SGFT_E2E=1`) y 31 de Node (paridad de precios y verificador del PIN).

| Módulo | Sentencias | Ramas | Cobertura |
|---|---:|---:|---:|
| `apps/accounts` (M-USR) | 258 | 46 | 97.4 % |
| `apps/catalog` (Productos) | 366 | 82 | 92.0 % |
| `apps/core` (acceso y base) | 128 | 26 | 97.4 % |
| `apps/inventory` (M-INV) | 238 | 56 | 96.3 % |
| `apps/pos` (M-PDV, turno y sincronización) | 1076 | 240 | 94.1 % |
| `apps/reports` (M-REP) | 271 | 48 | 98.4 % |
| `config` | 51 | 4 | 87.3 % |
| **Total** | **2388** | **502** | **95 %** |

Todos los servicios con reglas de negocio están al 96 % o más: `accounts/services.py`, `catalog/services.py`, `inventory/services.py`, `pos/services_pricing.py` y `reports/services.py` al 100 %; `pos/services.py` al 96 % y `pos/services_cash_session.py` al 95 %.

## Lo que falta cubrir (para T29)

| Archivo | Cobertura | Qué no se prueba |
|---|---:|---|
| `apps/pos/views_sync.py` | 81 % | Las validaciones de cada operación del lote (sin `uuid`, marca de tiempo sin zona, `usuario_id` o `efectivo_inicial_centavos` inválidos, `turno_uuid` mal formado, `tipo` desconocido) y el `IntegrityError` de dos envíos simultáneos del mismo UUID. |
| `config/settings.py` | 86 % | El bloque de producción (`DEBUG=False`) y el error por variable faltante; el CI corre con `DEBUG=False`, pero esas líneas se ejecutan antes de que empiece la medición. |
| `apps/catalog/views.py` | 89 % | Errores de formulario poco comunes en recetas e insumos y algunos 404. |
| `apps/inventory/views.py` | 93 % | Rama de 404 y errores del servicio en compras y mermas. |

Las pruebas E2E (`tests_e2e/`, `SGFT_E2E=1`) y las de Node no entran en esta medición: comprueban los flujos completos y el código de `static/pos/`, que coverage de Python no ve.

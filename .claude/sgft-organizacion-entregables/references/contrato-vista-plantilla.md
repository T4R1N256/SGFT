# Contrato vista–plantilla (costura backend ↔ frontend)

Con la división por capas, casi todo paquete funcional queda partido: un backend escribe la vista y un frontend escribe la plantilla. En Django esa frontera es invisible (la vista hace `render(request, "ruta.html", contexto)` y nada obliga a que la plantilla espere lo mismo), así que se vuelve explícita con un contrato escrito **en el docstring de la vista**, que es el único lugar que ambos lados abren siempre.

Este documento aplica la convención ya aprobada (`convencion-htmx-alpine-SGFT.md`) a la nueva forma de trabajar; no la reemplaza.

## 1. Plantilla del contrato

Copiar al inicio de cada vista que renderiza HTML:

```python
def nombre_de_la_vista(request, ...):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.1                       RF: RF-nn (o "pendiente 1.3.1")
    URL name    : pos:add_item                Método: POST (HTMX) | GET (carga completa)
    Roles       : cashier, admin              (RoleRequiredMixin / decorador de apps/core/mixins.py)
    Precondición: turno de caja abierto       (solo si aplica — regla 12)
    Plantilla   : pos/partials/order_summary.html   [fragmento]  |  pos/order_builder.html  [página]
    HTMX        : hx-target="#order-summary"  hx-swap="outerHTML"
    Contexto    :
        order          Order     pedido en curso; order.status in {"open", "closed"}
        order.items    QuerySet  líneas con quantity, dish.name, subtotal
        order.total    Decimal   calculado en servidor — la plantilla SOLO lo muestra
    Controles (HATEOAS):
        status == "open" y hay ítems  -> botón "Confirmar venta"  (pos:confirm_sale)
        status == "closed"            -> botón "Cancelar / ajustar venta" (pos:cancel_sale)
    Errores     : 403 sin rol · 409 sin turno abierto (mensaje en español dentro del fragmento)
    Backend     : Jared · Plantilla: Tarín
    """
```

Campos obligatorios: Paquete WBS, URL name, Método, Roles, Plantilla (con `[fragmento]` o `[página]`), Contexto y, si la respuesta ofrece acciones, Controles. Los demás se llenan cuando aplican.

## 2. Flujo de trabajo en tres pasos

1. **El backend abre el PR del contrato.** Escribe la firma de la vista, su docstring completo y una implementación mínima que renderiza la plantilla con el contexto prometido (aunque la plantilla todavía sea un esqueleto). Se registra la URL en `urls.py`. El frontend dueño de la plantilla es revisor de este PR: aprobar significa "con este contexto puedo construir la pantalla".
2. **El frontend construye la plantilla contra el contrato**, partiendo de su mockup (2.2.x). Si necesita un dato que no está en el contexto, **no lo calcula en la plantilla ni en Alpine**: pide que se agregue al contrato.
3. **Cualquier cambio posterior al contrato** (renombrar una variable, cambiar el `hx-target`, agregar un control) se hace en un PR que aprueban ambos dueños. Cambiar solo un lado rompe la pantalla sin que ninguna prueba unitaria lo detecte.

Así los dos lados trabajan en paralelo desde el primer día y ninguno bloquea al otro.

## 3. Reglas de ubicación y nombre que el contrato debe respetar

- **Fragmento o página.** Todo lo que se devuelve a una petición HTMX (sin `<html>`, `<head>`, `<body>`) vive en `templates/<app>/partials/`. Una página completa vive en `templates/<app>/` y extiende `base.html`. Si al abrir un archivo no se sabe cuál de los dos es, está mal ubicado (convención §4).
- **Una sola vista para ambos casos.** Cuando la misma pantalla se carga completa y también se refresca por HTMX, la vista elige con `request.htmx` (`django-htmx`); no se crean dos vistas.
- **Nombre de la vista y de la URL = la acción**, no la "parcialidad": `add_item`, `remove_item`, `mark_prepared`. Nunca `add_item_htmx` o `partial_summary` (convención §6).
- **El `id` del destino HTMX vive en la raíz del fragmento** cuando se usa `hx-swap="outerHTML"`: `order_summary.html` empieza con `<div id="order-summary">`. Así el fragmento puede reemplazarse a sí mismo indefinidamente. Los `id` van en minúsculas con guiones.
- **Textos visibles en español; identificadores en inglés** con el glosario de `CLAUDE.md` §9 (`dish`, `order`, `modifier`, `cash_session`, `cash_close`…).

## 4. Qué va de cada lado — tabla de decisión

| Necesidad | Lado | Herramienta | Archivo |
|---|---|---|---|
| Guardar o leer de la base de datos | Backend | HTMX → vista → servicio | `views.py` + `services.py` |
| Total, precio, descuento, existencia, cifra de reporte o corte | Backend | Se calcula en el servicio y llega en el contexto | `services*.py` |
| Qué botones/acciones ofrecer según el estado | Backend decide, frontend dibuja | `{% if %}` sobre datos del contexto (HATEOAS) | plantilla / fragmento |
| Abrir/cerrar un acordeón, mostrar un formulario, stepper de cantidad antes de enviar | Frontend | Alpine `x-data` local | plantilla |
| Formato de dinero o fecha | Frontend | filtro de `apps/core/templatetags/` | plantilla |
| Autorización | Backend | mixin de `apps/core/mixins.py` | `views.py` — ocultar un botón no es control de acceso |
| Calcular el total **sin conexión** | Frontend (pareja) | `calcularTotal()` de `static/pos/pricing.js`, centavos enteros | única excepción, cubierta por la prueba de paridad; el servidor recalcula al sincronizar |

**Aclaración sobre la última fila.** La convención HTMX/Alpine (5-sep-2026) dice que "Alpine nunca calcula dinero". ADR-02 (10-sep-2026) introdujo después el cálculo offline en `pricing.js`. Ambas reglas conviven así: en línea, el dinero lo calcula siempre el servidor; sin conexión, lo calcula únicamente `pricing.js` (no código Alpine suelto), en enteros de centavos, y el servidor lo vuelve a validar al sincronizar.

## 5. Ejemplo completo — 3.3.1 Selección de platillos

**Backend (Jared) — `apps/pos/views.py`:**

```python
# + decorador de rol de apps/core/mixins.py (su nombre final lo fija Jesús en 3.1.3)
def dish_list(request):
    """
    CONTRATO VISTA–PLANTILLA — SGFT
    Paquete WBS : 3.3.1                       RF: pendiente 1.3.1
    URL name    : pos:dish_list               Método: GET (carga completa y HTMX)
    Roles       : cashier, admin
    Plantilla   : pos/partials/dish_list.html [fragmento] si request.htmx
                  pos/order_builder.html      [página]    en otro caso
    HTMX        : hx-target="#dish-list"      hx-swap="outerHTML"
    Contexto    :
        dishes   QuerySet[Dish]  activos, ordenados por categoría
        order    Order           pedido abierto en curso (para los botones "Agregar")
    Controles (HATEOAS):
        por cada dish -> botón "Agregar {{ dish.name }}" (pos:add_item order.id dish.id)
    Backend     : Jared · Plantilla: Tarín
    """
    dishes = Dish.objects.filter(active=True).order_by("category", "name")
    order = ...  # pedido abierto en curso; la regla para obtenerlo vive en pos/services.py
    template = "pos/partials/dish_list.html" if request.htmx else "pos/order_builder.html"
    return render(request, template, {"dishes": dishes, "order": order})
```

**Frontend (Tarín) — `apps/pos/templates/pos/partials/dish_list.html`:** construye la lista usando únicamente `dishes` y `order`, con el botón `hx-post` hacia `pos:add_item` y `hx-target="#order-summary"`, tal como el ejemplo de la convención §5.

## 6. Contrato de sincronización (caso especial del módulo offline)

La costura entre `static/pos/db.js` (Tarín + Yahir) y `sync_operations()` (Jesús + Jared) no es una plantilla sino un lote JSON, así que su contrato no cabe en un docstring. Está **aprobado en su versión 1** (24-sep-2026) en `docs/decisiones/contrato-sync-pdv.md`; la copia está en `assets/repo/docs/decisiones/contrato-sync-pdv.md` de esta skill. En resumen:

- un solo arreglo `operaciones` con campo `tipo` (`"apertura_turno"` / `"venta"`), llaves en español, importes en enteros de centavos;
- el servidor aplica primero aperturas y luego ventas, cada operación en su propia transacción;
- responde 200 con un estado por UUID (`aplicada`, `aplicada_con_revision`, `duplicada`, `cuarentena`), y el cliente borra de su cola todo UUID que aparezca en la respuesta;
- 401 sin sesión: la cola se conserva hasta volver a iniciar sesión;
- si el total del catálogo vigente difiere de lo cobrado, se registra lo cobrado y la venta se marca para revisión.

`db.js` usa `fetch`, que no hereda el `hx-headers` de `base.html`: debe enviar el encabezado `X-CSRFToken` leyendo la cookie `csrftoken`. Cualquier cambio de forma sube `version_contrato` y lo aprueban Jesús, Jared y Tarín.

Convención de uso — Django + HTMX + Alpine.js (SGFT)

Relacionado con: ADR-01 (Arquitectura y stack), acción pendiente 5. Fecha: 5 de septiembre de 2026

Esta guía fija cómo se integran HTMX y Alpine.js en el proyecto Django, para que las peticiones parciales sean predecibles y nadie tenga que "adivinar" cómo funciona el módulo de otra persona.

1. Instalación — nada de npm

En templates/base.html, dentro de <head>, dos líneas y ya:

html
<script src="https://unpkg.com/htmx.org@2"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js"></script>

No hay package.json, no hay node_modules, no hay paso de build. Cualquiera del equipo puede abrir el HTML y ver exactamente qué se está cargando.

1. CSRF: el detalle que rompe HTMX si se te olvida

Django exige el token CSRF en todo POST/PUT/DELETE. HTMX no lo agrega solo. La forma más simple de resolverlo una sola vez para todo el sitio: ponerlo en el <body> de base.html, ya que hx-headers se hereda a todos los elementos hijos.

html
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

Con esto, cualquier petición HTMX en cualquier plantilla que herede de base.html ya manda el token. No hay que repetirlo en cada botón.

1. Dependencia recomendada: django-htmx
   bash
   pip install django-htmx

Agrega django_htmx.middleware.HtmxMiddleware, que da acceso a request.htmx en cada vista (booleano y algunas propiedades más: request.htmx.target, request.htmx.trigger, etc.). Sirve para que una misma vista decida si debe devolver la página completa o solo el fragmento, sin duplicar lógica:

python
def dish_list(request):
dishes = Dish.objects.filter(active=True)
template = "pdv/partials/dish_list.html" if request.htmx else "pdv/dish_list.html"
return render(request, template, {"dishes": dishes})

Justificación para el PR (regla de CLAUDE.md sección 11: no agregar dependencias sin justificar): es una librería pequeña, de un solo mantenedor activo, sin dependencias propias más allá de Django, y evita si/else repetido en cada vista que combine HTMX y carga normal.

1. Estructura de carpetas

Cada app de Django separa sus plantillas completas de sus fragmentos:

apps/pdv/
├── templates/
│ └── pdv/
│ ├── order_builder.html # página completa
│ └── partials/
│ ├── order_summary.html # fragmento que HTMX intercambia
│ └── dish_list.html
├── views.py
└── urls.py

Regla: todo archivo que una vista devuelve como respuesta a una petición HTMX (y que por lo tanto NO es una página completa con <html>/<head>/<body>) vive dentro de partials/. Si al abrir un archivo no se sabe si es una página completa o un fragmento, algo está mal ubicado.

1. Cuándo usar HTMX y cuándo Alpine.js
   Necesitas... Usa
   Guardar o leer algo de la base de datos (agregar un ítem al pedido, marcar una orden como preparada, registrar un cobro, aplicar un descuento de inventario) HTMX, siempre. La lógica de negocio vive en la vista/servicio de Django, nunca en el navegador.
   Un cambio de interfaz que no necesita el servidor (abrir/cerrar un acordeón, mostrar/ocultar un formulario, un contador visual de cantidad antes de confirmar) Alpine.js, con x-data local al componente.
   El total del pedido, el precio, el descuento de inventario o cualquier cifra que aparece en un reporte o en el corte de caja Se calcula siempre en el servidor y se manda ya calculado en el fragmento HTMX. Alpine nunca calcula dinero ni decide reglas de negocio — coincide con la regla de seguridad de CLAUDE.md sección 10: la autorización y las reglas de negocio se validan en el servidor, no en el cliente.

Ejemplo — agregar un platillo al pedido (PDV), con HTMX manejando el POST y devolviendo el resumen ya recalculado por el servidor:

html
<!-- pdv/dish_list.html -->

<button
  hx-post="{% url 'pdv:add_item' order.id dish.id %}"
  hx-target="#order-summary"
  hx-swap="outerHTML">
Agregar {{ dish.name }} — ${{ dish.price }}
</button>
python

# views.py

def add_item(request, order_id, dish_id):
order = get_object_or_404(Order, pk=order_id)
dish = get_object_or_404(Dish, pk=dish_id)
OrderItem.objects.create(order=order, dish=dish, quantity=1, unit_price=dish.price)
return render(request, "pdv/partials/order_summary.html", {"order": order})
html
<!-- pdv/partials/order_summary.html -->
<div id="order-summary">
  <ul>
    {% for item in order.items.all %}
      <li>{{ item.quantity }} × {{ item.dish.name }} — ${{ item.subtotal }}</li>
    {% endfor %}
  </ul>
  <strong>Total: ${{ order.total }}</strong>
</div>

Ejemplo — un stepper de cantidad que es puro adorno visual hasta que se envía (Alpine, sin tocar el servidor todavía):

html
<div x-data="{ qty: 1 }">
  <button type="button" @click="qty = Math.max(1, qty - 1)">−</button>
  <span x-text="qty"></span>
  <button type="button" @click="qty++">+</button>
  <input type="hidden" name="quantity" x-bind:value="qty">
</div>
6. Nomenclatura de endpoints parciales

Las URLs que solo existen para devolver fragmentos HTMX se agrupan bajo el mismo urls.py de la app, sin prefijo especial, pero el nombre de la vista/URL describe la acción, no la "parcialidad": add_item, remove_item, mark_prepared, apply_stock_alert — igual que cualquier otra vista. Lo que las distingue es que renderizan una plantilla de partials/, no que su nombre lleve "htmx" o "partial".

1. Pruebas
   Las vistas que devuelven fragmentos se prueban igual que cualquier vista Django, con django.test.TestCase y self.client.post(...), revisando el HTML devuelto o el estado en base de datos. No hace falta un navegador real para esto.
   Playwright se reserva únicamente para los dos flujos end-to-end críticos ya acordados en el ADR-01 (venta completa en PDV, corte de caja), donde sí importa que HTMX intercambie el DOM correctamente y que Alpine reaccione en un navegador real.
2. Lo que NO se hace
   No se escribe JavaScript suelto en archivos .js propios para lógica que HTMX o Alpine ya cubren declarativamente en el HTML.
   No se duplica en Alpine ningún cálculo que ya hace el servidor (precios, descuentos, totales, validación de stock).
   No se agregan más librerías de JavaScript sin pasar primero por la misma justificación de la sección 3 de este documento.
3. HATEOAS en SGFT

HATEOAS (Hypermedia As The Engine Of Application State) es una de las restricciones originales de REST según la tesis de Roy Fielding (2000): el cliente no debe conocer de antemano, por fuera de la respuesta, qué acciones puede realizar a continuación. Cada respuesta del servidor debe traer, embebidos, los controles (enlaces, formularios) que indican cuáles transiciones de estado son válidas en ese momento. Es el nivel 3 (el más alto) del Richardson Maturity Model — casi ninguna "API REST" en JSON llega a ese nivel: la mayoría se queda en el nivel 2 (recursos + verbos HTTP), porque el cliente igual necesita documentación externa (Swagger/Postman) para saber qué URLs existen y cuándo puede llamarlas.

En la arquitectura de SGFT, HATEOAS no solo se puede implementar: ya está implementado por construcción. La razón es que SGFT no expone una API JSON separada de su interfaz — el HTML que Django devuelve es la hipermedia. Un <a href> o un <form action> siempre han sido controles de hipermedia (es el diseño original de la web, anterior a que "API REST" se volviera sinónimo de JSON); HTMX simplemente extiende ese mismo mecanismo con hx-get/hx-post/hx-target, que son controles de hipermedia con más expresividad que un enlace o un formulario clásico, pero exactamente el mismo principio. El navegador (el cliente) nunca necesita conocer de antemano la estructura de "endpoints" del sistema: solo actúa sobre los controles que el fragmento HTML le ofrece en ese momento.

Ejemplo concreto, ligado a la regla de negocio 7 de CLAUDE.md (toda venta registrada es inmutable): el fragmento order_summary.html decide qué controles incluir según el estado real del pedido en el servidor, no según lo que el cliente "cree" que puede hacer:

html
<!-- pdv/partials/order_summary.html -->
<div id="order-summary">
  <ul>
    {% for item in order.items.all %}
      <li>{{ item.quantity }} × {{ item.dish.name }} — ${{ item.subtotal }}</li>
    {% endfor %}
  </ul>
  <strong>Total: ${{ order.total }}</strong>

{% if order.status == "open" and order.items.exists %}
<button hx-post="{% url 'pdv:confirm_sale' order.id %}"
            hx-target="#order-summary" hx-swap="outerHTML">
Confirmar venta
</button>
{% elif order.status == "closed" %}
<button hx-post="{% url 'pdv:cancel_sale' order.id %}"
            hx-target="#order-summary" hx-swap="outerHTML">
Cancelar / ajustar venta
</button>
{% endif %}
</div>

Antes de confirmar, el único control que aparece es "Confirmar venta" (y solo si hay al menos un ítem — un pedido vacío no ofrece ese control). Una vez que la vista confirm_sale marca la venta como closed, el siguiente fragmento que el servidor devuelve ya no ofrece "Agregar ítem" — porque la venta es inmutable — sino "Cancelar/ajustar", que es la única transición válida según la regla de negocio. El botón "Confirmar venta" nunca vuelve a aparecer para esa venta. La interfaz no decide esto por sí sola ni con una lista de reglas duplicada en Alpine: simplemente refleja lo que el servidor decidió incluir en la representación, que es exactamente lo que pide HATEOAS.

Dónde sí haría falta trabajo adicional: si en el futuro SGFT necesitara una API JSON separada (por ejemplo, si se agregara una app nativa — hoy explícitamente fuera de alcance según el SRS, numeral 1.2.2), ahí HATEOAS no vendría gratis: JSON no es hipermedia por sí mismo, hace falta adoptar un formato explícito de hipermedia (HAL con bloques _links, JSON:API, o Siren) o usar HyperlinkedModelSerializer de Django REST Framework para que las respuestas incluyan enlaces a las transiciones válidas. Como esa API no existe en el alcance actual, no aplica hoy — se deja anotado aquí por si el alcance cambia bajo control de cambios.

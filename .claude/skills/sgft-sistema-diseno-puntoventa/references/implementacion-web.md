# Implementación web del sistema (Django + Tailwind v4 + HTMX/Alpine)

El SGFT usa plantillas de Django con Tailwind v4, HTMX y Alpine (DEC-24). Tailwind se compila con su **CLI autónomo**: un solo ejecutable, sin npm ni Node. El CSS resultante (`app.css`) se sube al repositorio, así que el servidor no necesita paso de compilación. Esta guía traduce el sistema de Figma a esa pila sin agregar dependencias de pago.

## Contenido
1. Dónde vive cada archivo y quién es dueño
2. Tokens CSS y tema de Tailwind
3. Tipografía Outfit (también sin conexión)
4. Recetas de componentes (HTML + CSS)
5. Reglas de presentación con HTMX y Alpine
6. Traspaso diseño → código

---

## 1. Dónde vive cada archivo y quién es dueño

Rutas según la skill `sgft-organizacion-entregables`. Consúltala si una ruta no aparece aquí.

| Archivo | Ruta | Dueño |
|---|---|---|
| Tokens generados | `static/core/css/tokens.css` (copia de `assets/tokens.css`) | Tarín |
| Entrada de Tailwind | `static/core/css/input.css` (importa Tailwind, tokens y componentes; declara los `@source`) | Tarín |
| CSS compilado que carga `base.html` | `static/core/css/app.css` (lo genera el CLI; no se edita) | Tarín |
| Componentes CSS propios | `static/core/css/components.css` | Tarín |
| Fuente Outfit local | `static/core/fonts/outfit-*.woff2` | Tarín |
| Carga de CSS y fuente | `apps/core/templates/base.html` | Tarín (rev. Yahir/Jesús) |
| Formato de dinero | `apps/core/templatetags/` (filtro, p. ej. `{{ total\|dinero }}` → `$4,850.00`) | Tarín |
| CSS del PDV sin conexión | El mismo `static/core/css/app.css`, precargado por el *service worker* | Tarín + Yahir (pareja obligatoria) |
| Mockups y exportaciones | `docs/prototipos/<paquete>/` | Según el paquete WBS 2.2.x |

Primero se usan utilidades de Tailwind con los tokens (`bg-superficie-tarjeta`, `rounded-lg`, `p-lg`). Una clase `sgft-*` en `components.css` solo se escribe cuando un componente de Figma repite la misma combinación en muchas plantillas.

## 2. Tokens CSS y tema de Tailwind

`assets/tokens.css` se genera con `python scripts/tokens.py css` y contiene:
- `--sgft-color-*`: las 26 variables de color.
- `--sgft-<valor documentado>`: nivel, indicador, botón oscuro y demás colores del §2 de `fundamentos.md`.
- `--sgft-radio-*` y `--sgft-espacio-*`.
- `--sgft-sombra-tarjeta` y `--sgft-sombra-boton-primario`.
- `--sgft-gradiente-*`.
- `--sgft-fuente`.
- Un bloque **`@theme inline`** que convierte los tokens en utilidades de Tailwind: `--color-*` (`bg-marca-primario`, `text-texto-secundario`, `border-borde-sutil`, `bg-nivel-bajo`), `--radius-*` (`rounded-md`), `--spacing-*` (`p-lg`, `gap-xs`), `--shadow-*` (`shadow-tarjeta`) y `--font-sans`. Empieza con `--color-*: initial`: **la paleta de Tailwind no existe** (`bg-gray-100` no compila), solo los colores del sistema.
- Una utilidad `bg-gradiente-*` por gradiente.
- Las clases `.sgft-texto-*`, una por estilo de texto de Figma, en `@layer components` para que una utilidad las pueda sobrescribir.

Reglas:
- **No edites `tokens.css` a mano.** Cambia `tokens.json`, regenera y comprueba con `python scripts/tokens.py verificar --css static/core/css/tokens.css` (puede ir en CI).
- `tokens.css` **no se carga en el navegador**: lo importa `input.css` y el CLI lo compila dentro de `app.css`. `base.html` carga solo `app.css`:
  ```html
  <link rel="stylesheet" href="{% static 'core/css/app.css' %}">
  ```
- **Compila después de cambiar clases, tokens o `components.css`** y sube `app.css` en el mismo commit:
  ```bash
  tailwindcss -i static/core/css/input.css -o static/core/css/app.css --minify   # --watch mientras desarrollas
  ```
  Una clase que no aparece en ningún archivo de `@source` no se genera. Por eso las clases se escriben completas en la plantilla (`sgft-badge--{{ level }}` funciona porque `components.css` declara las variantes; `bg-{{ color }}` no funciona).
- **Sin colores sueltos.** No uses valores arbitrarios (`bg-[#EE7023]`, `p-[13px]`) salvo para medidas de retícula de Figma sin token, como `grid-cols-[848fr_400fr]`.

## 3. Tipografía Outfit (también sin conexión)

Outfit tiene licencia OFL y es gratuita. **Sírvela desde `static/` y no desde Google Fonts.** El PDV funciona sin red (ADR-02) y una fuente por CDN no estaría disponible en ese caso. Descarga los 4 pesos en `.woff2` (400, 500, 600, 700) y agrégalos al caché del *service worker* de `static/pos/`.

```css
@font-face { font-family: 'Outfit'; src: url('../fonts/outfit-400.woff2') format('woff2'); font-weight: 400; font-display: swap; }
@font-face { font-family: 'Outfit'; src: url('../fonts/outfit-500.woff2') format('woff2'); font-weight: 500; font-display: swap; }
@font-face { font-family: 'Outfit'; src: url('../fonts/outfit-600.woff2') format('woff2'); font-weight: 600; font-display: swap; }
@font-face { font-family: 'Outfit'; src: url('../fonts/outfit-700.woff2') format('woff2'); font-weight: 700; font-display: swap; }
```

## 4. Recetas de componentes (HTML + CSS)

Son el punto de partida de `components.css`, que `input.css` importa. Van dentro de `@layer components` para que las utilidades de Tailwind les ganen. Todas usan tokens; si necesitas un valor que no existe como token, repasa `auditoria-y-deuda.md` §5 antes de escribirlo.

```css
@layer components {
/* Tarjeta de pantalla */
.sgft-card { background: var(--sgft-color-superficie-tarjeta); border: 1px solid var(--sgft-color-borde-sutil);
  border-radius: 22px; box-shadow: var(--sgft-sombra-tarjeta); padding: 28px; display: flex; flex-direction: column; gap: 20px; }
.sgft-card--media { padding: 24px; gap: 14px; }

/* Encabezado de tarjeta */
.sgft-card-header { display: flex; align-items: center; gap: 20px; }
.sgft-card-header__icon { width: 56px; height: 56px; border-radius: 16px; display: grid; place-items: center;
  background: var(--sgft-color-marca-durazno-200); color: var(--sgft-color-marca-primario-oscuro); }

/* Botones */
.sgft-btn { height: 48px; border-radius: var(--sgft-radio-md); padding: 0 22px 0 20px; gap: 8px;
  display: inline-flex; align-items: center; font-weight: 500; border: 0; cursor: pointer; }
.sgft-btn--primario   { background: var(--sgft-gradiente-accion); color: var(--sgft-color-texto-inverso); box-shadow: var(--sgft-sombra-boton-primario); }
.sgft-btn--secundario { background: var(--sgft-color-marca-durazno-100); color: var(--sgft-color-marca-primario-oscuro); }
.sgft-btn--contorno   { background: var(--sgft-color-superficie-tarjeta); color: var(--sgft-color-texto-primario); border: 1px solid var(--sgft-color-borde-sutil); }
.sgft-btn--oscuro     { background: var(--sgft-color-boton-oscuro-fondo); color: var(--sgft-color-sidebar-texto); border: 1px solid var(--sgft-boton-oscuro-borde); }

/* Insignia */
.sgft-badge { height: 32px; padding: 0 14px 0 12px; border-radius: var(--sgft-radio-sm); display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 500; }
.sgft-badge--exito   { background: var(--sgft-color-estado-exito-fondo);   color: var(--sgft-color-estado-exito); }
.sgft-badge--alerta  { background: var(--sgft-color-estado-alerta-fondo);  color: var(--sgft-color-estado-alerta); }
.sgft-badge--peligro { background: var(--sgft-color-estado-peligro-fondo); color: var(--sgft-color-estado-peligro); }
.sgft-badge--marca   { background: var(--sgft-color-marca-durazno-100);    color: var(--sgft-color-marca-primario-oscuro); }
.sgft-badge--neutral { background: var(--sgft-color-superficie-pista);     color: var(--sgft-color-texto-secundario); }

/* Chip de categoría */
.sgft-chip { height: 40px; padding: 0 18px; border-radius: 12px; font-size: 14px; font-weight: 500;
  background: var(--sgft-color-superficie-tarjeta); border: 1px solid var(--sgft-color-borde-sutil); color: var(--sgft-color-texto-secundario); }
.sgft-chip[aria-pressed="true"] { background: var(--sgft-gradiente-accion); color: var(--sgft-color-texto-inverso);
  border-color: transparent; box-shadow: var(--sgft-sombra-boton-primario); }

/* Barra de nivel (corte duro, --p de 0 a 100) */
.sgft-nivel { height: 8px; border-radius: 4px;
  background: linear-gradient(90deg, var(--c) 0 calc(var(--p) * 1%), var(--sgft-color-superficie-pista) 0); }
}
```

Con Django, el estado sale del servidor y la plantilla solo elige la clase:

```html
<span class="sgft-badge sgft-badge--{{ ingredient.level }}">{{ ingredient.get_level_display }}</span>
<div class="sgft-nivel" style="--p: {{ ingredient.level_pct }}; --c: var(--sgft-nivel-{{ ingredient.level }})"></div>
```

Para que ese mapeo funcione, `level` debe valer `normal`, `bajo` o `critico` (en minúsculas, sin acento). Las tres clases de insignia son alias de estado que `components.css` agrega:
- `.sgft-badge--normal`, de `exito`;
- `.sgft-badge--bajo`, de `alerta`;
- `.sgft-badge--critico`, de `peligro`.

Y las tres variables `--sgft-nivel-*` existen en los tokens (también como utilidades `bg-nivel-normal`, `bg-nivel-bajo` y `bg-nivel-critico`).

**Sidebar y retícula.** El sidebar es un `<nav>` de 270 px fijo con fondo `--sgft-color-sidebar-fondo`. El elemento activo usa `aria-current="page"` y recibe el gradiente `--sgft-gradiente-accion-nav`. El área de contenido tiene `padding: 4px 28px 28px` a la derecha del sidebar y debajo de una barra superior de 112 px. En pantallas de menos de 1200 px el sidebar se colapsa a íconos (72 px). Ese caso **no está diseñado todavía**: es una propuesta y debe ratificarse.

## 5. Reglas de presentación con HTMX y Alpine

- **El dinero se calcula en el servidor.** Importes, totales, subtotales y porcentajes vienen de Django ya formateados con el filtro de dinero. Alpine no calcula precios (regla del proyecto).
- **Chips de categoría.**
  - El filtro de productos usa `hx-get`.
  - El estado activo (`aria-pressed`) se puede alternar con Alpine, porque es solo visual.
- **Pasos de cantidad del ticket.**
  - Restar y Sumar hacen `hx-post` a la vista del ticket y reemplazan la línea o el resumen.
  - Solo en `static/pos/`, sin conexión, la cantidad y el total los calcula `calcularTotal()` (paridad con `calcular_total()`).
- **Candado de PIN.**
  - Un módulo con candado abre el flujo de PIN (`accounts/pin.html`) antes de navegar.
  - El candado es informativo: la autorización se valida en el servidor.
- **Estados de sincronización.**
  - «En línea · N pendientes» se alimenta del conteo de la cola offline.
  - Sin red, el punto cambia a `--sgft-color-estado-alerta` y el texto a «Sin conexión · N pendientes». Es una propuesta: falta diseñarlo en Figma.

## 6. Traspaso diseño → código

1. **Localiza el componente** en Figma y anota su nombre y sus propiedades (`componentes.md`).
2. **Traduce el valor de cada propiedad:**

| Propiedad de Figma | En la plantilla |
|---|---|
| `Variante` / `Tipo` / `Estado` | Modificador de clase (`--primario`, `--exito`) |
| `Texto` | Contenido de la plantilla |
| `Icono` | SVG inline de Lucide con `stroke-width="2"` y `currentColor` |
| `Mostrar icono` | `{% if %}` |

3. **Toma los colores del token**, nunca del inspector: si Dev Mode muestra un hex, busca su token con `tokens.py buscar`.
4. **Compara con la captura de Figma** a 1600 × 900. Las medidas de `pantallas-y-patrones.md` §2 son la referencia.
5. **Si el diseño y el código difieren**, gana el diseño aprobado. Si el diseño es imposible o inaccesible, documenta la diferencia en el PR y avisa al integrador.

---
name: sgft-sistema-diseno-puntoventa
description: Sistema de diseño «PuntoVenta» del SGFT (food truck El Pardo). Especifica colores con valores hex, las 47 variables de Figma (revisión 1.1) con su code syntax, la tipografía Outfit (19 estilos), sombras y foco, gradientes, íconos, radios y espacios, los 20 componentes con sus medidas y la retícula exacta de las pantallas y capas prototipadas. Incluye auditoría de contraste y deuda, tokens en JSON y CSS con tema de Tailwind v4, y helpers probados para use_figma. Úsala siempre que alguien del equipo diseñe, modifique o revise una pantalla, mockup o prototipo del SGFT en Figma (paquetes 2.2.x); cree o extienda un componente, token o estilo; necesite un color, tamaño, radio, sombra, estilo de texto o formato de dato exacto; escriba plantillas Django, CSS o HTML que deban verse como los prototipos; o pregunte por consistencia visual o accesibilidad. Úsala aunque no mencione «sistema de diseño», «tokens» ni «variables».
---

# SGFT · Sistema de diseño PuntoVenta

## Propósito

El SGFT tiene seis pantallas de alta fidelidad en Figma con el estilo de la referencia «PuntoVenta»: sidebar café con ondas naranjas, fondo crema, tarjetas cálidas y acentos naranja. Esta skill convierte ese trabajo en reglas explícitas para que cualquier pantalla nueva, componente o plantilla de código se vea como parte del mismo producto.

Sin esta skill, cada persona toma colores del inspector, inventa tamaños de texto y duplica tarjetas a mano. En pocas semanas habría cinco naranjas, tres grises y textos que no pasan contraste.

Los valores salen de leer el archivo de Figma con la Plugin API (30/09/2026) y se actualizaron a la **revisión 1.1** (29/09/2026, levantada el 03/10/2026): menú lateral oculto, Nueva Venta más grande, cantidad sin pasos +/−, estado de caja y apertura con PIN de administrador. La fuente de verdad legible por máquina es `assets/tokens.json`.

## Referencia rápida

**Archivo:** `xlRs7pLokMUYvE4aKXvQ91` (plan Education). Tiene tres páginas:
- 01 · Prototipos: 6 pantallas (Nueva Venta con caja cerrada y abierta, Productos, Caja, Inventario, Reportes), 7 capas superpuestas y las notas de la rev. 1.1;
- 02 · Componentes: la librería;
- 03 · Guía de estilos.

El archivo de wireframes `lpzclyVBEwmXqs03EzGOD3` **nunca se modifica**.

**Color.** Colección «SGFT · Tokens», modo «Claro», 31 variables `color/…`, con code syntax `var(--sgft-color-…)`.

| Rol | Token → hex |
|---|---|
| Acento | `marca/primario` #EE7023 · `marca/primario-oscuro` #E0621D · `marca/primario-claro` #F59A4E |
| Marca suave | `marca/durazno-100` #FBE6D1 · `marca/durazno-200` #FCDEC2 · `marca/anillo` #F8DCC6 |
| Superficies | `superficie/fondo` #F9F1E8 · `superficie/tarjeta` #FDF8F2 · `superficie/campo` #FFFBF7 · `superficie/pista` #EFE6DD · `borde/sutil` #EFE4D9 |
| Texto | `texto/primario` #2B1A10 · `texto/secundario` #7A695D · `texto/terciario` #A89A90 · `texto/inverso` #FFFFFF |
| Estados (texto/fondo) | éxito #2F7D3A/#E4EFDE · alerta #B7791F/#FDF0D2 · peligro #C23B22/#FBE3DE |
| Sidebar | fondo #3A2718 · pie #2F1F13 · texto #F3E6DA · ícono #E6D2C0 · onda #8A4A1E |
| Rev. 1.1 | `superficie/velo-oscuro` #2B1A10 al 45 % · `superficie/oscura` #2B1A10 · `estado/peligro-solido` #C23B22 · `indicador/en-linea` #6BC47A · `boton-oscuro/fondo` #FFFFFF al 7 % |

Gradiente de acción: `#F58A3C → #E9661F`, horizontal. Lo usan el botón Primario, el chip Activo y la navegación activa.

**Tipografía.** Outfit en cuatro pesos: Regular, Medium, SemiBold y Bold. Todos los estilos llevan interlineado del 140 %, salvo Display y H1, que llevan 120 %.

| Estilo | Peso · tamaño | Tracking |
|---|---|---|
| `Display/Monto XL` | Bold 46 | −1 |
| `Display/Indicador` | Bold 34 | −0.5 |
| `Título/H1` | SemiBold 28 | −0.3 |
| `Título/H2` | SemiBold 22 | −0.2 |
| `Título/H3` | SemiBold 18 | 0 |
| `Cuerpo/Base` | Regular 16 | 0 |
| `Cuerpo/Medio` | Medium 16 | 0 |
| `Cuerpo/Pequeño` | Regular 14 | 0 |
| `Cuerpo/Pequeño Medio` | Medium 14 | 0 |
| `Etiqueta/Mayúsculas` | Medium 12, en MAYÚSCULAS | +1 |
| `Etiqueta/Chip` | Medium 13 | 0 |
| `Display/KPI` | Bold 32 | −0.5 |
| `Título/H2 compacto` | SemiBold 19 | −0.2 |
| `Cuerpo/Grande` · `Cuerpo/Descripción` · `Cuerpo/Nota` | Regular 18 · 13 · 12 | 0 |
| `Número/Precio` · `Número/Importe` | SemiBold 16 · 14 | 0 |
| `Etiqueta/Mini` | SemiBold 12 | 0 |

**Medidas.** Colección «SGFT · Medidas»:
- `radio/xs` 8 · `radio/sm` 10 · `radio/chip` 12 · `radio/md` 14 · `radio/campo` 16 · `radio/lg` 20 · `radio/tarjeta` 22 · `radio/xl` 24 · `radio/pill` 999
- `espacio/xs` 8 · `espacio/sm` 12 · `espacio/md` 16 · `espacio/canal` 20 · `espacio/lg` 24 · `espacio/margen` 28 · `espacio/xl` 32

Radios reales: 22 en tarjetas de pantalla, 18 en tarjetas de producto e insumo, 14 en botones y 16 en miniaturas y buscador.

**Sombras:**
- `Sombra/Tarjeta`: 0 8 28, #8A592B al 7 %.
- `Sombra/Botón primario`: 0 8 18, expansión −4, #ED7024 al 28 %.
- `Foco/Anillo`: 2 px de `superficie/fondo` y 4 px de `marca/primario-oscuro`.

**Retícula:**
- Frame de 1600 × 900. **Sin sidebar fijo** (rev. 1.1): el menú lateral de 270 se abre como capa con el botón «Menú».
- Barra superior de 1600 × 112.
- **Área de contenido:** x 28 → 1572 (1544) y y 116 → 872 (756); margen de 28.
- En el iPhone 17 (402 × 874) el diseño es propuesta: una columna con margen de 16.
- Tarjetas de pantalla: radio 22 y relleno de 28, o de 24 en las medianas.

**Componentes:**
- **Base:**
  - `Botón`: Primario, Secundario, Contorno y Oscuro.
  - `Insignia`: Éxito, Alerta, Peligro, Marca y Neutral.
  - `Chip de categoría`: Activo e Inactivo.
  - `Elemento de navegación`: Activo y Normal, con la opción Requiere PIN.
  - `Botón de ícono`: Neutro, Oscuro, Primario y Peligro; Normal (48) y Compacto (40).
- **Estructura:**
  - `Sidebar`: una variante por pantalla; capa superpuesta.
  - `Barra superior`: menú, logotipo, buscador, `Estado de caja`, total, notificaciones y perfil.
  - `Estado de caja`: Abierta y Cerrada.
  - `Encabezado de tarjeta`.
- **Contenido:**
  - `Tarjeta de producto · Venta`: 352 × 176, Normal, En ticket y Presionada.
  - `Línea de ticket`: sin +/−, con «Quitar» rojo.
  - `Menú de cantidad`, `Aviso de stock`, `Aviso de caja cerrada` y `Diálogo · Abrir caja`.
  - `Tarjeta de producto · Catálogo`.
  - `Tarjeta de insumo`.
  - Fotos e íconos: 41 íconos Lucide de 24 px con trazo 2.

## Principios (el porqué de las reglas)

1. **El naranja significa «aquí está lo importante»**, y solo se usa en tres cosas: la acción principal, el dato protagonista y la pantalla activa. Si todo es naranja, nada lo es. La marca vive en el durazno como superficie y en el naranja como acento. Por eso hay **una sola acción Primaria por vista**.
2. **Los colores de estado tienen un solo significado.** El verde, el ámbar y el rojo son el semáforo del negocio: stock normal, bajo o crítico, y tendencias. Si se usan como decoración, el cajero ya no puede confiar en ellos.
3. **Cada valor sale de un token.** Si un color o tamaño no existe como token, primero se busca el más cercano (`scripts/tokens.py buscar`) y, si no hay, se propone uno nuevo. Nunca se escribe suelto: los valores sueltos son la causa de la deuda documentada en la auditoría.
4. **La interfaz muestra y el servidor decide.** Importes, niveles de stock y permisos (PIN) los calcula Django; el diseño solo los representa. La skill `sgft-organizacion-entregables` fija esa separación, y el diseño la respeta: no hay controles que den a entender que el cliente calcula dinero.
5. **Estructura del wireframe y piel de la referencia.** Las pantallas conservan la distribución de los wireframes aprobados y toman el lenguaje visual de PuntoVenta. Un cambio de estructura se justifica por escrito, como se hizo con «Ticket promedio» en lugar de «Satisfacción».
6. **Datos verosímiles y coherentes.** Los números de ejemplo cuadran entre pantallas: ingresos = efectivo + transferencia, ticket promedio = ingresos / tickets. Un prototipo con datos incoherentes hace que la revisión se enfoque en los números y no en el diseño.

## Flujos de trabajo

### A. Diseñar o modificar una pantalla en Figma
1. Carga `figma-use`, que es obligatoria para `use_figma`. Si vas a crear componentes o tokens, carga también `figma-generate-library`. Confirma con `whoami` que el plan sea *student* o de pago.
2. Lee `references/pantallas-y-patrones.md` para la retícula, los formatos de dato y el prototipo, y `references/figma-recetas.md` para las restricciones y el esqueleto de script.
3. Reutiliza componentes y patrones de `references/componentes.md`. Toma los helpers probados de `assets/figma/helpers-plugin-api.js`.
4. Construye la pantalla en su celda del lienzo (§7 de pantallas), con sidebar y barra superior. El contenido va dentro de 298–1572 × 116–872.
5. Valida con `get_screenshot` y con el checklist de `references/auditoria-y-deuda.md` §7. Actualiza las zonas de navegación.

### B. Crear o extender un componente
1. Revisa si ya existe algo reutilizable, incluidos los patrones del §13 de componentes.
2. Sigue las fases de `figma-generate-library` y el §4 de `references/figma-recetas.md`: auto layout, variables vinculadas, propiedades TEXT, BOOLEAN e INSTANCE_SWAP, y `description`.
3. Documéntalo en `references/componentes.md` y agrégalo a la guía de estilos.

### C. Implementar en código (Django + Tailwind)
1. Lee `references/implementacion-web.md`: rutas y dueños, compilación con el CLI de Tailwind, fuente local para el modo sin conexión y recetas de clases `sgft-*`.
2. Genera o actualiza los tokens:
   ```
   python scripts/tokens.py css --salida static/core/css/tokens.css
   python scripts/tokens.py verificar --css static/core/css/tokens.css
   tailwindcss -i static/core/css/input.css -o static/core/css/app.css --minify
   ```
3. Traduce cada propiedad de Figma a un modificador de clase o a contenido de plantilla. Nunca copies un hex del inspector.

### D. Responder dudas o revisar consistencia
- **Valores concretos:** usa la referencia rápida de arriba y luego `references/fundamentos.md`.
- **Contraste:** `python scripts/tokens.py contraste "#TEXTO" "#FONDO"` o `contraste` sin argumentos para todos los pares.
- **Revisión de una pantalla:** aplica el checklist del §7 de la auditoría y reporta cada punto que falle con su corrección.

## Estado del sistema: lo que hay que saber antes de usarlo

El sistema funciona, pero tiene deuda medida. Los detalles están en `references/auditoria-y-deuda.md`.
- **Contraste.** 10 de 17 pares de texto no cumplen AA. Los casos principales son el texto blanco sobre el gradiente naranja (2.45–3.29) y el naranja sobre fondos claros (2.85–3.35). Hay propuestas concretas, pero la del botón Primario cambia el tono de marca y **la decide el equipo**. Mientras tanto, en diseños nuevos:
  - usa `primario-oscuro` para montos grandes;
  - no pongas texto `terciario` con información esencial.
- **Variables.** No tienen *code syntax* y la mayoría tiene alcances amplios. Radios y espacios no están vinculados a nodos.
- **Estilos de texto.** Unos 155 textos de las pantallas tienen el estilo desvinculado por ajustes de tamaño. Hay 10 estilos nuevos propuestos. Mientras no existan, usa los tamaños de la tabla «Tamaños que se usaron fuera de los estilos» (`fundamentos.md` §4) y no inventes otros.
- **Pendientes de diseño:**
  - estado sin conexión del sidebar y de la barra;
  - modal de PIN de administrador (DEC-24);
  - estados vacíos;
  - foco visible;
  - comportamiento responsivo por debajo de 1200 px.

  Si te piden alguno, diséñalo como **propuesta** con los tokens existentes y márcalo como tal.

## Extender el sistema sin romperlo

- **Pantalla nueva:** va en la siguiente celda libre del lienzo, con su clave en `MODULE_KEY`, su placeholder «… (F2)...» y datos coherentes con las demás.
- **Token o estilo nuevo:** sigue el procedimiento de `auditoria-y-deuda.md` §5. Primero `tokens.json` y `tokens.py verificar`, luego Figma con alcances y *code syntax*, y por último la documentación.
- **Cambios de sistema:** afectan a todas las pantallas (un token, un estilo o un componente base). Van en un PR propio y los ratifica el integrador (Tarín), igual que los cambios de estructura del repositorio.

## Recursos de la skill

| Archivo | Cuándo leerlo o usarlo |
|---|---|
| `references/fundamentos.md` | Valores de color, tipografía, medidas, sombras, gradientes, íconos y emoji, con su uso permitido |
| `references/componentes.md` | Cualquier componente: API, anatomía con medidas, variantes, tokens y reglas; también los patrones que aún son frames |
| `references/pantallas-y-patrones.md` | Retícula, coordenadas de las 6 pantallas, correspondencia con los wireframes, formatos de dato, coherencia de cifras, prototipo y organización del lienzo |
| `references/auditoria-y-deuda.md` | Hallazgos medidos, contraste WCAG con propuestas, plan de corrección y **checklist de conformidad** |
| `references/pantallas-y-fragmentos.md` | Plan de interfaz: regiones, fragmentos HTMX y vistas de cada pantalla, estados vacíos y de error, comportamiento sin red y diseño de los formularios |
| `references/implementacion-web.md` | Llevar el sistema a Django, Tailwind v4, HTMX y Alpine: rutas, dueños, CSS, fuente sin conexión y recetas |
| `references/figma-recetas.md` | Antes de escribir cualquier script `use_figma`: restricciones, IDs, esqueleto, errores conocidos y scripts de auditoría |
| `assets/tokens.json` | Fuente de verdad de los tokens, legible por máquina |
| `assets/tokens.css` | Variables CSS `--sgft-*`, tema de Tailwind (`@theme`) y clases `.sgft-texto-*`. Se genera; no se edita |
| `assets/figma/helpers-plugin-api.js` | Funciones probadas para construir en Figma: `discover`, `pv`, `txt`, `card`, `pageHeader`, `screen`, `donut`, `barChart`, `keyValue`… |
| `scripts/tokens.py` | `contraste`, `buscar`, `css`, `verificar` (este último sale con código 1 si hay errores; sirve en CI) |

## Mantenimiento

Cuando cambie algo en Figma (token, estilo o componente):
1. Actualiza `assets/tokens.json` y los `references/` afectados.
2. Corre `python scripts/tokens.py verificar` y regenera `tokens.css`.
3. Si cambiaste componentes o pantallas, vuelve a correr los scripts de lectura de `figma-recetas.md` §5 y actualiza los conteos de la auditoría.

La skill la mantiene el integrador de frontend (Tarín). Yahir revisa los cambios que afecten a los paquetes 2.2.2–2.2.4.

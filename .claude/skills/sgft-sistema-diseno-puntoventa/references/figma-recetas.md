# Recetas para trabajar el sistema en Figma (MCP · `use_figma`)

Es la experiencia acumulada al construir el sistema. Léela antes de escribir cualquier script de `use_figma` sobre el archivo del SGFT. Complementa, no sustituye, a las skills `figma-use`, que es obligatoria, y `figma-generate-library`, necesaria cuando se crean componentes o tokens.

## Contenido
1. Datos del archivo y del acceso
2. Restricciones de `use_figma` que ya nos costaron un error
3. Esqueleto de un script (pantalla nueva)
4. Crear o extender un componente
5. Scripts de lectura para auditar
6. Validación visual
7. Errores conocidos y su causa

---

## 1. Datos del archivo y del acceso

**Archivos:**

| Archivo | fileKey | Notas |
|---|---|---|
| Vigente | `xlRs7pLokMUYvE4aKXvQ91` | «SGFT · Prototipos UI (estilo PuntoVenta) (Copy)», equipo *al247521's team*, plan Education |
| Obsoleto | `MLJiUTmFunexSyDDBMYsLn` | Cuenta Starter anterior. No trabajes ahí |
| Wireframes | `lpzclyVBEwmXqs03EzGOD3` | **Solo lectura, no se modifica nunca** |

**Páginas:** `0:1` «01 · Prototipos», `2:2` «02 · Componentes» y `2:3` «03 · Guía de estilos».

**IDs estables de la librería.** Aun así, localiza siempre los nodos por nombre; los IDs solo sirven para confirmar.
- `Botón` 5:22, `Insignia` 5:50, `Chip de categoría` 5:55
- `Elemento de navegación` 6:36, `Sidebar` 6:540
- `Barra superior` 7:412, `Encabezado de tarjeta` 7:431
- `Tarjeta de producto · Venta` 7:439, `Línea de ticket` 7:446
- `Tarjeta de producto · Catálogo` 2003:425, `Tarjeta de insumo` 2003:453
- `Foto/Burrito de asada` 3:2, `Foto/Burrito de pollo` 3:3

**Pantallas:** Panel Principal 2004:435, Nueva Venta 2004:673, Productos 2004:1088, Caja 2005:1244, Inventario 2005:1504, Reportes 2005:1840. Las notas son 2005:2306 y la guía 2006:1806.

**Rev. 1.2 (4-oct-2026).** La 1.1 queda intacta para comparar; lo nuevo está en dos páginas:
- `2093:1894` «04 · Componentes · Rev. 1.2»: `Estado de caja` 2093:1895, `Tarjeta de producto · Venta` 2093:1902, `Línea de ticket` 2093:1926, `Menú de cantidad` 2093:1937, `Diálogo · Abrir caja` 2093:1950 y el nuevo `Diálogo · PIN de administrador` 2093:2096. Son copias: los cambios a la 1.1 no les llegan.
- `2093:2138` «05 · Prototipos · Rev. 1.2»: Caja cerrada 2093:2139, Nueva Venta 2093:2335, Productos 2093:2614, Overlay Abrir caja 2093:2879, Overlay Menú de cantidad 2093:2930, Overlay PIN 2093:3246 y las notas 2093:3333.
- El iPhone 17 todavía no tiene marcos; su retícula está en `pantallas-y-patrones.md` §1.

**Límites del MCP:**
- Starter: 20 llamadas al mes. Así se bloqueó el primer intento.
- Education, Pro u Org con asiento Full: 200 llamadas al día.
- `whoami` y `create_new_file` no cuentan.
- Antes de un trabajo grande, confirma con `whoami` que el plan sea *student* o de pago y el asiento *Full*.

## 2. Restricciones de `use_figma` que ya nos costaron un error

**Prohibido en el script:**
- `figma.notify`, `figma.closePlugin`, `figma.viewport.*`;
- `figma.loadAllPagesAsync`, `setPluginData`, `createImageAsync`.

Si necesitas los nodos de otra página, usa `await page.loadAsync()`.

**Páginas:** cada llamada empieza en la primera página (01 · Prototipos). Cambia de página **como máximo una vez** con `await figma.setCurrentPageAsync(page)`.

**Tamaño:** el código admite como máximo 50 000 caracteres. Incluye solo los helpers que uses. Dos o tres pantallas por llamada caben bien, con unos 25–40 kB de código cada una.

**Salida:**
- Devuelve los IDs con `return`.
- Para verificar dentro de la misma llamada, usa `await nodo.screenshot()`.
- `console.log` no se ve.

**Orden y aislamiento:**
- Nunca hagas llamadas `use_figma` en paralelo. Van en secuencia.
- Envuelve cada pantalla en try/catch. Si falla, borra el frame parcial y devuelve el error; no dejes basura en el lienzo.

**Texto:**
- Antes de editar texto, `figma.loadFontAsync({family: 'Outfit', style})`. Los estilos son Regular, Medium, **SemiBold** (sin espacio) y Bold.
- Si cambias `fontSize` o `fontName` después de aplicar un estilo, **el estilo se desvincula** (auditoría H6). Si no existe el estilo que necesitas, créalo primero.
- Para truncar: `textTruncation = 'ENDING'` **antes** de `maxLines`. En el orden inverso se ignora `maxLines`, como pasó con la descripción del catálogo.
- Texto que se ajusta al ancho: `appendChild` → `textAutoResize = 'HEIGHT'` → `layoutSizingHorizontal = 'FILL'` (helper `wrapText`). Si queda en `WIDTH_AND_HEIGHT`, ignora FILL.

**Tamaños en auto layout:**
- `resize()` devuelve el nodo a FIXED. Llama a `resize()` antes de FILL, no después: el botón «Confirmar compra» perdió su FILL por eso.
- `FILL` y `layoutGrow` solo funcionan si el padre ya es auto layout. Primero `appendChild`, luego el tamaño.

**Instancias:**
- Al cambiar el ícono (INSTANCE_SWAP), el trazo vuelve a `#2B1A10`. Recolorea después del cambio (`recolor(firstInstance(b), token)`).
- Para cambiar la variante de una instancia anidada: `nested.setProperties({'Tipo': 'Alerta'})`.

**Emoji:** `node.screenshot()` puede mostrarlos vacíos porque se cargan tarde. Confírmalo con `get_screenshot` antes de «arreglar» algo que no está roto.

## 3. Esqueleto de un script (pantalla nueva)

Copia de `assets/figma/helpers-plugin-api.js` solo las funciones necesarias:
- siempre: `discover`, `pv`, `txt`, `al`, `pad`, `fixed`, `add`, `place`, `frame`, `row`, `col` y `between`;
- según el diseño: `card`, `pageHeader`, `screen`, `button`, `badge`, `chip`, `header`, etc.

Después de los helpers va el esqueleto:

```js
// … helpers …
const SCREEN = { nueva: { name: '07 · Mi pantalla', x: 0, y: 3180, active: 'Caja', search: 'Buscar … (F2)...' } };
function newScreen(key) { const d = SCREEN[key]; return screen(d.name, d.x, d.y, d.active, d.search); }

async function buildNueva() {
  const s = newScreen('nueva');
  await pageHeader(s, 'Título', 'Subtítulo · contexto', [button('Contorno', 'Exportar PDF', 'Descargar')]);
  const c = await card('Bloque principal', CX, 196, 627, 300, s);   // x, y, ancho, alto dentro del área 298..1572 × 116..872
  c.appendChild(header('Bloque principal', 'Gráfica', true));
  // … contenido con txt()/badge()/keyValue() …
  return { screen: s };
}

const ok = await discover();
if (!ok) return { error: 'No se encontró la librería SGFT; no se modificó nada.' };
for (const n of figma.currentPage.children.slice()) if (n.name === SCREEN.nueva.name) n.remove();   // idempotencia
try { const r = await buildNueva(); await r.screen.screenshot(); return { pantalla: r.screen.id, avisos: log }; }
catch (e) { for (const n of figma.currentPage.children.slice()) if (n.name === SCREEN.nueva.name) n.remove(); return { error: e.message }; }
```

Luego, en otra llamada, agrega la clave a `MODULE_KEY` y vuelve a generar las zonas de navegación (función `wireNavigation` del helper; ver `pantallas-y-patrones.md` §6).

## 4. Crear o extender un componente

Sigue las fases de `figma-generate-library`: variables antes que componentes, un componente a la vez y validación después de cada uno. Además, en este sistema:

1. Crea el componente en la página 02 (`await figma.setCurrentPageAsync(compPage)`, una sola vez) debajo de lo existente, desde y ≥ 2200 y sin encimar.
2. Construye con auto layout. Vincula rellenos, bordes y texto a variables con `pv()`. Aplica `Sombra/Tarjeta` si es una superficie elevada.
3. Propiedades:
   - TEXT para cada texto editable: `addComponentProperty('Nombre', 'TEXT', …)` y `componentPropertyReferences = {characters: key}`.
   - BOOLEAN para lo opcional.
   - INSTANCE_SWAP para íconos. **Nunca una variante por ícono.**
4. Variantes con `figma.combineAsVariants(...)`, nombradas `Propiedad=Valor`. Colócalas en rejilla, porque quedan encimadas en (0,0). Máximo unas 30 combinaciones.
5. Escribe `description` en el componente o en el conjunto: qué es, cuándo usarlo y qué regla de negocio representa.
6. Valida con `get_screenshot` del componente. Registra el componente en `componentes.md` y agrégalo a la guía de estilos (página 03).

## 5. Scripts de lectura para auditar

Son de solo lectura y no cuentan como cambios. Úsalos para rehacer el inventario después de cambios grandes.

```js
// Variables con valores, alcances y code syntax
const toHex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
const cols = await figma.variables.getLocalVariableCollectionsAsync();
const vars = await figma.variables.getLocalVariablesAsync();
return vars.map(v => { const col = cols.find(c => c.id === v.variableCollectionId); const val = v.valuesByMode[col.modes[0].modeId];
  return { c: col.name, n: v.name, v: (val && val.r !== undefined) ? toHex(val) : val, s: v.scopes, cs: v.codeSyntax }; });
```

```js
// Textos sin estilo y rellenos sin variable en la página de prototipos
const M = figma.mixed, sinEstilo = {}, sinVariable = {};
for (const t of figma.currentPage.findAll(n => n.type === 'TEXT'))
  if (!t.textStyleId || t.textStyleId === M) { const k = (t.fontName === M ? 'mixed' : t.fontName.style) + ' ' + (t.fontSize === M ? 'mixed' : t.fontSize); sinEstilo[k] = (sinEstilo[k] || 0) + 1; }
for (const n of figma.currentPage.findAll(n => 'fills' in n && Array.isArray(n.fills) && n.type !== 'TEXT'))
  for (const p of n.fills) if (p.type === 'SOLID' && !(p.boundVariables && p.boundVariables.color)) {
    const k = '#' + [p.color.r, p.color.g, p.color.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
    sinVariable[k] = (sinVariable[k] || 0) + 1; }
return { sinEstilo, sinVariable };
```

En los recorridos, protege los valores `figma.mixed` (`fontName`, `fontSize`, `cornerRadius`, `strokeWeight`, `textStyleId`) antes de concatenarlos. Si no, el script falla con «cannot convert symbol to string».

## 6. Validación visual

- Después de cada pantalla, usa `get_screenshot` (máximo 1024 px) del frame.
- Revisa que no haya texto recortado ni tarjetas que desborden su contenido; las tarjetas recortan su contenido, así que un desborde se ve como texto cortado.
- Revisa que la acción Primaria sea única y que los emoji sean visibles.
- Compara siempre con la pantalla hermana: el mismo sidebar, la misma barra y el mismo encabezado en y 116.
- Para cambios de sistema (tokens o estilos), toma capturas de las 6 pantallas y de la guía de estilos.

## 7. Errores conocidos y su causa

| Síntoma | Causa | Solución |
|---|---|---|
| `Cannot write to node with unloaded font` | No se cargó Outfit con ese peso | `loadFontAsync` de los 4 pesos en `discover()` |
| `FILL can only be set on children of auto-layout frames` | Se fijó FILL antes de `appendChild` o el padre no es auto layout | Primero agrega el nodo, luego el tamaño |
| La descripción se muestra en 1 línea aunque `maxLines = 2` | Se fijó `maxLines` antes de `textTruncation` | Fija el truncado primero |
| El botón perdió el ancho completo | `resize()` después de FILL | `resize()` primero |
| El ícono cambiado sale negro | El swap reinicia el trazo | `recolor()` después del swap |
| Emoji vacíos en la captura | Carga diferida | Verifica con `get_screenshot` |
| `in get_parent: The node with id "I…;…" does not exist` | Se leyó `.parent` de nodos internos de una instancia dentro de un `findAll` | Busca por nombre y tipo sin subir por `.parent` |
| `cannot convert symbol to string` | Valor `figma.mixed` | Protégelo con `=== figma.mixed` |
| «You've reached the Figma MCP tool call limit» | Plan Starter (20 al mes) | Trabaja desde la cuenta Education |

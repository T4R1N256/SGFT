/*
 * Helpers del sistema PuntoVenta para use_figma (Plugin API) — versión probada en el archivo
 * "SGFT · Prototipos UI (estilo PuntoVenta)" (fileKey xlRs7pLokMUYvE4aKXvQ91), 30/09/2026.
 *
 * Cómo usarlo:
 *   1. Carga antes las skills figma-use (obligatoria) y, si vas a crear componentes, figma-generate-library.
 *   2. Copia en tu script SOLO las funciones que uses (límite de 50 000 caracteres por llamada) y
 *      termina con tu código: `const ok = await discover(); if (!ok) return {error: ...}` y luego tu pantalla.
 *   3. use_figma: nada de figma.notify, figma.closePlugin, loadAllPagesAsync ni setPluginData; devuelve IDs con return.
 *   4. Cada llamada empieza en la primera página (01 · Prototipos). Cambia de página como máximo una vez.
 *
 * Reglas que estas funciones ya respetan (no las rompas al modificarlas):
 *   - Colores siempre por variable: pv('marca/primario') (sin el prefijo 'color/').
 *   - Texto siempre con estilo: txt(texto, 'Cuerpo/Pequeño', 'texto/secundario'). Si pasas {size} o {weight},
 *     Figma DESVINCULA el estilo (deuda documentada): prefiere un estilo existente.
 *   - resize() antes de FILL; texto que envuelve: appendChild → textAutoResize='HEIGHT' → FILL (wrapText/growText).
 *   - Tras cambiar el ícono de una instancia (INSTANCE_SWAP) hay que recolorearlo: button/badge/header ya lo hacen.
 *   - Truncado: textTruncation='ENDING' ANTES de maxLines.
 */
const FONT = 'Outfit';
const W = 1600, H = 900, SIDEBAR_W = 270;
const CX = 298, CW = 1274, CY = 116; // área de contenido (x inicial, ancho, y inicial)
const MODULES = ['Panel Principal', 'Nueva Venta', 'Productos', 'Inventario', 'Caja', 'Reportes'];
const PALETTE = {
  'color/marca/primario': '#EE7023', 'color/marca/primario-oscuro': '#E0621D', 'color/marca/primario-claro': '#F59A4E',
  'color/marca/durazno-100': '#FBE6D1', 'color/marca/durazno-200': '#FCDEC2', 'color/marca/anillo': '#F8DCC6',
  'color/sidebar/fondo': '#3A2718', 'color/sidebar/pie': '#2F1F13', 'color/sidebar/texto': '#F3E6DA', 'color/sidebar/icono': '#E6D2C0', 'color/sidebar/onda': '#8A4A1E',
  'color/superficie/fondo': '#F9F1E8', 'color/superficie/tarjeta': '#FDF8F2', 'color/superficie/campo': '#FFFBF7', 'color/superficie/pista': '#EFE6DD',
  'color/borde/sutil': '#EFE4D9',
  'color/texto/primario': '#2B1A10', 'color/texto/secundario': '#7A695D', 'color/texto/terciario': '#A89A90', 'color/texto/inverso': '#FFFFFF',
  'color/estado/exito-fondo': '#E4EFDE', 'color/estado/exito': '#2F7D3A', 'color/estado/alerta-fondo': '#FDF0D2', 'color/estado/alerta': '#B7791F',
  'color/estado/peligro-fondo': '#FBE3DE', 'color/estado/peligro': '#C23B22'
};
const LEVEL = { normal: '#5FAE6B', bajo: '#E0A030', critico: '#D2472C' };
const SESSION_TOTAL = '$4,850.00';
const SCREEN = {
  principal: { name: '01 · Panel Principal', x: 0, y: 0, active: 'Panel Principal', search: 'Buscar producto por SKU, nombre o código de barras (F2)...' },
  venta: { name: '02 · Nueva Venta', x: 1760, y: 0, active: 'Nueva Venta', search: 'Buscar platillo por nombre, categoría o código (F2)...' },
  productos: { name: '03 · Productos', x: 0, y: 1060, active: 'Productos', search: 'Buscar platillo en el catálogo (F2)...' },
  caja: { name: '04 · Caja', x: 1760, y: 1060, active: 'Caja', search: 'Buscar ticket, movimiento o monto (F2)...' },
  inventario: { name: '05 · Inventario', x: 0, y: 2120, active: 'Inventario', search: 'Buscar insumo por nombre o unidad (F2)...' },
  reportes: { name: '06 · Reportes', x: 1760, y: 2120, active: 'Reportes', search: 'Buscar en reportes por producto, insumo o fecha (F2)...' }
};
const MODULE_KEY = { 'Panel Principal': 'principal', 'Nueva Venta': 'venta', 'Productos': 'productos', 'Inventario': 'inventario', 'Caja': 'caja', 'Reportes': 'reportes' };
let V = {}, TS = {}, ES = {}, ICON = {}, COMP = {}, PAGES = {};
const log = [];
function hex(h) {
  h = h.replace('#', '');
  return { r: parseInt(h.slice(0, 2), 16) / 255, g: parseInt(h.slice(2, 4), 16) / 255, b: parseInt(h.slice(4, 6), 16) / 255 };
}
function pv(name, op) {
  const v = V['color/' + name];
  if (!v) throw new Error('Variable de color no encontrada: color/' + name);
  const p = figma.variables.setBoundVariableForPaint({ type: 'SOLID', color: { r: 0, g: 0, b: 0 } }, 'color', v);
  return op === undefined ? p : Object.assign({}, p, { opacity: op });
}
function solid(h, op) { return { type: 'SOLID', color: hex(h), opacity: op === undefined ? 1 : op }; }
function grad(a, b, vertical) {
  return {
    type: 'GRADIENT_LINEAR',
    gradientTransform: vertical ? [[0, 1, 0], [-1, 0, 1]] : [[1, 0, 0], [0, 1, 0]],
    gradientStops: [{ position: 0, color: Object.assign(hex(a), { a: 1 }) }, { position: 1, color: Object.assign(hex(b), { a: 1 }) }]
  };
}
function barPaint(p, color) {
  const q = Math.max(0.001, Math.min(p, 0.998));
  return {
    type: 'GRADIENT_LINEAR', gradientTransform: [[1, 0, 0], [0, 1, 0]],
    gradientStops: [
      { position: 0, color: Object.assign(hex(color), { a: 1 }) },
      { position: q, color: Object.assign(hex(color), { a: 1 }) },
      { position: q + 0.001, color: Object.assign(hex('#EFE6DD'), { a: 1 }) },
      { position: 1, color: Object.assign(hex('#EFE6DD'), { a: 1 }) }
    ]
  };
}
function frame(name) { const f = figma.createFrame(); f.name = name; f.fills = []; f.clipsContent = false; return f; }
function al(dir, name, opts) {
  const f = figma.createFrame();
  f.name = name; f.fills = []; f.clipsContent = false;
  f.layoutMode = dir; f.primaryAxisSizingMode = 'AUTO'; f.counterAxisSizingMode = 'AUTO';
  if (opts) for (const k of Object.keys(opts)) f[k] = opts[k];
  return f;
}
function pad(f, t, r, b, l) {
  f.paddingTop = t;
  f.paddingRight = (r === undefined) ? t : r;
  f.paddingBottom = (b === undefined) ? t : b;
  f.paddingLeft = (l === undefined) ? ((r === undefined) ? t : r) : l;
  return f;
}
function fixed(f, w, h) { f.resize(w, h); f.primaryAxisSizingMode = 'FIXED'; f.counterAxisSizingMode = 'FIXED'; return f; }
function add(parent, child, o) {
  parent.appendChild(child);
  if (o) {
    if (o.h) child.layoutSizingHorizontal = o.h;
    if (o.v) child.layoutSizingVertical = o.v;
    if (o.grow) child.layoutGrow = 1;
  }
  return child;
}
function place(parent, child, x, y) { parent.appendChild(child); child.x = x; child.y = y; return child; }
function spacer(name, h) { const s = frame(name || 'Espaciador'); s.resize(1, h || 1); return s; }
function hline(name) { const r = figma.createRectangle(); r.name = name || 'Divisor'; r.resize(100, 1); r.fills = [pv('borde/sutil')]; return r; }
function vline(h, name) { const r = figma.createRectangle(); r.name = name || 'Divisor vertical'; r.resize(1, h); r.fills = [pv('borde/sutil')]; return r; }
async function txt(chars, style, color, op, extra) {
  const t = figma.createText();
  const st = TS[style];
  if (!st) throw new Error('Estilo de texto no encontrado: ' + style);
  await t.setTextStyleIdAsync(st.id);
  t.characters = chars;
  t.fills = [pv(color, op)];
  if (extra) {
    if (extra.weight) t.fontName = { family: FONT, style: extra.weight };
    if (extra.size) t.fontSize = extra.size;
    if (extra.align) t.textAlignHorizontal = extra.align;
    if (extra.name) t.name = extra.name;
  }
  return t;
}
function emoji(ch, size) {
  const t = figma.createText();
  t.fontName = { family: FONT, style: 'Regular' };
  t.fontSize = size; t.characters = ch; t.name = 'Emoji';
  return t;
}
function recolor(node, color, op) {
  if (!node) return;
  const list = node.findAll(n => ('strokes' in n) && Array.isArray(n.strokes) && n.strokes.length > 0);
  for (const n of list) n.strokes = [pv(color, op)];
}
function icon(name, color, size, op) {
  const c = ICON[name];
  if (!c) throw new Error('Ícono no encontrado: Icono/' + name);
  const i = c.createInstance();
  i.resize(size, size);
  recolor(i, color, op);
  i.name = 'Icono/' + name;
  return i;
}
function emojiTile(name, size, ch, fs, radius) {
  const t = al('HORIZONTAL', name, { primaryAxisAlignItems: 'CENTER', counterAxisAlignItems: 'CENTER', cornerRadius: radius });
  fixed(t, size, size);
  t.fills = [grad('#FCE3CC', '#F8CBA4', true)];
  t.appendChild(emoji(ch, fs));
  return t;
}
function setProps(inst, map) {
  const props = inst.componentProperties;
  const out = {};
  for (const k of Object.keys(map)) {
    const key = Object.keys(props).find(p => p === k || p.split('#')[0] === k);
    if (key) out[key] = map[k];
    else log.push('Propiedad "' + k + '" no encontrada en ' + inst.name);
  }
  if (Object.keys(out).length) inst.setProperties(out);
  return inst;
}
function variant(setName, variantName) {
  const s = COMP[setName];
  if (!s) throw new Error('Componente no encontrado: ' + setName);
  const v = s.type === 'COMPONENT_SET' ? s.children.find(c => c.name === variantName) : s;
  if (!v) throw new Error('Variante no encontrada: ' + setName + ' / ' + variantName);
  return v.createInstance();
}
function inst(name) {
  const c = COMP[name];
  if (!c) throw new Error('Componente no encontrado: ' + name);
  return c.createInstance();
}
function firstInstance(node) { return node.findOne(n => n.type === 'INSTANCE'); }
const BTN_ICON_COLOR = { Primario: 'texto/inverso', Secundario: 'marca/primario-oscuro', Contorno: 'texto/secundario', Oscuro: 'marca/primario' };
function button(kind, label, iconName, name) {
  const b = variant('Botón', 'Variante=' + kind);
  const map = { 'Texto': label };
  if (iconName) map['Icono'] = ICON[iconName].id; else map['Mostrar icono'] = false;
  setProps(b, map);
  if (iconName) recolor(firstInstance(b), BTN_ICON_COLOR[kind]);
  b.name = name || ('Botón/' + label);
  return b;
}
const BADGE_COLOR = { 'Éxito': 'estado/exito', 'Alerta': 'estado/alerta', 'Peligro': 'estado/peligro', 'Marca': 'marca/primario-oscuro', 'Neutral': 'texto/secundario' };
function badge(kind, label, iconName) {
  const b = variant('Insignia', 'Tipo=' + kind);
  const map = { 'Texto': label };
  if (iconName) map['Icono'] = ICON[iconName].id; else map['Mostrar icono'] = false;
  setProps(b, map);
  if (iconName) recolor(firstInstance(b), BADGE_COLOR[kind]);
  b.name = 'Insignia/' + label;
  return b;
}
function chip(label, active) {
  const c = variant('Chip de categoría', 'Estado=' + (active ? 'Activo' : 'Inactivo'));
  setProps(c, { 'Texto': label });
  c.name = 'Chip/' + label;
  return c;
}
function header(title, iconName, compact) {
  const h = inst('Encabezado de tarjeta');
  setProps(h, { 'Título': title, 'Icono': ICON[iconName].id });
  recolor(firstInstance(h), 'marca/primario-oscuro');
  if (compact) {
    h.itemSpacing = 14;
    const t = h.findOne(n => n.type === 'TEXT');
    if (t) t.fontSize = 19;
  }
  h.name = 'Encabezado/' + title;
  return h;
}
async function card(name, x, y, w, h, parent) {
  const c = al('VERTICAL', name, { itemSpacing: 20, cornerRadius: 22 });
  fixed(c, w, h);
  pad(c, 28);
  c.fills = [pv('superficie/tarjeta')];
  c.strokes = [pv('borde/sutil')]; c.strokeWeight = 1;
  c.clipsContent = true;
  await c.setEffectStyleIdAsync(ES['Sombra/Tarjeta'].id);
  place(parent, c, x, y);
  return c;
}
function row(name, opts) { return al('HORIZONTAL', name, Object.assign({ counterAxisAlignItems: 'CENTER' }, opts || {})); }
function col(name, opts) { return al('VERTICAL', name, opts || {}); }
function between(name) { return row(name, { primaryAxisAlignItems: 'SPACE_BETWEEN' }); }
function dashedTile(name, w, h) {
  const t = al('VERTICAL', name, { primaryAxisAlignItems: 'CENTER', counterAxisAlignItems: 'CENTER', itemSpacing: 10, cornerRadius: 20 });
  fixed(t, w, h);
  t.fills = [pv('marca/durazno-100', 0.45)];
  t.strokes = [pv('marca/primario', 0.55)]; t.strokeWeight = 1.5; t.dashPattern = [8, 6];
  return t;
}
function plusCircle(size) {
  const c = al('HORIZONTAL', 'Agregar', { primaryAxisAlignItems: 'CENTER', counterAxisAlignItems: 'CENTER', cornerRadius: size / 2 });
  fixed(c, size, size);
  c.fills = [grad('#F58A3C', '#E9661F')];
  c.appendChild(icon('Más', 'texto/inverso', Math.round(size * 0.46)));
  return c;
}
async function react(node, destId) {
  const reaction = {
    trigger: { type: 'ON_CLICK' },
    actions: [{ type: 'NODE', destinationId: destId, navigation: 'NAVIGATE', transition: { type: 'DISSOLVE', easing: { type: 'EASE_OUT' }, duration: 0.25 }, preserveScrollPosition: false }]
  };
  try {
    if (typeof node.setReactionsAsync === 'function') await node.setReactionsAsync([reaction]);
    else node.reactions = [reaction];
  } catch (e) {
    log.push('Interacción no creada en "' + node.name + '": ' + e.message);
  }
}
function screen(name, x, y, active, searchText) {
  const s = frame(name);
  s.resize(W, H); s.x = x; s.y = y;
  s.fills = [pv('superficie/fondo')]; s.clipsContent = true;
  PAGES.proto.appendChild(s);
  const sb = variant('Sidebar', 'Activo=' + active); sb.name = 'Sidebar'; place(s, sb, 0, 0);
  const tb = inst('Barra superior'); tb.name = 'Barra superior'; place(s, tb, SIDEBAR_W, 0);
  setProps(tb, searchText ? { 'Búsqueda': searchText, 'Total sesión': SESSION_TOTAL } : { 'Total sesión': SESSION_TOTAL });
  return s;
}
async function pageHeader(parent, title, subtitle, rightNodes, width) {
  const r = between('Encabezado de página');
  r.resize(width || CW, 60); r.primaryAxisSizingMode = 'FIXED'; r.counterAxisSizingMode = 'AUTO';
  const c = col('Título', { itemSpacing: 4 });
  c.appendChild(await txt(title, 'Título/H1', 'texto/primario'));
  c.appendChild(await txt(subtitle, 'Cuerpo/Pequeño', 'texto/secundario'));
  r.appendChild(c);
  if (rightNodes && rightNodes.length) {
    const g = row('Acciones', { itemSpacing: 12 });
    for (const n of rightNodes) g.appendChild(n);
    r.appendChild(g);
  }
  place(parent, r, CX, CY);
  return r;
}
async function discover() {
  for (const p of figma.root.children) {
    if (p.name.indexOf('Prototipos') >= 0) PAGES.proto = p;
    else if (p.name.indexOf('Componentes') >= 0) PAGES.comp = p;
    else if (p.name.indexOf('Guía de estilos') >= 0) PAGES.guide = p;
  }
  if (!PAGES.comp || !PAGES.proto) return false;
  if (typeof PAGES.comp.loadAsync === 'function') await PAGES.comp.loadAsync();
  const nodes = PAGES.comp.findAll(n => n.type === 'COMPONENT_SET' || (n.type === 'COMPONENT' && (!n.parent || n.parent.type !== 'COMPONENT_SET')));
  for (const n of nodes) {
    if (n.name.indexOf('Icono/') === 0) ICON[n.name.slice(6)] = n;
    else COMP[n.name] = n;
  }
  const required = ['Sidebar', 'Barra superior', 'Botón', 'Insignia', 'Chip de categoría', 'Encabezado de tarjeta',
    'Tarjeta de producto · Venta', 'Línea de ticket', 'Foto/Burrito de asada', 'Foto/Burrito de pollo'];
  for (const r of required) if (!COMP[r]) return false;
  (await figma.variables.getLocalVariablesAsync('COLOR')).forEach(v => { V[v.name] = v; });
  (await figma.getLocalTextStylesAsync()).forEach(s => { TS[s.name] = s; });
  (await figma.getLocalEffectStylesAsync()).forEach(s => { ES[s.name] = s; });
  for (const st of ['Regular', 'Medium', 'SemiBold', 'Bold']) await figma.loadFontAsync({ family: FONT, style: st });
  return true;
}
function money(v, noDecimals) {
  const s = noDecimals ? String(Math.round(v)) : v.toFixed(2);
  const parts = s.split('.');
  return '$' + parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (parts[1] ? '.' + parts[1] : '');
}
function lerpHex(a, b, t) {
  const A = hex(a), B = hex(b);
  const c = k => { const v = Math.round((A[k] + (B[k] - A[k]) * t) * 255).toString(16); return v.length < 2 ? '0' + v : v; };
  return '#' + c('r') + c('g') + c('b');
}
function rect(name, w, h, fills, radius) {
  const r = figma.createRectangle();
  r.name = name; r.resize(Math.max(1, w), Math.max(1, h));
  r.fills = fills || [];
  if (radius) r.cornerRadius = radius;
  return r;
}
function dot(color, size) {
  const e = figma.createEllipse(); e.name = 'Indicador';
  e.resize(size || 8, size || 8); e.fills = [solid(color)];
  return e;
}
function widthFixed(f, w) {
  f.resize(w, Math.max(1, f.height));
  if (f.layoutMode === 'VERTICAL') { f.counterAxisSizingMode = 'FIXED'; f.primaryAxisSizingMode = 'AUTO'; }
  else { f.primaryAxisSizingMode = 'FIXED'; f.counterAxisSizingMode = 'AUTO'; }
  return f;
}
function wrapGrid(name, w, gapX, gapY) {
  const g = al('HORIZONTAL', name, { layoutWrap: 'WRAP', itemSpacing: gapX, counterAxisSpacing: gapY });
  return widthFixed(g, w);
}
function progress(name, w, h, p, fills) {
  const f = frame(name); f.resize(w, h); f.cornerRadius = h / 2; f.clipsContent = true;
  f.fills = [pv('superficie/pista')];
  place(f, rect('Avance', Math.round(w * p), h, fills || [grad('#F58A3C', '#E9661F')], h / 2), 0, 0);
  return f;
}
async function wrapText(parent, chars, style, color, extra) {
  const t = await txt(chars, style, color, undefined, extra);
  parent.appendChild(t);
  t.textAutoResize = 'HEIGHT';
  t.layoutSizingHorizontal = 'FILL';
  return t;
}
function growText(parent, t) {
  parent.appendChild(t);
  t.textAutoResize = 'HEIGHT';
  t.layoutGrow = 1;
  return t;
}
function fillButton(b) {
  b.primaryAxisAlignItems = 'CENTER';
  b.paddingLeft = 12; b.paddingRight = 12;
  return b;
}
function stateBadge(inst0, kind, label) {
  const st = inst0.findOne(n => n.type === 'INSTANCE' && n.name === 'Estado');
  if (!st) { log.push('Sin insignia "Estado" en ' + inst0.name); return; }
  st.setProperties({ 'Tipo': kind });
  setProps(st, { 'Texto': label });
}
async function donut(p, size) {
  const d = frame('Dona de meta'); d.resize(size, size);
  const inner = 0.84, R = size / 2, th = R * (1 - inner), mid = R - th / 2;
  const track = figma.createEllipse(); track.name = 'Pista'; track.resize(size, size);
  track.arcData = { startingAngle: 0, endingAngle: 2 * Math.PI, innerRadius: inner };
  track.fills = [pv('marca/anillo')]; d.appendChild(track);
  const a0 = -Math.PI / 2, a1 = a0 + 2 * Math.PI * p;
  const arc = figma.createEllipse(); arc.name = 'Avance'; arc.resize(size, size);
  arc.arcData = { startingAngle: a0, endingAngle: a1, innerRadius: inner };
  arc.fills = [grad('#F59A4E', '#E0621D')]; d.appendChild(arc);
  const caps = [['Remate inicial', a0], ['Remate final', a1]];
  for (const cp of caps) {
    const cx = R + mid * Math.cos(cp[1]), cy = R + mid * Math.sin(cp[1]);
    const e = figma.createEllipse(); e.name = cp[0]; e.resize(th, th);
    e.fills = [solid(lerpHex('#F59A4E', '#E0621D', cx / size))];
    place(d, e, cx - th / 2, cy - th / 2);
  }
  const center = col('Centro', { primaryAxisAlignItems: 'CENTER', counterAxisAlignItems: 'CENTER', itemSpacing: 2 });
  fixed(center, size, size);
  center.appendChild(await txt((p * 100).toFixed(1) + '%', 'Display/Indicador', 'texto/primario', undefined, { size: 40 }));
  center.appendChild(await txt('de meta', 'Etiqueta/Mayúsculas', 'texto/secundario', undefined, { size: 14 }));
  place(d, center, 0, 0);
  return d;
}
async function stat(iconName, label, value) {
  const c = col('Indicador/' + label, { itemSpacing: 14, counterAxisAlignItems: 'CENTER' });
  pad(c, 6, 8);
  const r = row('Etiqueta', { itemSpacing: 10 });
  r.appendChild(icon(iconName, 'texto/secundario', 22));
  r.appendChild(await txt(label, 'Cuerpo/Base', 'texto/secundario'));
  c.appendChild(r);
  c.appendChild(await txt(value, 'Display/Indicador', 'texto/primario', undefined, { size: 30 }));
  return c;
}
async function barChart(name, w, h, labels, values, o) {
  o = o || {};
  const f = frame(name); f.resize(w, h);
  const axisW = o.axis ? 56 : 0, labelH = 22, top = o.tag ? 34 : 6;
  const plotW = w - axisW, plotH = h - labelH - top;
  const maxV = o.max || Math.max.apply(null, values);
  if (o.axis) {
    for (let k = 0; k <= 2; k++) {
      const y = Math.round(top + plotH - plotH * k / 2);
      place(f, rect('Guía', plotW, 1, [pv('borde/sutil')]), axisW, y);
      const t = await txt(money(maxV * k / 2, true), 'Cuerpo/Pequeño', 'texto/terciario', undefined, { size: 12 });
      place(f, t, 0, y - 9);
    }
  }
  const peakV = Math.max.apply(null, values), peak = values.indexOf(peakV);
  const slot = plotW / values.length, bw = Math.round(Math.min(o.barW || 44, slot * 0.62));
  for (let i = 0; i < values.length; i++) {
    const bh = Math.max(4, Math.round(plotH * values[i] / maxV));
    const x = Math.round(axisW + slot * i + (slot - bw) / 2);
    const b = rect('Barra/' + labels[i], bw, bh, i === peak ? [grad('#F59A4E', '#E0621D', true)] : [pv('marca/durazno-200')]);
    b.topLeftRadius = Math.min(8, bw / 2); b.topRightRadius = Math.min(8, bw / 2);
    place(f, b, x, top + plotH - bh);
    const l = await txt(labels[i], 'Cuerpo/Pequeño', i === peak ? 'texto/primario' : 'texto/secundario', undefined, { size: 12, align: 'CENTER' });
    l.resize(Math.round(slot), l.height); l.textAutoResize = 'HEIGHT';
    place(f, l, Math.round(axisW + slot * i), top + plotH + 6);
    if (i === peak && o.tag) {
      const tg = al('HORIZONTAL', 'Etiqueta de pico', { primaryAxisAlignItems: 'CENTER', counterAxisAlignItems: 'CENTER', cornerRadius: 8 });
      fixed(tg, 70, 24); tg.fills = [pv('texto/primario')];
      tg.appendChild(await txt(money(values[i], true), 'Etiqueta/Chip', 'texto/inverso', undefined, { size: 12 }));
      place(f, tg, Math.round(x + bw / 2 - 35), top + plotH - bh - 30);
    }
  }
  return f;
}
async function rankBadge(n) {
  const b = al('HORIZONTAL', 'Posición', { primaryAxisAlignItems: 'CENTER', counterAxisAlignItems: 'CENTER', cornerRadius: 13 });
  fixed(b, 26, 26);
  b.fills = n <= 3 ? [grad('#F58A3C', '#E9661F')] : [pv('marca/durazno-100')];
  b.appendChild(await txt(String(n), 'Etiqueta/Chip', n <= 3 ? 'texto/inverso' : 'marca/primario-oscuro', undefined, { size: 12, weight: 'SemiBold' }));
  return b;
}
async function keyValue(name, label, value, o) {
  o = o || {};
  const r = between(name);
  const l = row('Etiqueta', { itemSpacing: 8 });
  if (o.icon) l.appendChild(icon(o.icon, 'texto/secundario', 18));
  l.appendChild(await txt(label, o.labelStyle || 'Cuerpo/Pequeño', o.labelColor || 'texto/secundario'));
  r.appendChild(l);
  r.appendChild(await txt(value, o.valueStyle || 'Cuerpo/Pequeño Medio', o.valueColor || 'texto/primario', undefined, o.valueExtra));
  return r;
}
function newScreen(key) { const d = SCREEN[key]; return screen(d.name, d.x, d.y, d.active, d.search); }
async function metricCard(parent, name, x, y, iconName, value, valueColor, bKind, bText, bIcon, note) {
  const c = await card(name, x, y, 627, 200, parent);
  pad(c, 24); c.itemSpacing = 14;
  c.appendChild(header(name, iconName, true));
  const r = between('Valor'); add(c, r, { h: 'FILL' });
  r.appendChild(await txt(value, 'Display/Indicador', valueColor));
  r.appendChild(badge(bKind, bText, bIcon));
  await wrapText(c, note, 'Cuerpo/Pequeño', 'texto/secundario');
  return c;
}
async function alertItem(ch, name, detail, critical) {
  const r = row('Alerta/' + name, { itemSpacing: 12, cornerRadius: 16 }); pad(r, 12, 14);
  r.fills = [pv(critical ? 'estado/peligro-fondo' : 'estado/alerta-fondo')];
  r.appendChild(emojiTile('Miniatura', 44, ch, 22, 12));
  const c = col('Datos', { itemSpacing: 2 }); add(r, c, { grow: true });
  const top = between('Encabezado'); add(c, top, { h: 'FILL' });
  top.appendChild(await txt(name, 'Cuerpo/Pequeño Medio', 'texto/primario'));
  top.appendChild(await txt(critical ? 'Crítico' : 'Bajo', 'Etiqueta/Chip', critical ? 'estado/peligro' : 'estado/alerta', undefined, { size: 12, weight: 'SemiBold' }));
  await wrapText(c, detail, 'Cuerpo/Pequeño', 'texto/secundario', { size: 12 });
  return r;
}

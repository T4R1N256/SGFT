# Pantallas, retícula y reglas de contenido

## Contenido
1. Lienzo y retícula base
2. Las pantallas (coordenadas exactas, rev. 1.1)
3. Correspondencia con los wireframes originales
4. Reglas de contenido y formato de datos
5. Coherencia de los datos de ejemplo
6. Prototipo: navegación e interacciones
7. Organización del lienzo en Figma

---

## 1. Lienzo y retícula base (rev. 1.1)

Todas las pantallas son **frames de 1600 × 900**, con relleno `$superficie/fondo` y recorte activado. Desde la revisión 1.1 (29/09/2026) **no hay sidebar fijo**: el contenido usa todo el ancho y el menú se abre como capa superpuesta.

| Zona | x | y | Ancho × alto | Contenido |
|---|---|---|---|---|
| Barra superior | 0 | 0 | 1600 × 112 | Instancia de `Barra superior` con el placeholder de la pantalla |
| **Área de contenido** | **28** | **116** | **1544 × 756** | Todo lo demás. Termina en x 1572 y y 872; margen de 28 (`espacio/margen`) |
| Encabezado de página | 28 | 116 | 1544 (o 1080) × 58 | Título H1, subtítulo y acciones a la derecha |
| Inicio del contenido bajo el encabezado | 28 | 192–200 | — | Chips en y 192; tarjetas y rejillas en y 196–200 |
| Menú lateral (capa) | 0 | 0 | 270 × 900 | `Sidebar` sobre `superficie/velo-oscuro`; solo cuando se abre |

**Divisiones habituales del área de 1544 px:**

| División | Anchos |
|---|---|
| 2 columnas iguales (Caja) | 760 · 24 · 760 |
| Principal y lateral (Nueva Venta, Inventario) | 1080 · 24 · 440 |
| 4 columnas (Reportes) | 368 · 24 · 368 · 24 · 368 · 24 · 368 |
| Rejilla de venta | 3 columnas de 344 con canal 24 × 18 |

**Capas superpuestas** (página de prototipos, fila «Overlays»):
- **Menú:** `Sidebar` de 270 × 900 en (0, 0) sobre el velo. Se cierra con «Cerrar menú» (Botón de ícono Oscuro Compacto en 208, 35), tocando fuera o al elegir un módulo.
- **Diálogo · Abrir caja:** 480 × 436 centrado (560, 232) sobre el velo.
- **Menú de cantidad:** 300 × 251, a 12 px a la derecha de la tarjeta presionada.

**iPhone 17 (DEC-33, ratificado con el prototipo del 4-oct-2026; Figma solo tiene 1600 × 900).** Las reglas viven en el bloque «Teléfono» de `static/core/css/components.css`.
- **Vertical (402 × 874):** barra con Menú, «Caja» y total, y el buscador en su propia fila (sin marca, campana ni perfil). Chips en una fila desplazable; 2 productos por fila con tarjeta compacta (miniatura de 52, nombre en varias líneas, sin la etiqueta de categoría). Ticket flotante abajo en acordeón: plegado muestra la venta; abierto ocupa toda la pantalla.
- **Horizontal (874 × 402):** barra en una fila: hamburguesa con el naranja del logotipo (sin logotipo ni texto), búsqueda, «Alerta stock» (solo ícono y texto), «Caja» y total. Pantalla fija: solo se desplaza la rejilla. «Nueva venta #0039» (número en `texto/secundario`) y los chips en una fila; 3 productos por fila; ticket de 300 a la derecha en acordeón: plegado muestra la venta; abierto se alarga con todas las líneas y se desplaza completo.

## 2. Las pantallas (coordenadas exactas, rev. 1.1)

Todas las coordenadas son relativas al frame de la pantalla. La barra superior está en todas.

### 01 · Nueva Venta · Caja cerrada — `2045:1946` (lienzo 0, 0)
- Contenido de Nueva Venta deshabilitado: opacidad 35 % y sin interacción. El menú y la barra superior siguen activos.
- `Aviso de caja cerrada` de 520 × 370 en (540, 316): «La caja está cerrada», «Necesitas abrir la caja para iniciar las ventas.», botón «Abrir caja» con Candado y «Requiere PIN de administrador».
- La barra superior muestra `Estado de caja` = Cerrada.

### 02 · Nueva Venta — `2045:2158` (lienzo 1760, 0)
Búsqueda: «Buscar producto por SKU, nombre o código de barras (F2)...»

| Bloque | x, y | Tamaño | Detalle |
|---|---|---|---|
| Encabezado de página | 28, 116 | 1080 × 63 | «Nueva venta» / «Ticket #0039 · Turno matutino · Para llevar». A la derecha, `Aviso de stock` (291 × 63) cuando el servidor reporta insumos bajos o críticos. |
| Categorías | 28, 192 | 492 × 40 | Chips: Todos (activo), Burritos, Desayunos, Guisados, Bebidas; gap 10 |
| Productos del menú | 28, 248 | 1080 × 564 | Rejilla 3 × 3 de `Tarjeta de producto · Venta` de 344 × 176 |
| Herramientas de lista | 28, 824 | 797 × 48 | Ordenar y Filtros (Secundario) y «Mostrando 9 de 16 · Toca para agregar · Mantén presionado para cambiar la cantidad» |
| Ticket en curso | 1132, 116 | 440 × 756 | Pad 25. Contenido debajo de esta tabla. |

Contenido de «Ticket en curso», de arriba abajo:
1. Encabezado compacto «Ticket» con insignia Marca «8 artículos».
2. Seis `Línea de ticket` de 390 × 60, separadas 2.
3. Espacio flexible.
4. «Subtotal (8 artículos)» y monto.
5. «Total» (`Título/H2`) y monto en `Display/Indicador` naranja.
6. «Método de pago»: Efectivo (seleccionado, Secundario con borde) y Transferencia (Contorno), FILL con gap 10.
7. «Confirmar compra»: Primario de 56 de alto y FILL.

### 03 · Productos — `2046:788` (lienzo 0, 1060)
| Bloque | x, y | Tamaño | Detalle |
|---|---|---|---|
| Encabezado de página | 28, 116 | 1544 × 58 | «Productos» / «Catálogo del menú · 9 platillos activos · La edición requiere PIN de administrador». Ordenar y Filtros (Contorno). |
| Catálogo | 28, 200 | 1544 × 664 | Rejilla con salto de línea de `Tarjeta de producto · Catálogo` (238 × 322) y el tile «Agregar platillo». |

### 04 · Caja — `2046:1100` (lienzo 1760, 1060)
Solo Administrador: el módulo lleva candado y pide PIN (DEC-27).

| Bloque | x, y | Tamaño | Detalle |
|---|---|---|---|
| Encabezado de página | 28, 116 | 1544 × 58 | «Caja» / turno, hora de apertura y fondo inicial. |
| Gráfica de ventas | 28, 196 | 1544 × 304 | Chips Hoy/Semana/Mes y gráfica de barras por hora. |
| Ganancias totales | 28, 520 | 760 × 200 | KPI con insignia de tendencia y nota de margen. |
| Mermas totales | 812, 520 | 760 × 200 | KPI en `estado/peligro` con insignia Peligro. |
| Total de hoy | 28, 740 | 760 × 132 | «TOTAL DE HOY» en `Display/Monto XL` y desglose Efectivo/Transferencia. |
| Cierre de turno | 812, 740 | 760 × 132 | «Cierre de turno», «Efectivo esperado en caja», «0 operaciones pendientes de sincronizar» con punto, y «Cerrar caja» (Primario, **sin candado**: el PIN ya se pidió al entrar). Al cerrar, Nueva Venta vuelve al estado «Caja cerrada». |

### 05 · Inventario — `2047:1101` (lienzo 0, 2120)
| Bloque | x, y | Tamaño | Detalle |
|---|---|---|---|
| Encabezado de página | 28, 116 | 1544 × 58 | «Inventario» / «Existencias de insumos · Actualizado hoy a las 10:45 AM · 8 insumos». Ordenar y Filtros. |
| Insumos | 28, 200 | 1080 × 544 | Rejilla de `Tarjeta de insumo`. |
| Agregar insumo | 28, 764 | 528 × 60 | Tile punteado. |
| Insumos bajos | 1132, 200 | 440 × 624 | Encabezado compacto con insignia Peligro «3», tres alertas de stock (390 × 68), «Sugerencia de compra» y las acciones «Registrar compra» (Primario) y «Registrar merma» (Secundario). |

### 06 · Reportes — `2047:1358` (lienzo 1760, 2120)
Sustituye al Panel Principal (ventas, productos, insumos y mermas por periodo).

| Bloque | x, y | Tamaño | Detalle |
|---|---|---|---|
| Encabezado de página | 28, 116 | 1544 × 58 | «Reportes» y acciones. |
| Insumos usados · Productos vendidos · Ventas · Mermas | 28 / 420 / 812 / 1204, 196 | 368 × 580 cada una | Cuatro columnas de tarjetas. |
| Selector de periodo | 28, 800 | 1544 × 52 | «Fecha», campo de fecha de 300 × 52, chips Hoy/Semana/Mes y «Calendario» (Primario) a la derecha. |

## 3. Correspondencia con los wireframes originales

**El archivo de wireframes no se modifica.** Es `lpzclyVBEwmXqs03EzGOD3`, «AdmonAct (Copy)», en una cuadrícula de 2 × 3.

Qué se conserva:
- La posición relativa de los bloques de cada wireframe:
  - Ordenar y Filtros van abajo a la izquierda en Nueva Venta y arriba a la derecha en Productos e Inventario.
  - En Reportes, Fecha va abajo a la izquierda y Calendario abajo a la derecha.
  - «Cerrar/Abrir caja» queda en la tarjeta de cierre.
- Los nombres de los bloques: «Última venta», «Más vendido hoy», «Estado del día», «Insumos bajos», «Total de hoy», etc.

**Cambios justificados:**
1. «Satisfacción» se sustituye por «Ticket promedio», porque el sistema no mide satisfacción.
2. «Total Sesión» es igual a los ingresos del día.
3. El sidebar agrega Caja y Sincronizar y marca con candado los módulos que piden PIN (DEC-24).
4. Reportes agrega «Exportar PDF» (DEC-13).
5. Las miniaturas usan emoji en vez de fotos.

## 4. Reglas de contenido y formato de datos

- **Idioma.** La interfaz está en español de México y usa «tú» implícito, sin tratamiento formal. Los botones van en infinitivo o imperativo breve: «Confirmar compra», «Registrar merma», «Exportar PDF».
- **Dinero.** Se escribe `$4,850.00`: signo pegado, coma de miles, punto y dos decimales. En los ejes de las gráficas va sin decimales, `$1,000`. Nunca se escribe «MXN» ni «pesos».
- **Porcentajes.** Sin espacio y con un decimal: `80.8%`, `+14.2% vs ayer`. Las tendencias llevan el signo explícito.
- **Cantidades.** `pza`/`pzas`, `kg` con un decimal (`8.5 kg`), `uds.` para productos vendidos y `L` para litros.
- **Fechas y horas.**
  - Fecha: `dd/mm/aaaa`.
  - Rango: `21/09/2026 – 27/09/2026`, con guion largo y espacios.
  - Hora: `10:42 AM`.
  - Horas del eje: `07 h`.
- **Identificadores.** `Ticket #0039`, con cuatro dígitos.
- **Separador de metadatos.** Punto medio con espacios: `Turno matutino · Para llevar`.
- **Longitudes máximas.**

| Texto | Máximo |
|---|---|
| Nombre de producto en venta | 2 líneas de 106 px (≈ 30 caracteres) |
| Nombre en el ticket | 1 línea de 122 px (≈ 18 caracteres) |
| Modificadores | ≈ 20 caracteres |
| Insignia | 25 caracteres |
| Descripción de catálogo | 2 líneas (≈ 70 caracteres) |

- **Placeholders del buscador.** Describen qué se busca en esa pantalla y terminan en «(F2)...».
- **Estados vacíos** (propuesta, aún no diseñados): miniatura con emoji, frase en `Cuerpo/Base` secundaria y, si procede, la acción Secundaria. No uses ilustraciones.

## 5. Coherencia de los datos de ejemplo

Los datos de las pantallas cuadran entre sí. Si cambias una cifra, recalcula las que dependen de ella:

- **Día (29/09/2026, turno matutino)**
  - Ingresos $4,850.00 = Efectivo $3,120.00 + Transferencia $1,730.00.
  - 38 tickets × $127.63 ≈ $4,850.00.
  - Meta $6,000.00, al 80.8 %.
  - La suma de ventas por hora (180 + 620 + … + 240) da $4,850.
- **Caja**
  - Efectivo esperado $3,620.00 = fondo $500.00 + efectivo $3,120.00.
  - Ganancia $2,910.00 = $4,850.00 − costo de insumos $1,940.00 (margen del 60 %).
  - Mermas $186.50 = 3.8 % de las ventas.
- **Ticket #0039**
  - 8 artículos, $480.00 = 170 + 75 + 100 + 50 + 30 + 55.
  - Asada ×2 con queso extra da $170.
- **Más vendido**
  - Burrito de asada: 42 uds. × $75 = $3,150.00.
- **Semana del 21 al 27/09/2026**
  - Ventas $31,550.00 = Efectivo $20,450 + Transferencia $11,100.
  - 254 tickets, promedio $124.21.
  - Mermas $742.00 = 2.4 %.
  - Top 6 = 720 uds.
  - Costo de los 7 insumos principales: $9,230.00.

## 6. Prototipo: navegación e interacciones

- **Inicio del flujo:** «SGFT · Recorrido (rev. 1.1)», que arranca en 01 · Nueva Venta · Caja cerrada.
- **Zonas.** Cada pantalla tiene `Zona/Menú` (48 × 48 en 28, 32) que abre su capa «Overlay · Menú · <Pantalla>». En la capa, `Zona/Nav <Módulo>` (226 × 52 en x 22, y = 114 + i·56, i de 0 a 4) navega y `Zona/Cerrar menú` regresa.
- **Caja cerrada → abierta:** `Zona/Abrir caja` abre «Overlay · Abrir caja»; «Abrir caja» del diálogo lleva a 02 · Nueva Venta y «Cancelar» o «Cerrar diálogo» regresan.
- **Menú de cantidad:** mantener presionado «Burrito de asada» abre «Overlay · Menú de cantidad»; «Listo» lo cierra.
- **Transición.** Siempre `ON_CLICK` → `NAVIGATE`, con `DISSOLVE` de 0.25 s y `EASE_OUT`.
- **Pantallas nuevas.** Agrega su clave en `MODULE_KEY`, vuelve a generar las zonas de todas las pantallas (primero borra las que existan con ese nombre) y no dupliques interacciones.

## 7. Organización del lienzo en Figma

**Página 01 · Prototipos**
- Pantallas en una cuadrícula de 2 columnas (x 0 y 1760) por 3 filas (y 0, 1060 y 2120), con 160 px de separación.
- Notas de diseño en (3520, 0), con un ancho de 640.
- Una pantalla nueva va en la siguiente celda libre: x 0 o 1760 y y 3180, luego 4240, etc.

**Página 02 · Componentes**
- Íconos y fotos arriba.
- Componentes base (Botón, Insignia, Chip, Navegación) al centro.
- Sidebar, Barra superior, Encabezado y tarjetas desde y 1600.

**Página 03 · Guía de estilos**
- Un solo frame «Guía de estilos · SGFT» de 1600 de ancho, con colores, tipografía, componentes y reglas.

**Nombres de las capas.** Van en español y describen el contenido: «Estado del día», «Ticket en curso», «Producto/Burrito de asada», «Línea/Café de olla». Nunca uses «Frame 123».

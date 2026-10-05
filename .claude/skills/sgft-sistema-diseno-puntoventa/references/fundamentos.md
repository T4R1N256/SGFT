# Fundamentos del sistema PuntoVenta

Valores levantados directamente del archivo de Figma (lectura con la Plugin API, 30/09/2026). La versión legible por máquina es `assets/tokens.json`; si este documento y el JSON discrepan, gana el JSON y hay que corregir este archivo.

## Contenido
1. Color: variables de la colección «SGFT · Tokens»
2. Colores que existen en los diseños pero no son variables
3. Gradientes
4. Tipografía (Outfit)
5. Medidas: radios y espacios («SGFT · Medidas»)
6. Sombras
7. Iconografía
8. Imágenes y emoji

---

## 1. Color: variables de la colección «SGFT · Tokens»

- **Colección:** «SGFT · Tokens» (`VariableCollectionId:2:4`).
- **Modo:** un solo modo, «Claro».
- **Variables:** 26, de tipo COLOR, en un solo nivel. No hay capa de primitivos ni alias.
- **Nombres:** todas empiezan con `color/`. En código se escriben con el prefijo `--sgft-color-`, por ejemplo `--sgft-color-marca-primario`.

### Marca
| Variable | Hex | Rol |
|---|---|---|
| `color/marca/primario` | `#EE7023` | Acento de marca. Montos protagonistas, total del ticket y punto de notificación. |
| `color/marca/primario-oscuro` | `#E0621D` | Texto e íconos naranja sobre fondos claros: precios, «Agregar…», íconos de encabezado de tarjeta, texto del botón Secundario, monto del Total sesión. |
| `color/marca/primario-claro` | `#F59A4E` | Inicio de gradientes de datos y barras secundarias del ranking. |
| `color/marca/durazno-100` | `#FBE6D1` | Superficie de marca suave: botón Secundario, Insignia Marca, píldora Total sesión, botón Restar, chip de hora, sugerencia de compra. El tile punteado lo usa al 45 %. |
| `color/marca/durazno-200` | `#FCDEC2` | Contenedor del ícono del encabezado de tarjeta, avatar y barras de gráfica que no son el pico. |
| `color/marca/anillo` | `#F8DCC6` | Pista de la dona de meta. |

### Sidebar (solo se usan dentro del sidebar)
| Variable | Hex | Rol |
|---|---|---|
| `color/sidebar/fondo` | `#3A2718` | Fondo del sidebar. |
| `color/sidebar/pie` | `#2F1F13` | Franja de usuario al pie. |
| `color/sidebar/texto` | `#F3E6DA` | Texto de módulos en estado Normal, divisor y texto del botón Oscuro. |
| `color/sidebar/icono` | `#E6D2C0` | Íconos en estado Normal y «En línea · N pendientes». |
| `color/sidebar/onda` | `#8A4A1E` | Tono base de las ondas decorativas. |

### Superficies y bordes
| Variable | Hex | Rol |
|---|---|---|
| `color/superficie/fondo` | `#F9F1E8` | Fondo de toda pantalla. |
| `color/superficie/tarjeta` | `#FDF8F2` | Tarjetas, botón Contorno, chip Inactivo. |
| `color/superficie/campo` | `#FFFBF7` | Buscador y campo de fecha. |
| `color/superficie/pista` | `#EFE6DD` | Pista de barras de progreso y de nivel, Insignia Neutral. |
| `color/borde/sutil` | `#EFE4D9` | Borde de 1 px de tarjetas, campos y chips; divisores de 1 px. |

### Texto
| Variable | Hex | Rol |
|---|---|---|
| `color/texto/primario` | `#2B1A10` | Títulos, nombres, valores de KPI e importes. También es el fondo de la etiqueta de pico en las gráficas. |
| `color/texto/secundario` | `#7A695D` | Subtítulos, etiquetas de indicador, descripciones, placeholder e íconos neutros. |
| `color/texto/terciario` | `#A89A90` | Solo apoyo no esencial: categoría en mayúsculas, ejes, «Método de pago». No cumple AA (ver auditoría). |
| `color/texto/inverso` | `#FFFFFF` | Texto e íconos sobre el gradiente de acción. |

### Estados
| Variable | Hex | Rol |
|---|---|---|
| `color/estado/exito` | `#2F7D3A` | Tendencia positiva, «Disponible», «Normal», «Caja abierta», sincronización al día. |
| `color/estado/exito-fondo` | `#E4EFDE` | Fondo de la Insignia Éxito. |
| `color/estado/alerta` | `#B7791F` | Stock Bajo, «Pocas porciones». |
| `color/estado/alerta-fondo` | `#FDF0D2` | Fondo de la Insignia Alerta y de las alertas de stock Bajo. |
| `color/estado/peligro` | `#C23B22` | Stock Crítico y mermas. La tarjeta crítica lleva un borde de 1.5 px con este color al 45 %. |
| `color/estado/peligro-fondo` | `#FBE3DE` | Fondo de la Insignia Peligro y de las alertas de stock Crítico. |

### Alcances actuales de las variables (scopes)

| Grupo | Alcances |
|---|---|
| `texto/*` | `TEXT_FILL` |
| `borde/sutil` | `STROKE_COLOR` |
| Las otras 21 | `FRAME_FILL`, `SHAPE_FILL`, `TEXT_FILL`, `STROKE_COLOR` |

Consecuencias en el uso diario:
- Ninguna variable tiene *code syntax*.
- Dos variables se usan fuera de su alcance mediante la API:
  - `borde/sutil` pinta el relleno de los divisores;
  - `texto/primario` pinta el fondo de la etiqueta de pico.

  Por eso no aparecen en el selector de Figma si alguien intenta hacer lo mismo a mano. El plan de corrección está en `auditoria-y-deuda.md`.

### Reglas de uso del color
- **Jerarquía de un solo acento.** El naranja se reserva para tres cosas: la acción principal, el dato protagonista y la pantalla activa. Ninguna tarjeta tiene fondo naranja: la marca aparece en durazno (`durazno-100/200`) como superficie y en naranja como acento. Si una vista necesita dos acentos, una de las dos cosas no es principal.
- **Los estados van por pares.** Cada estado usa su texto sobre su fondo (`estado/exito` sobre `estado/exito-fondo`, etc.). No combines el texto de un estado con el fondo de otro ni pongas texto de estado sobre durazno.
- **El sidebar es un mundo aparte.** Los tokens `sidebar/*` no se usan fuera del sidebar, y los de superficie no se usan dentro.
- **Semáforo de inventario.** Normal usa éxito (verde), Bajo usa alerta (ámbar) y Crítico usa peligro (rojo). Es el único significado del verde, el ámbar y el rojo en todo el sistema.

## 2. Colores que existen en los diseños pero no son variables

Están documentados para que nadie invente un valor nuevo. Úsalos tal cual hasta que se conviertan en variables (propuesta en la auditoría).

| Nombre documentado | Valor | Dónde aparece |
|---|---|---|
| `nivel/normal` | `#5FAE6B` | Barra de nivel del insumo en estado Normal. |
| `nivel/bajo` | `#E0A030` | Barra de nivel en estado Bajo. |
| `nivel/critico` | `#D2472C` | Barra de nivel en estado Crítico. |
| `indicador/en-linea` | `#6BC47A` | Punto de 8 px «En línea» en el sidebar y en el cierre de turno. |
| `boton-oscuro/fondo` | `#FFFFFF` al 7 % | Fondo del botón «Activar modo admin». |
| `boton-oscuro/borde` | `#EE7023` al 45 % | Borde de 1 px del mismo botón. |
| `perfil/fondo` | `#F2E6DA` | Círculo del perfil (54 px) en la barra superior. |
| `categoria-foto/fondo` | `#FFFFFF` al 85 % | Píldora de categoría sobre la imagen del catálogo. |
| Remates de la dona | `#EB7E36` / `#F4964B` | Círculos que redondean los extremos del arco. Se calculan interpolando el gradiente «dato» en la posición x del remate. |

Antes de usar un color suelto, corre `python scripts/tokens.py buscar "#RRGGBB"`, que devuelve el token más cercano.

## 3. Gradientes

Figma no tiene variables de gradiente, así que estos se aplican como relleno. La dirección horizontal va de izquierda a derecha. La vertical va de arriba abajo, con matriz `[[0,1,0],[-1,0,1]]`.

| Nombre | Desde → hasta | Dirección | Uso exclusivo |
|---|---|---|---|
| `accion` | `#F58A3C` → `#E9661F` | Horizontal | Botón Primario, chip Activo, botón Sumar, círculo «+», rank 1–3, barra de meta. |
| `accion-nav` | `#F58A3C` → `#EC6C24` | Horizontal | Elemento de navegación Activo. |
| `logotipo` | `#F68B3E` → `#E9661F` | Horizontal | Cuadro de 50 px del logotipo. |
| `dato` | `#F59A4E` → `#E0621D` | Horizontal en la dona, vertical en la barra pico | Dato protagonista de una gráfica. |
| `miniatura` | `#FCE3CC` → `#F8CBA4` | Vertical | Fondo de toda miniatura con emoji. |
| `imagen-catalogo` | `#FDE9D6` → `#F7C79E` | Vertical | Zona de imagen de la tarjeta de catálogo. |
| `onda-1` / `onda-2` / `onda-3` | `#D9702A→#8A4A1E` / `#B85A20→#6E3816` / `#8E4519→#5A2E13` | Vertical | Las tres ondas del sidebar (270 × 289 / 214 / 125). |

La **barra de nivel** no es un gradiente suave. Usa un **corte duro** de cuatro paradas: `[color, color @p, pista @p+0.001, pista]`, con `p` como la proporción de 0 a 1. Así una sola capa dibuja relleno y pista.

## 4. Tipografía (Outfit)

- **Familia única:** Outfit, de Google Fonts, con licencia OFL, gratuita.
- **Pesos cargados:** Regular 400, Medium 500, SemiBold 600 y Bold 700. En Figma el nombre exacto es «SemiBold», sin espacio.
- **Estilos de texto:** 19 desde la rev. 1.1 (los 8 que antes eran «propuestos» ya existen), sin variables vinculadas.

| Estilo | Peso | Tamaño | Interlineado | Tracking | Caja | Uso |
|---|---|---|---|---|---|---|
| `Display/Monto XL` | Bold | 46 | 120 % | −1 px | — | Monto protagonista («Total de hoy»). |
| `Display/Indicador` | Bold | 34 | 120 % | −0.5 px | — | Valor de KPI, total del ticket, % de la dona. |
| `Título/H1` | SemiBold | 28 | 120 % | −0.3 px | — | Título de página. |
| `Título/H2` | SemiBold | 22 | 140 % | −0.2 px | — | Título de tarjeta, precio de catálogo, «Total». |
| `Título/H3` | SemiBold | 18 | 140 % | 0 | — | Nombre en catálogo, monto del Total sesión, «Cierre de turno». |
| `Cuerpo/Base` | Regular | 16 | 140 % | 0 | — | Texto corrido, etiqueta de indicador, campo de fecha. |
| `Cuerpo/Medio` | Medium | 16 | 140 % | 0 | — | Etiqueta de botón y de módulo, nombre de insumo. |
| `Cuerpo/Pequeño` | Regular | 14 | 140 % | 0 | — | Subtítulo de página, placeholder, notas. |
| `Cuerpo/Pequeño Medio` | Medium | 14 | 140 % | 0 | — | Nombre en venta y ticket, filas de reporte, chip. |
| `Etiqueta/Mayúsculas` | Medium | 12 | 140 % | +1 px | MAYÚSCULAS | Categoría, «Método de pago», «Total de hoy». |
| `Etiqueta/Chip` | Medium | 13 | 140 % | 0 | — | Texto de Insignia, estado de sincronización. |
| `Display/KPI` | Bold | 32 | 120 % | −0.5 px | — | Valor de KPI, cantidad del Menú de cantidad, dígitos del PIN. |
| `Título/H2 compacto` | SemiBold | 19 | 140 % | −0.2 px | — | Encabezado de tarjeta compacta, nombre en tarjeta de venta. |
| `Cuerpo/Grande` | Regular | 18 | 140 % | 0 | — | Mensaje del Aviso de caja cerrada. |
| `Cuerpo/Descripción` | Regular | 13 | 140 % | 0 | — | Descripciones, existencias, modificadores del ticket. |
| `Cuerpo/Nota` | Regular | 12 | 140 % | 0 | — | Notas, ejes de gráfica, subtítulos pequeños. |
| `Número/Precio` | SemiBold | 16 | 140 % | 0 | — | Importe de la línea de ticket. |
| `Número/Importe` | SemiBold | 14 | 140 % | 0 | — | Importes en filas, píldora «×N». |
| `Etiqueta/Mini` | SemiBold | 12 | 140 % | 0 | — | Estados cortos de alertas. |

### Tamaños que se usaron fuera de los estilos (histórico, rev. 1.0)

En la rev. 1.1 se crearon casi todos los estilos propuestos (columna derecha); usa el estilo. Solo `Display/Monto XXL` y `Display/Dona` siguen sin existir: eran del Panel Principal, que se eliminó.

| Valor en los frames | Dónde | Estilo propuesto que lo reemplaza |
|---|---|---|
| Bold 52 | Monto «Ingresos totales» del Panel Principal | `Display/Monto XXL` |
| Bold 40 | Porcentaje dentro de la dona | `Display/Dona` |
| Bold 30–32 | Valores de indicador y de reporte | `Display/KPI` (32) |
| SemiBold 19 | Título del encabezado de tarjeta compacto | `Título/H2 compacto` |
| SemiBold 16 | Precio en tarjeta de venta, importe de línea de ticket | `Número/Precio` |
| SemiBold 14 | Importes en filas de reporte | `Número/Importe` |
| Regular 18–19, Medium 20 | Etiquetas del Panel Principal (réplica de la referencia) | `Cuerpo/Grande` (18) |
| Regular 13 | Descripción de catálogo, existencia de insumo, notas | `Cuerpo/Descripción` |
| Regular 12 | Modificadores, detalle de alertas, ejes de gráficas | `Cuerpo/Nota` |
| Medium / SemiBold 12 | Categoría sobre foto, rank, estado «Crítico/Bajo» | `Etiqueta/Mini` |
| Regular 18–60 | Emoji dentro de miniaturas | No aplica: el emoji no lleva estilo |

### Reglas tipográficas
- **Números.** Los montos van en SemiBold o Bold, nunca en Regular. El formato es `$4,850.00`: signo pegado, coma de miles y punto decimal, igual que la referencia.
- **Jerarquía por tarjeta.** Máximo tres niveles: título (H2 o compacto 19), dato (Display o H3) y apoyo (Cuerpo/Pequeño). Si hace falta un cuarto nivel, divide la tarjeta.
- **Mayúsculas.** Solo con `Etiqueta/Mayúsculas`. Nunca se escriben mayúsculas a mano en el texto.
- **Truncado.** Nombre de producto en venta: 2 líneas. Nombre en ticket y en catálogo: 1 línea. Descripción de catálogo: 2 líneas. Siempre con puntos suspensivos.

## 5. Medidas: radios y espacios («SGFT · Medidas»)

- **Colección:** «SGFT · Medidas» (`VariableCollectionId:2:31`).
- **Modo:** «Base».
- **Variables:** 9, de tipo FLOAT.

| Variable | Valor | Alcance |
|---|---|---|
| `radio/sm` | 10 | `CORNER_RADIUS` |
| `radio/md` | 14 | `CORNER_RADIUS` |
| `radio/lg` | 20 | `CORNER_RADIUS` |
| `radio/pill` | 999 | `CORNER_RADIUS` |
| `espacio/xs` | 8 | `WIDTH_HEIGHT`, `GAP` |
| `espacio/sm` | 12 | `WIDTH_HEIGHT`, `GAP` |
| `espacio/md` | 16 | `WIDTH_HEIGHT`, `GAP` |
| `espacio/lg` | 24 | `WIDTH_HEIGHT`, `GAP` |
| `espacio/xl` | 32 | `WIDTH_HEIGHT`, `GAP` |

**Hoy ningún nodo vincula estas variables.** Los radios y espacios se escribieron como números. La escala que realmente usan los frames es esta:

| Radio | Dónde |
|---|---|
| 8 | Botones Restar/Sumar, etiqueta de pico, píldora de categoría sobre foto |
| 10 | Insignia, miniatura de reporte (36 px) |
| 12 | Chip de categoría, chip de hora, miniatura de alerta (44 px) |
| 14 | Botón, elemento de navegación, logotipo, campo de fecha, miniatura de línea de ticket, sugerencia de compra |
| 16 | Buscador, píldora Total sesión, contenedor de ícono (56 px), miniaturas de 56–58 px, fotos, alertas |
| 18 | Tarjeta de producto · Venta, Tarjeta de insumo |
| 20 | Tarjeta de catálogo, tiles punteados |
| 22 | Tarjetas de pantalla (contenedores grandes) |
| 24 | Marco de notas |
| La mitad del alto | Círculos: avatar 44, perfil 54, rank 26, «+» 32/64 |

**Espacios de referencia:**
- **Márgenes de pantalla:** 28.
- **Relleno de tarjeta:**
  - grande, 28;
  - mediana, 24;
  - franja horizontal (tarjetas de 132 de alto), 20 × 28.
- **Separación entre bloques de una tarjeta:** de 12 a 24.
- **Canales entre tarjetas:** 20 a 24 en horizontal y 20 a 24 en vertical.
- **Rejillas:** productos de venta 16 × 16; catálogo 21 × 20; insumos 20 × 16; columnas de reporte 22.
- **Botones:** 20–22 de relleno horizontal; 8 entre ícono y texto.

Usa múltiplos de 2 y prefiere la escala 8 · 12 · 16 · 20 · 24 · 28.

## 6. Sombras

| Estilo de efecto | Definición | CSS | Se aplica a |
|---|---|---|---|
| `Sombra/Tarjeta` | DROP_SHADOW `#8A592B` 7 %, y 8, desenfoque 28, expansión 0 | `0 8px 28px 0 rgba(138,89,43,.07)` | Tarjetas, buscador, tarjetas de producto e insumo. |
| `Sombra/Botón primario` | DROP_SHADOW `#ED7024` 28 %, y 8, desenfoque 18, expansión −4 | `0 8px 18px -4px rgba(237,112,36,.28)` | Solo elementos con el gradiente `accion`: botón Primario, chip Activo, nav Activo, logotipo. |

Ningún otro elemento lleva sombra. La elevación la marca el cambio de superficie: de fondo a tarjeta y a campo.

## 7. Iconografía

- **Juego:** 41 componentes `Icono/<Nombre>` de estilo Lucide (rev. 1.1 agregó `Menú` y `Chevron derecha`).
- **Marco:** 24 × 24.
- **Trazo:** 2 px, con extremos y uniones redondeados. Sin relleno.
- **Color del componente:** `#2B1A10`. En cada uso se recolorea con una variable.

| Módulo o función | Ícono |
|---|---|
| Abrir menú | `Menú` |
| Nueva Venta | `Carrito` |
| Productos | `Paquete` |
| Inventario | `Portapapeles` |
| Caja | `Cartera` |
| Reportes | `Gráfica` |
| Sincronizar | `Sincronizar` |
| Modo admin | `Escudo` |
| Candado de PIN | `Candado` |
| Buscar | `Buscar` |
| Notificaciones | `Campana` |
| Perfil | `Usuario` |
| Cerrar sesión | `Salir` |
| Agregar / quitar | `Más` / `Menos` |
| Filtrar / ordenar | `Filtro` / `Ordenar` |
| Tendencias | `Tendencia arriba` / `Tendencia abajo` |
| Ticket | `Recibo` |
| Más vendido | `Corona` |
| Tickets (indicador) | `Boleto` |
| Clientes | `Personas` |
| Fecha | `Calendario` |
| Alertas | `Alerta` |
| Merma | `Basura` |
| Editar | `Lápiz` |
| Efectivo | `Billete` |
| Transferencia | `Transferencia` |
| Exportar | `Descargar` |
| Confirmar | `Check` |
| Desplegable | `Chevron abajo` |
| Ir a (aviso de stock) | `Chevron derecha` |
| Hora | `Reloj` |
| Nube / sin red | `Nube` |
| Otras | `Tienda`, `Estrella`, `Más opciones`, `Cerrar`, `Cubiertos` |

Tamaños en uso (px):

| Tamaño | Dónde |
|---|---|
| 14 | Candado del tile, Restar/Sumar |
| 16 | Insignia, candado del nav |
| 18 | Filas clave-valor, chevron |
| 20 | Botón, buscador, calendario |
| 22 | Módulo del sidebar, indicador del Panel Principal, cerrar sesión |
| 24 | Perfil |
| 28 | Encabezado de tarjeta, campana |

El color depende del contexto:

| Contexto | Color del ícono |
|---|---|
| Sobre el gradiente de acción | `texto/inverso` |
| En botón Secundario y encabezado de tarjeta | `marca/primario-oscuro` |
| Neutro | `texto/secundario` |
| Insignia | El color de texto de su estado |

## 8. Imágenes y emoji

- **Fotografía real:** solo en el Panel Principal. Son los componentes `Foto/Burrito de asada` (280 × 207) y `Foto/Burrito de pollo` (96 × 96), ambos con radio 16.
- **Miniaturas con emoji:** en el resto del sistema cada producto e insumo se representa con un emoji sobre el gradiente `miniatura`. La tabla indica el tamaño del cuadro y el del emoji.

| Dónde | Cuadro | Emoji |
|---|---|---|
| Venta | 56 | 30 |
| Ticket | 48 | 26 |
| Insumo | 58 | 30 |
| Alerta | 44 | 22 |
| Reporte | 36 | 18 |
| Catálogo | 238 × 120 | 60 |

- **Emoji por categoría:**

| Categoría | Emoji |
|---|---|
| Burritos | 🌯 |
| Desayunos | 🍳 🥘 |
| Guisados | 🍲 🌶️ 🍖 |
| Bebidas | ☕ 🥛 🥤 🍊 |

- **Emoji por insumo:**

| Insumo | Emoji |
|---|---|
| Tortilla | 🌮 |
| Carne | 🥩 |
| Pollo | 🍗 |
| Queso | 🧀 |
| Frijol | 🥣 |
| Huevo | 🥚 |
| Chile | 🌶️ |

- **Qué emoji usar:** solo los de Unicode ≤ 12 (🫓 y 🫘 no se ven en todos los equipos).
- **Capturas con emoji vacío:** las capturas rápidas (`node.screenshot()`) pueden mostrar emoji vacíos porque se cargan tarde. Verifica con `get_screenshot` antes de concluir que falta algo.

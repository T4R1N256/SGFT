# Componentes del sistema PuntoVenta

Todos viven en la página **02 · Componentes** del archivo `xlRs7pLokMUYvE4aKXvQ91`. Actualizado a la **revisión 1.1** (29/09/2026): cada componente de Figma trae además una `description` con sus reglas, que manda si difiere de este documento. Aquí se documenta el API (propiedades), la anatomía con medidas exactas, los tokens de cada parte y las reglas de uso.

Notación usada en la anatomía:
- `H` y `V` son auto layout horizontal y vertical.
- El relleno (`pad`) se da en el orden arriba/derecha/abajo/izquierda.
- `$token` es una variable vinculada; un hex suelto no está vinculado.

## Contenido
1. Botón · 2. Insignia · 3. Chip de categoría · 4. Elemento de navegación · 5. Sidebar · 6. Barra superior · 7. Encabezado de tarjeta · 8. Tarjeta de producto · Venta · 9. Línea de ticket · 10. Tarjeta de producto · Catálogo · 11. Tarjeta de insumo · 12. Fotos e íconos · 13. Patrones de pantalla (no son componentes) · 14. Botón de ícono · 15. Estado de caja · 16. Menú de cantidad · 17. Aviso de stock · 18. Aviso de caja cerrada · 19. Diálogo · Abrir caja

---

## 1. Botón — `COMPONENT_SET` `5:22`

**API:**
- `Variante`: Primario | Secundario | Contorno | Oscuro
- `Texto` (TEXT, por defecto «Botón»)
- `Icono` (INSTANCE_SWAP)
- `Mostrar icono` (BOOLEAN)

**Anatomía:**
- Contenedor `H`, gap 8, pad 0/22/0/20, centrado.
- Alto fijo de 48; el ancho se ajusta al contenido. Radio 14.
- `Icono` de 20 × 20 (swap + visibilidad).
- `Texto` en `Cuerpo/Medio`.

| Variante | Relleno | Borde | Texto e ícono | Sombra |
|---|---|---|---|---|
| Primario | gradiente `accion` | — | `$texto/inverso` | `Sombra/Botón primario` |
| Secundario | `$marca/durazno-100` | — | `$marca/primario-oscuro` | — |
| Contorno | `$superficie/tarjeta` | `$borde/sutil` 1 | `$texto/primario` (ícono `texto/secundario`) | — |
| Oscuro | `#FFFFFF` 7 % | `#EE7023` 45 %, 1 | `$sidebar/texto` (ícono `marca/primario`) | — |

**Tamaños en uso:**

| Alto | Dónde | Ajustes |
|---|---|---|
| 48 | Estándar | — |
| 56 | «Confirmar compra» | Ancho completo |
| 40 | Dentro de la tarjeta de catálogo | Pad lateral 10, ícono 16 |

Cuando el botón ocupa todo el ancho: FILL, contenido centrado y pad lateral 12.

**Reglas:**
- **Una sola acción Primaria por vista.** «Confirmar compra», «Cerrar caja», «Registrar compra» y «Calendario» son las primarias de sus pantallas.
- **Secundario:** acción alterna del mismo flujo (Ordenar, Filtros en venta, Registrar merma, Receta).
- **Contorno:** acciones de herramienta en encabezados (Ordenar, Filtros, Exportar PDF) y la opción no seleccionada de un par (Transferencia).
- **Oscuro:** solo sobre `sidebar/fondo`.
- **Seleccionado en un grupo** (método de pago): usa Secundario con borde `$marca/primario` al 60 %, 1.5 px.
- **Íconos:** después de cambiar el `Icono`, recolorea el vector. El swap pierde el color. Colores: Primario `texto/inverso`, Secundario `marca/primario-oscuro`, Contorno `texto/secundario`, Oscuro `marca/primario`.

## 2. Insignia — `COMPONENT_SET` `5:50`

**API:**
- `Tipo`: Éxito | Alerta | Peligro | Marca | Neutral
- `Texto` (TEXT)
- `Icono` (INSTANCE_SWAP)
- `Mostrar icono` (BOOLEAN)

**Anatomía:**
- Contenedor `H`, gap 6, pad 0/14/0/12.
- Alto fijo de 32 (26 dentro de la tarjeta de insumo). Radio 10.
- Ícono de 16 y texto en `Etiqueta/Chip`.

| Tipo | Fondo | Texto e ícono | Significado |
|---|---|---|---|
| Éxito | `$estado/exito-fondo` | `$estado/exito` | Tendencia positiva, Disponible, Normal, Caja abierta |
| Alerta | `$estado/alerta-fondo` | `$estado/alerta` | Stock bajo, Pocas porciones |
| Peligro | `$estado/peligro-fondo` | `$estado/peligro` | Crítico, mermas, conteo de alertas |
| Marca | `$marca/durazno-100` | `$marca/primario-oscuro` | Conteos neutros de marca («8 artículos», «$3,150.00 en ventas») |
| Neutral | `$superficie/pista` | `$texto/secundario` | Identificadores («Ticket #0038») |

**Reglas:**
- El ícono es opcional. Úsalo solo para tendencias (`Tendencia arriba/abajo`), `Check` o `Alerta`.
- El texto debe caber en una línea y tener como máximo 25 caracteres.
- La insignia nunca es un botón: no lleva interacción.

## 3. Chip de categoría — `COMPONENT_SET` `5:55`

**API:**
- `Estado`: Activo | Inactivo
- `Texto` (TEXT)

**Anatomía:**
- Contenedor `H`, pad 0/18.
- Alto fijo de 40. Radio 12.
- Texto en `Cuerpo/Pequeño Medio`.

| Estado | Relleno | Borde | Texto | Sombra |
|---|---|---|---|---|
| Activo | gradiente `accion` | — | `$texto/inverso` | `Sombra/Botón primario` |
| Inactivo | `$superficie/tarjeta` | `$borde/sutil` | `$texto/secundario` | — |

**Uso:**
- Filtros de categoría en Nueva Venta, con gap 10.
- Periodo Hoy/Semana/Mes en Caja y Reportes, con gap 8.
- Siempre hay exactamente un chip Activo por grupo.

## 4. Elemento de navegación — `COMPONENT_SET` `6:36`

**API:**
- `Estado`: Activo | Normal
- `Texto` (TEXT)
- `Icono` (INSTANCE_SWAP)
- `Requiere PIN` (BOOLEAN): muestra el candado.

**Anatomía:**
- Contenedor `H`, gap 16, pad 0/16/0/18. Tamaño fijo de 226 × 52. Radio 14.
- Ícono de 22.
- Texto en `Cuerpo/Medio`, con FILL.
- Candado de 16.

| Estado | Relleno | Texto | Ícono | Sombra |
|---|---|---|---|---|
| Activo | gradiente `accion-nav` | `$texto/inverso` | `texto/inverso` | `Sombra/Botón primario` |
| Normal | transparente | `$sidebar/texto` | `sidebar/icono` | — |

**Regla (rev. 1.1):** Productos, Inventario, **Caja** y Reportes llevan `Requiere PIN = true`. Nueva Venta es el único módulo sin candado. El candado es informativo: el servidor valida el PIN.

## 5. Sidebar — `COMPONENT_SET` `6:540`

**API:** `Activo`: Nueva Venta | Productos | Inventario | Caja | Reportes (el Panel Principal se eliminó en la rev. 1.1).

**Comportamiento (rev. 1.1):** **oculto por defecto.** Lo abre el Botón de ícono «Menú» de la Barra superior y se muestra como capa sobre `superficie/velo-oscuro`. Se cierra con «Cerrar menú», tocando fuera o al elegir un módulo.

**Contenedor:** 270 × 900, `V`, pad 30/22/140/22, relleno `$sidebar/fondo`.

**Anatomía, de arriba abajo:**
1. **Ondas decorativas.** Frame de 270 × 320 en y 470, con tres vectores de gradiente `onda-1..3`.
2. **Logotipo.** `H`, gap 14: cuadro «Marca» de 50 × 50 (radio 14, gradiente `logotipo`, `Sombra/Botón primario`, ícono `Tienda` de 28 blanco) y nombre «PuntoVenta» (`Título/H2`, `sidebar/texto`) con «El Pardo · SGFT» (Medium 13, `sidebar/icono`).
3. **Cerrar menú.** Botón de ícono Oscuro Compacto (40) con `Cerrar`, en (208, 35).
4. **Navegación.** `V`, gap 4, pad superior 34, con 5 elementos de navegación de 226 × 52.
5. **Divisor.** Pad vertical de 14 y línea de 1 px `$sidebar/texto` con opacidad baja.
6. **Sincronizar.** Elemento de navegación seguido de «Estado de sincronización»: punto `$indicador/en-linea` de 8 px y «En línea · N pendientes» en `Etiqueta/Chip` `$sidebar/icono`, con pad izquierdo 56.
7. **Espaciador** flexible.
8. **Activar modo admin.** Botón Oscuro FILL × 48 con ícono `Escudo`.
9. **Usuario.** 270 × 120 en y 780, relleno `$sidebar/pie` y borde superior: avatar de 44 (`$marca/durazno-200`, iniciales en `marca/primario-oscuro`), nombre (SemiBold 13) y correo (Medium 12), e ícono `Salir` de 22.

**Estados pendientes de diseñar:** sin conexión (módulos no disponibles, «Sin conexión · N pendientes») y modo admin activo.

## 6. Barra superior — `COMPONENT` `7:412`

**Contenedor (rev. 1.1):** 1600 × 112, `H`, SPACE_BETWEEN, pad lateral 28, a todo lo ancho. Sin relleno.

**Anatomía:**
- **Menú y marca.** `H`, gap 16:
  - Botón de ícono **Neutro Normal** (48, radio 14) con `Menú` (hamburguesa). Abre el Sidebar.
  - Logotipo: cuadro de 44 (radio 12, gradiente `logotipo`, `Tienda` de 24) y «PuntoVenta» (SemiBold 18) con «El Pardo · SGFT» (`Cuerpo/Nota` secundario), gap 12.
- **Buscador.** 600 × 56, `H`, gap 12, pad lateral 20, radio 16, `$superficie/campo`, borde `$borde/sutil`, `Sombra/Tarjeta`. Ícono `Buscar` de 20 y placeholder en `Cuerpo/Pequeño` secundario, terminado en «(F2)...».
- **Acciones.** `H`, gap 26:
  - **Estado de caja** (§15), instancia expuesta.
  - **Total sesión:** alto 54, pad 18, radio 16, `$marca/durazno-100`; «Total Sesión:» en `Cuerpo/Pequeño` secundario y monto en `Título/H3` `$marca/primario-oscuro`.
  - **Notificaciones:** `Campana` de 32 con indicador `$marca/primario`.
  - **Perfil:** círculo de 54, relleno `#F2E6DA`, `Usuario` de 24.

## 7. Encabezado de tarjeta — `COMPONENT` `7:431`

**API:**
- `Título` (TEXT)
- `Icono` (INSTANCE_SWAP)

**Anatomía:**
- `H`, gap 20, alineado al centro.
- Contenedor del ícono de 56 × 56, radio 16, relleno `$marca/durazno-200`, con ícono de 28 en `marca/primario-oscuro`.
- Título en `Título/H2` `$texto/primario`.

**Versión compacta** (tarjetas de 200–580 px de alto): gap 14 y título a 19 px (se sobrescribe; ver auditoría).

**Regla:** toda tarjeta de pantalla empieza con este encabezado. Si la tarjeta necesita una acción o una insignia, van a la derecha en una fila SPACE_BETWEEN.

## 8. Tarjeta de producto · Venta — `COMPONENT_SET` `2044:1956`

La versión anterior (200 × 108, `7:439`) quedó como «(anterior)» y no se usa.

**API:**
- `Estado`: Normal | En ticket | Presionada
- TEXT: `Nombre`, `Precio`, `Categoría`, `Emoji`, `Cantidad`

**Contenedor:** 352 × 176 (344 en la rejilla), `H`, gap 16, pad 20, radio 20, `Sombra/Tarjeta`.

**Anatomía:**
- **Miniatura.** 120 × 120, radio 18, gradiente `miniatura`, emoji de 64.
- **Datos.** `V`, gap 6, FILL:
  - `Categoría` en `Etiqueta/Mayúsculas` `$texto/secundario`;
  - `Nombre` en `Título/H2 compacto` `$texto/primario`, máximo 2 líneas;
  - `Precio` en `Título/H2` `$marca/primario-oscuro`.
- **Cantidad en ticket** (solo En ticket): círculo de 36, gradiente `accion`, `Sombra/Botón primario`, número SemiBold 16 blanco. En código va sobre la **esquina inferior derecha de la miniatura** (DEC-33; en Figma está en la esquina superior derecha de la tarjeta), para dejar todo el ancho al nombre.

| Estado | Relleno | Borde | Sombra |
|---|---|---|---|
| Normal | `$superficie/tarjeta` | `$borde/sutil` 1 | `Sombra/Tarjeta` |
| En ticket | `$superficie/tarjeta` | `$marca/primario` 2 | `Sombra/Tarjeta` |
| Presionada | `$marca/durazno-100` | `$marca/primario` 2 | — |

**Interacción (rev. 1.1):**
- **Toque = +1** al ticket. La tarjeta completa es el objetivo táctil.
- **Mantener presionado 0.5 s** abre el Menú de cantidad (§16). Mientras se mantiene, el estado es Presionada.
- `En ticket` y `Cantidad` los decide el servidor (o `calcularTotal()` sin red); la plantilla solo los representa.

## 9. Línea de ticket — `COMPONENT` `7:446`

**Contenedor (rev. 1.1):** 372 × 60 (390 en el ticket), `H`, gap 12, sin relleno. **Sin pasos +/−.**

**Anatomía:**
- **Miniatura.** 48 × 48, radio 14, gradiente `miniatura`, emoji de 26.
- **Datos.** `V`, gap 1, FILL: `Nombre` en `Cuerpo/Medio` y `Modificadores` en `Cuerpo/Descripción` secundario, ambos en 1 línea con puntos suspensivos.
- **Cantidad.** En Figma, píldora «×N». En código (DEC-33), círculo de 20 sobre la esquina inferior derecha de la miniatura, como en la tarjeta de venta; la columna queda libre para el nombre y los lectores de pantalla oyen «N unidades».
- **Importe.** `Número/Precio`, 76 de ancho, alineado a la derecha.
- **Quitar.** Botón de ícono **Peligro Compacto** (40) con `Menos`: resta 1 y elimina el renglón al llegar a 0. Lleva `aria-label` («Quitar uno de <nombre>»).

**Reglas de contenido:**
- **Modificadores:** separados con « · » (por ejemplo «Sin cebolla · Extra queso»); el texto que no cabe se trunca.
- **Recargos:** entre paréntesis, «(+$15)».
- **Importe:** cantidad × precio más recargos. Lo calcula el servidor; la plantilla solo lo muestra.

## 10. Tarjeta de producto · Catálogo — `COMPONENT` `2003:425`

**API** (TEXT):
- `Nombre`
- `Descripción`
- `Precio`
- `Categoría`
- `Emoji`

La insignia interna «Disponibilidad» se cambia de variante en cada instancia.

**Contenedor:**
- Medidas: 238 × 322, `V`, gap 0, radio 20, con recorte.
- Superficie: `$superficie/tarjeta`, borde `$borde/sutil`, `Sombra/Tarjeta`.

**Anatomía:**
- **Imagen.** 238 × 120, gradiente `imagen-catalogo`, emoji de 60 centrado.
  - Encima va la píldora «Categoría», en posición absoluta en (12, 12): pad 4/10, radio 8, fondo blanco al 85 %, texto Medium 12 `$marca/primario-oscuro`.
- **Contenido.** `V`, gap 8, pad 14/16/16/16, ocupa el resto:
  - `Nombre` en `Título/H3`, 1 línea;
  - `Descripción` en Regular 13 `$texto/secundario`, 2 líneas;
  - fila «Precio y estado» SPACE_BETWEEN: `Precio` en `Título/H2` `$marca/primario-oscuro` e Insignia `Disponibilidad`;
  - fila «Acciones», gap 10: `Receta` (Secundario, 40 de alto, FILL) y `Editar` (Primario con `Lápiz` de 16, 40 de alto, FILL).

**Estados de disponibilidad:**

| Estado | Insignia |
|---|---|
| Disponible | Éxito |
| Pocas porciones | Alerta |
| Agotado (propuesto) | Peligro |

**Regla:** la edición requiere PIN de administrador. La tarjeta «Agregar platillo» es un tile punteado de 238 × 322, no un componente.

## 11. Tarjeta de insumo — `COMPONENT` `2003:453`

**API** (TEXT):
- `Nombre`
- `Existencia`
- `Emoji`

En cada instancia se cambia la insignia «Estado» (variante y texto) y el relleno del rectángulo «Nivel».

**Contenedor:**
- Medidas: 425 × 118 en el componente; las instancias miden 425 × 124.
- Layout: `H`, gap 16, pad lateral 18, radio 18.
- Superficie: `$superficie/tarjeta`, borde `$borde/sutil`, `Sombra/Tarjeta`.

**Anatomía:**
- **Miniatura.** 58 × 58, radio 16, emoji de 30.
- **Datos.** `V`, gap 6, ocupa el resto:
  - «Encabezado» SPACE_BETWEEN: `Nombre` en `Cuerpo/Medio` e Insignia «Estado» de 26 de alto;
  - `Existencia` en Regular 13 secundario, con el formato «Existencia: 8.5 kg  ·  Mínimo: 3 kg» (dos espacios a cada lado del punto medio);
  - «Nivel»: rectángulo FILL × 8, radio 4, relleno de barra con corte duro.

| Estado | Insignia | Color de nivel | Extra |
|---|---|---|---|
| Normal | Éxito «Normal» | `#5FAE6B` | — |
| Bajo | Alerta «Bajo» | `#E0A030` | — |
| Crítico | Peligro «Crítico» | `#D2472C` | Borde de tarjeta `$estado/peligro` al 45 %, 1.5 px |

**Regla:** el estado lo decide el servidor, comparando la existencia contra el mínimo. Umbral propuesto: menos de 50 % del mínimo es crítico. La interfaz solo lo representa.

## 12. Fotos e íconos

- `Foto/Burrito de asada` (`3:2`, 280 × 207, radio 16) y `Foto/Burrito de pollo` (`3:3`, 96 × 96, radio 16). Eran imágenes de la referencia para el Panel Principal, que se eliminó en la rev. 1.1: hoy no se usan.
- 39 componentes `Icono/*` de 24 × 24. La lista y los tamaños están en `fundamentos.md` §7.

## 13. Patrones de pantalla (frames, no componentes)

Se construyen con los helpers de `assets/figma/helpers-plugin-api.js` y todavía no son componentes (ver auditoría §4).

| Patrón | Especificación |
|---|---|
| **Tarjeta de pantalla** (`card`) | `V`, radio 22, `$superficie/tarjeta`, borde `$borde/sutil` 1, `Sombra/Tarjeta`, con recorte. Pad 28 y gap 20–24 (grande), pad 24 y gap 14–16 (mediana), o pad 20 × 28 en horizontal para franjas de 132 de alto. |
| **Encabezado de página** (`pageHeader`) | En x 298, y 116; ancho 1274 (848 junto a un panel lateral); alto ≈ 58. Izquierda: `Título/H1` y subtítulo `Cuerpo/Pequeño` secundario, gap 4. Derecha: acciones (Contorno) o insignia, gap 12. |
| **KPI** (`metricCard`) | Tarjeta mediana de 627 × 200: encabezado compacto, fila con valor `Display/Indicador` e insignia, y nota `Cuerpo/Pequeño` secundaria. |
| **Clave-valor** (`keyValue`) | Fila SPACE_BETWEEN: ícono de 18 opcional con etiqueta `Cuerpo/Pequeño` secundaria, y valor `Cuerpo/Pequeño Medio` o `Cuerpo/Medio`. |
| **Dona de meta** (`donut`) | 224 × 224, radio interior 0.84 (trazo ≈ 18). Pista `$marca/anillo`; arco con gradiente `dato` desde −90° en sentido horario; remates circulares del grosor del trazo. En el centro, % Bold 40 y «de meta» en `Etiqueta/Mayúsculas`. |
| **Barra de meta** (`progress`) | 318 × 14, radio 7, pista `$superficie/pista`, avance con gradiente `accion`. |
| **Gráfica de barras** (`barChart`) | Eje de 56 px con 3 guías de 1 px `$borde/sutil` y etiquetas Regular 12 terciarias; fila de etiquetas de 22 px. Barras de ancho mínimo entre 44 y 62 % del espacio, radio superior 8. La barra pico usa el gradiente `dato` vertical; las demás, `$marca/durazno-200`. Sobre el pico va una etiqueta de 70 × 24, radio 8, fondo `texto/primario`, texto blanco 12. |
| **Ranking** | Círculo de 26: gradiente `accion` y texto blanco para las posiciones 1–3; `durazno-100` y texto `primario-oscuro` de la 4 en adelante. Nombre con FILL, unidades en secundario y barra de 6 px (corte duro) debajo, gap 8. Filas separadas 18. |
| **Alerta de stock** (`alertItem`) | Fila de radio 16, pad 12/14, gap 12, fondo `estado/*-fondo`. Miniatura de 44, nombre `Cuerpo/Pequeño Medio`, estado SemiBold 12 del color del estado y detalle Regular 12 secundario. |
| **Tile punteado** (`dashedTile`) | Fondo `$marca/durazno-100` al 45 %, borde `$marca/primario` al 55 %, 1.5 px, guiones 8/6, radio 20. Lleva círculo «+» (64 o 32) y texto `marca/primario-oscuro`; si la acción está protegida, «Requiere PIN» con candado de 14. |
| **Campo de fecha** | 300 × 52, radio 14, `$superficie/campo`, borde `$borde/sutil`. Ícono `Calendario` de 20, texto `Cuerpo/Base` con FILL y `Chevron abajo` de 18. |
| **Selector segmentado** (método de pago) | Dos botones FILL con gap 10: el seleccionado es Secundario con borde naranja; el otro, Contorno. |

## 14. Botón de ícono — `COMPONENT_SET` `2043:1836` (rev. 1.1)

**API:** `Variante`: Neutro | Oscuro | Primario | Peligro · `Tamaño`: Normal | Compacto · `Icono` (INSTANCE_SWAP).

| Tamaño | Medida | Radio | Ícono |
|---|---|---|---|
| Normal | 48 × 48 | `radio/md` 14 | 24 |
| Compacto | 40 × 40 | `radio/chip` 12 | 20 |

| Variante | Relleno | Borde | Ícono | Sombra | Uso |
|---|---|---|---|---|---|
| Neutro | `$superficie/tarjeta` | `$borde/sutil` 1 | `texto/primario` | — | Menú (hamburguesa), cerrar diálogo |
| Oscuro | `$boton-oscuro/fondo` | — | `sidebar/texto` | — | Cerrar el menú lateral |
| Primario | gradiente `accion` | — | `texto/inverso` | `Sombra/Botón primario` | Aumentar cantidad |
| Peligro | `$estado/peligro-solido` | — | `texto/inverso` | — | Quitar o disminuir; **único botón rojo del sistema** |

**Regla:** siempre lleva nombre accesible en código (`aria-label`).

## 15. Estado de caja — `COMPONENT_SET` `2043:1845` (rev. 1.1)

**API:** `Estado`: Abierta | Cerrada. Va en la Barra superior, a la izquierda de Total sesión, **en todas las pantallas**.

**Contenedor:** alto 54, pad lateral 18, gap 10, radio 16 (`radio/campo`). Texto en `Cuerpo/Pequeño Medio` **`$texto/primario`** (contraste AA; el color lo dan el fondo y el indicador). En código dice solo **«Caja»** (DEC-33); «abierta» o «cerrada» quedan para lectores de pantalla.

| Estado | Fondo | Indicador |
|---|---|---|
| Abierta | `$estado/exito-fondo` | Punto de 10 `$indicador/en-linea` |
| Cerrada | `$estado/peligro-fondo` | `Candado` de 18 `$estado/peligro` |

El estado lo decide el servidor (o el turno guardado en el dispositivo sin red, regla 12).

## 16. Menú de cantidad — `COMPONENT` `2044:1976` (rev. 1.1)

Aparece al mantener presionado 0.5 s un producto en Nueva Venta. En código es un **modal de toda la pantalla** sobre `superficie/velo-oscuro` (DEC-33; en Figma es un popover a 12 px de la tarjeta). Se cierra con «Listo», tocando el velo o con Escape.

**Contenedor:** 300 de ancho, `V`, gap 16, pad 20, radio 20, `$superficie/tarjeta`, borde `$borde/sutil`, `Sombra/Tarjeta`.

**Anatomía:**
1. **Producto.** `H`, gap 12: miniatura de 48 (radio 14, emoji 26), nombre en `Título/H3` (1 línea) y «Cantidad en el ticket» en `Cuerpo/Nota` secundario.
2. **Ajuste.** SPACE_BETWEEN: «Disminuir» (Botón de ícono Peligro Normal con `Menos`), cantidad en `Display/KPI` y «Aumentar» (Botón de ícono Primario Normal con `Más`).
3. Nota centrada «Toca el producto otra vez para sumar 1» en `Cuerpo/Nota` secundario.
4. «Listo»: botón Secundario FILL × 48.

## 17. Aviso de stock — `COMPONENT` `2044:2084` (rev. 1.1)

Aviso en el encabezado de Nueva Venta. **Aparece solo si el servidor reporta insumos Bajo o Crítico** (regla 3: es visual y no bloquea la venta). Al tocarlo lleva a Inventario, que pide PIN.

**Contenedor:** `H`, gap 12, pad 10/16/10/10, radio 16, `$superficie/tarjeta`, borde **`$estado/alerta` 1.5 px**, `Sombra/Tarjeta`.

**Anatomía:** contenedor de ícono de 40 (radio 12, `$estado/alerta-fondo`) con `Alerta` de 22 en `estado/alerta`; «Alerta stock» en `Cuerpo/Medio` primario y el detalle («3 insumos bajos · Ver inventario») en `Cuerpo/Descripción` secundario; `Chevron derecha` de 20.

**Sin red (DEC-29):** usa la copia local de existencias, que cada venta descuenta. No se rotula como «teórica»; Inventario muestra «Última sincronización: <fecha y hora>».

## 18. Aviso de caja cerrada — `COMPONENT` `2044:2095` (rev. 1.1)

Bloquea Nueva Venta cuando no hay turno abierto (regla 12). Se centra sobre el contenido, que queda deshabilitado (opacidad 35 %, sin interacción); el menú y la barra superior siguen activos.

**Contenedor:** 520 de ancho, `V`, gap 16, pad 40, centrado, radio 24 (`radio/xl`), `$superficie/tarjeta`, borde `$borde/sutil`, `Sombra/Tarjeta`.

**Anatomía:** cuadro de 72 (radio 20, `$marca/durazno-200`) con `Candado` de 36 `marca/primario-oscuro`; título «La caja está cerrada» en `Título/H1`; mensaje en `Cuerpo/Grande` secundario; botón Primario de 56 «Abrir caja» con `Candado`; nota «Requiere PIN de administrador» en `Cuerpo/Nota` secundario.

## 19. Diálogo · Abrir caja — `COMPONENT` `2044:2111` (rev. 1.1)

Se abre desde el Aviso de caja cerrada o desde Caja, centrado sobre `superficie/velo-oscuro`. **Solo el Administrador abre la caja** (DEC-27).

**Contenedor:** 480 de ancho, `V`, gap 20, pad 32, radio 24, `$superficie/tarjeta`, borde `$borde/sutil`, `Sombra/Tarjeta`.

**Anatomía:**
1. **Encabezado.** SPACE_BETWEEN: ícono `Cartera` de 28 en cuadro de 56 (radio 16, `$marca/durazno-200`), «Abrir caja» en `Título/H2` y «Turno matutino · 30/09/2026» en `Cuerpo/Pequeño` secundario; a la derecha, Botón de ícono Neutro Compacto con `Cerrar`.
2. **PIN de administrador.** Etiqueta en `Cuerpo/Pequeño Medio`; **6 casillas** (DEC-28; Figma aún dibuja 4) FILL × 56 (radio 14, `$superficie/campo`, borde `$borde/sutil`) con «•» en `Display/KPI`; la casilla activa lleva borde 2 `$marca/primario-oscuro` y `Foco/Anillo`. Nota en `Cuerpo/Nota` secundario.
3. **Fondo inicial en efectivo.** Etiqueta y campo de 52 (radio 14, pad 16, gap 12) con `Billete` de 20 y el monto en `Cuerpo/Base`.
4. **Acciones.** `H`, gap 12: «Cancelar» (Contorno, FILL) y «Abrir caja» (Primario con `Candado`, FILL).

**PIN sin red (DEC-28):** la nota de Figma dice «El PIN se valida en el servidor»; en código la nota es «Si no hay conexión, el PIN se valida en este dispositivo». La verificación local (WebCrypto contra el verificador en Dexie) vive en `static/pos/` y se programa en pareja en la Fase 6.


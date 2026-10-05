# Auditoría del sistema y plan de corrección

> **Revisión 1.1 (03/10/2026):** esta auditoría describe la rev. 1.0. La 1.1 resolvió H2 (code syntax en todas las variables), creó los 8 estilos de texto propuestos (H6, parte de F2), convirtió en variables `#6BC47A` y `#FFFFFF` al 7 % (H7) y agregó `description` a los componentes nuevos (H10). Los conteos de abajo no se volvieron a medir.

La auditoría se hizo el 30/09/2026. Leí con la Plugin API las 6 pantallas, los 13 componentes y conjuntos, las 35 variables y los 13 estilos. Los criterios son los de las skills `figma-generate-library` y `figma-use`: los tokens van antes que los componentes, con alcances precisos, *code syntax* y sin valores escritos a mano. El sistema funciona y es consistente a la vista. Lo que sigue es deuda técnica, ordenada por prioridad.

## Contenido
1. Resumen de hallazgos
2. Accesibilidad (contraste WCAG 2.1)
3. Variables: alcances, *code syntax* y arquitectura
4. Texto sin estilo y valores escritos a mano
5. Cómo proponer un token o estilo nuevo
6. Plan de corrección por fases
7. Checklist de conformidad (revisión de cualquier pantalla nueva)

---

## 1. Resumen de hallazgos

| # | Hallazgo | Medida | Prioridad |
|---|---|---|---|
| H1 | Contraste insuficiente en 10 de 17 combinaciones de texto | Ratios de 2.45 a 4.35 frente al mínimo de 4.5 (o 3 en texto grande) | **Alta** |
| H2 | ~~Ninguna variable tiene *code syntax*~~ | **Resuelto en la rev. 1.1:** las variables exponen `var(--sgft-…)`, igual que `tokens.css` | — |
| H3 | Alcances demasiado amplios | 21 de 26 colores permiten `FRAME_FILL`, `SHAPE_FILL`, `TEXT_FILL` y `STROKE_COLOR` a la vez | Media |
| H4 | Variables usadas fuera de su alcance | `borde/sutil` como relleno de divisores; `texto/primario` como fondo de la etiqueta de pico | Media |
| H5 | Radios y espacios sin vincular a «SGFT · Medidas» | Ningún nodo vinculado. La escala real (8 a 22) no coincide con los tokens (10/14/20) | Media |
| H6 | Textos con estilo desvinculado (en las pantallas) | 22 combinaciones de tamaño y peso; 206 nodos, de los que ≈ 50 son emoji | Media |
| H7 | Rellenos sólidos sin variable | Ver la lista debajo de esta tabla | Baja |
| H8 | Gradientes sin token | 9 gradientes documentados; Figma no permite variables de gradiente | Baja (documentado) |
| H9 | Patrones repetidos que no son componentes | Tarjeta, encabezado de página, KPI, alerta, clave-valor, tile punteado, campo de fecha | Media |
| H10 | Faltan descripciones | «Chip de categoría» y «Encabezado de tarjeta» no tienen `description` | Baja |

Rellenos sólidos sin variable (H7), en la forma «color: repeticiones», contadas sobre las 6 pantallas:
- `#6BC47A`: 6
- `#FFFFFF` al 7 %: 6
- `#F2E6DA`: 6
- `#FFFFFF` al 85 %: 9
- `#5FAE6B`: 1
- remates de la dona: 2

A esto se suman los niveles de insumo como gradientes.

## 2. Accesibilidad (contraste WCAG 2.1)

Para recalcular todos los pares, corre `python scripts/tokens.py contraste`. El umbral es 4.5:1 para texto normal y 3:1 para texto grande (≥ 24 px, o ≥ 18.66 px en negrita).

| Combinación | Ratio | Dónde aparece | Propuesta |
|---|---|---|---|
| Blanco sobre gradiente `accion` | 2.45–3.29 | Botón Primario, chip Activo, nav Activo | Opción A: gradiente accesible `#C0561B → #A8460F` (4.58–5.92), que cambia el tono de marca. Opción B: mantener el gradiente y subir la etiqueta a SemiBold 19 o más (texto grande, 3:1). Aun así el extremo claro falla, así que habría que oscurecer solo el inicio a `#E36A22`. **Decisión del equipo.** |
| `primario` sobre tarjeta | 2.85 (texto grande) | Montos Display naranja: $4,850.00, total del ticket | Usar `marca/primario-oscuro` (3.35) para montos de 24 px o más. El cambio de tono es mínimo. |
| `primario-oscuro` sobre `durazno-100` | 2.92 | Texto del botón Secundario, Insignia Marca, monto del Total sesión | Nuevo `marca/texto` `#AC4B16` (4.6). |
| `primario-oscuro` sobre tarjeta | 3.35 | Precios de venta y catálogo | `marca/texto` `#AC4B16`, o subir el precio a 18.66 px o más en negrita. |
| `texto/terciario` sobre tarjeta | 2.59 | Categoría en mayúsculas, ejes, «Método de pago» | Cambiar el valor a `#7B7069` (4.56). Mantiene la jerarquía frente a `secundario` `#7A695D`, así que conviene fusionarlos o dejar `terciario` solo para decoración. |
| `estado/alerta` sobre `alerta-fondo` | 3.22 | Insignia Alerta, alertas de stock Bajo | Nuevo `estado/alerta-texto` `#966319` (4.53). |
| `estado/exito` sobre `exito-fondo` | 4.30 | Insignia Éxito | Ajustar a `#2E7938` (4.53) o aclarar el fondo. |
| `estado/peligro` sobre `peligro-fondo` | 4.35 | Insignia Peligro | Ajustar a `#BC3921` (4.58). |
| `texto/secundario` sobre `durazno-100` | 4.33 | «Total Sesión:», sugerencia de compra | `#76665A` en ese contexto, o `texto/primario`. |

Otros criterios:
- **Objetivos táctiles.** Botones de 48 o más, nav de 52, tarjetas de venta de 200 × 122: ✔. Los botones Restar y Sumar miden 26 × 26: ✘, lo recomendado es 44. Propuesta: agrandar el área táctil a 40 o 44 con un marco transparente que conserve el cuadro visual de 26.
- **El color no es el único indicador.** El semáforo de inventario siempre lleva la insignia con texto (Normal, Bajo, Crítico): ✔. El método de pago seleccionado solo se distingue por el borde naranja: ⚠. Conviene agregar un ícono `Check` o texto.
- **Foco visible.** No está diseñado. Propuesta: anillo de 2 px `marca/primario-oscuro` con 2 px de separación sobre `superficie/fondo`.

## 3. Variables: alcances, *code syntax* y arquitectura

**Arquitectura.** Con 35 variables, el patrón de una sola colección por tipo, sin primitivos, es aceptable. `figma-generate-library` recomienda una colección simple por debajo de 50 tokens. Solo conviene agregar una capa de primitivos con alias si se añade un modo Oscuro o un modo de alto contraste.

**Alcances recomendados.** Sustituyen a los actuales.

| Grupo | Alcances |
|---|---|
| `superficie/*`, `sidebar/fondo`, `sidebar/pie`, `marca/durazno-*`, `marca/anillo`, `estado/*-fondo` | `FRAME_FILL`, `SHAPE_FILL` |
| `texto/*`, `estado/exito`, `estado/alerta`, `estado/peligro`, `sidebar/texto`, `sidebar/icono` | `TEXT_FILL`, más `STROKE_COLOR` en los que colorean íconos |
| `marca/primario`, `marca/primario-oscuro`, `marca/primario-claro` | `TEXT_FILL`, `STROKE_COLOR`, `SHAPE_FILL` |
| `borde/sutil` | `STROKE_COLOR` y `SHAPE_FILL` (para los divisores) |
| `radio/*` | `CORNER_RADIUS` (ya correcto) |
| `espacio/*` | `GAP` y `WIDTH_HEIGHT` (ya correcto); agregar la escala real 2, 4, 6, 10, 14, 18, 20, 28 solo si se van a vincular |

Para el fondo de la etiqueta de pico, crea `superficie/oscura` (`#2B1A10`, `FRAME_FILL`) en lugar de usar `texto/primario`.

**Code syntax (WEB).**
- Formato: `var(--sgft-color-<grupo>-<nombre>)`, por ejemplo `var(--sgft-color-marca-primario)`.
- Medidas: `var(--sgft-radio-md)` y `var(--sgft-espacio-lg)`.
- Son exactamente los nombres que genera `python scripts/tokens.py css`.
- Aplicación con la API: `v.setVariableCodeSyntax('WEB', 'var(--sgft-color-' + v.name.slice(6).replace('/', '-') + ')')`. Para `radio/*` y `espacio/*` usa `var(--sgft-' + name.replace('/', '-') + ')`.

## 4. Texto sin estilo y valores escritos a mano

**Causa.** Los helpers aplican un estilo y luego sobrescriben el tamaño o el peso (`txt(..., {size})`), y Figma desvincula el estilo. **Remedio:** crear los estilos que faltan y reasignarlos por tamaño y peso.

| Estilo nuevo propuesto | Definición | Reemplaza |
|---|---|---|
| `Display/Monto XXL` | Bold 52 / 120 % / −1 px | Bold 52 |
| `Display/Dona` | Bold 40 / 120 % / −0.5 px | Bold 40 |
| `Display/KPI` | Bold 32 / 120 % / −0.5 px | Bold 30 y 32 |
| `Título/H2 compacto` | SemiBold 19 / 140 % / −0.2 px | SemiBold 19 |
| `Cuerpo/Grande` | Regular 18 / 140 % | Regular 17–19, Medium 20 (Panel Principal) |
| `Número/Precio` | SemiBold 16 / 140 % | SemiBold 16 |
| `Número/Importe` | SemiBold 14 / 140 % | SemiBold 14 |
| `Cuerpo/Descripción` | Regular 13 / 140 % | Regular 13 |
| `Cuerpo/Nota` | Regular 12 / 140 % | Regular 12 |
| `Etiqueta/Mini` | SemiBold 12 / 140 % | Medium y SemiBold 12, SemiBold 13 |
| — (exentos) | Emoji de 18 a 60 | Los emoji no llevan estilo |

## 5. Cómo proponer un token o estilo nuevo

1. Antes de crear nada, busca: `python scripts/tokens.py buscar "#RRGGBB"`. Si la distancia es menor que 12, usa el token existente.
2. Nombra según la función, no el aspecto: `estado/alerta-texto`, no `marron-2`. Respeta los grupos `marca`, `superficie`, `borde`, `texto`, `estado` y `sidebar`.
3. Agrégalo en `assets/tokens.json` con valor, alcances y uso. Corre `tokens.py verificar` y `tokens.py css`.
4. En Figma, créalo en la colección que le corresponde, con los alcances del paso 2 y *code syntax* WEB. Si es texto, crea el estilo de texto.
5. Regístralo en `fundamentos.md` y avisa al integrador, que ratifica los cambios del sistema.

## 6. Plan de corrección por fases

Cada fase es una rama y un PR independientes. En Figma, cada fase se valida con `get_screenshot` de las 6 pantallas.

| Fase | Qué | Riesgo | Llamadas `use_figma` estimadas |
|---|---|---|---|
| F1 | *Code syntax* en las 35 variables y alcances según §3 | Nulo (no cambia lo visual) | 1–2 |
| F2 | Estilos de texto de §4 y reasignación de los ≈ 155 textos desvinculados (sin contar emoji) | Bajo | 2–3 |
| F3 | Variables `nivel/*`, `indicador/en-linea`, `superficie/oscura`, `boton-oscuro/*` y revinculación | Bajo | 2 |
| F4 | Decisión de accesibilidad (opción A o B del §2) y aplicación de `marca/texto`, `texto/terciario` y estados | Medio (visual) | 3–4 |
| F5 | Convertir en componentes los patrones del H9: Tarjeta, Encabezado de página, KPI, Alerta de stock, Fila clave-valor, Tile punteado, Campo de fecha | Medio | 6–8 |
| F6 | Vincular radios y espacios a «SGFT · Medidas» | Bajo | 2–3 |

## 7. Checklist de conformidad (revisión de cualquier pantalla nueva)

Pasa esta lista antes de dar por terminada una pantalla o componente. Si falla una sola, corrígela: no la dejes como pendiente.

- [ ] El frame mide 1600 × 900, tiene fondo `$superficie/fondo`, la instancia de `Sidebar` con la variante correcta y la `Barra superior` con un placeholder propio.
- [ ] Todo el contenido está dentro de x 298–1572 y y 116–872.
- [ ] Hay un encabezado de página (H1 más subtítulo) o, en el Panel Principal, tarjetas desde y 116.
- [ ] Cada tarjeta usa el patrón de tarjeta (radio 22, borde, `Sombra/Tarjeta`) y empieza con `Encabezado de tarjeta`.
- [ ] Todo relleno y borde está vinculado a una variable, salvo los gradientes y los valores documentados en `fundamentos.md` §2 y §3.
- [ ] Todo texto tiene estilo de texto, salvo los emoji.
- [ ] Hay una sola acción Primaria.
- [ ] El naranja solo aparece en la acción principal, el dato protagonista y la navegación activa.
- [ ] Los datos cumplen el formato del §4 de `pantallas-y-patrones.md` y cuadran con las demás pantallas.
- [ ] Los módulos y acciones que piden PIN muestran el candado.
- [ ] Se crearon las zonas de navegación y se actualizó el prototipo.
- [ ] Revisaste la pantalla con `get_screenshot`: sin texto recortado, sin solapes y con los emoji visibles.
- [ ] `python scripts/tokens.py contraste` no muestra pares nuevos por debajo del mínimo.

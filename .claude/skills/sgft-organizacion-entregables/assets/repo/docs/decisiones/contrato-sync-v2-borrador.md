# Contrato de `POST /pos/sync/` — versión 2 (BORRADOR)

**Estado:** propuesta del 3 de octubre de 2026, **sin aprobar**. Cambia la forma del lote, así que requiere a Jesús Hernández, Jared Beltrán y Alejandro Tarín (`CLAUDE.md` §5-bis). Mientras no se apruebe, rige `contrato-sync-pdv.md` (v1).
**Origen:** DEC-29: Productos e Inventario también funcionan sin red, con el PIN de Administrador (DEC-28), y lo que no se pueda aplicar al sincronizar va a cuarentena (regla 9).
**Paquetes WBS:** 3.2.1, 3.2.2, 3.2.3, 3.2.5, 3.2.7, 3.4.3, 3.4.6, 3.4.9.

## 1. Qué cambia respecto de v1

- `version_contrato` pasa a `2`. El servidor sigue aceptando lotes v1 mientras haya dispositivos con la versión anterior.
- El campo `tipo` admite, además de `apertura_turno` y `venta`:

| `tipo` | Qué registra | Servicio que lo aplica (propuesto) |
|---|---|---|
| `platillo` | Alta o edición de un platillo: nombre, categoría, `precio_centavos`, activo | `catalog` (Diego) |
| `insumo` | Alta o edición de un insumo: nombre, unidad de medida, `min_stock` | `catalog` (Diego) |
| `receta` | Receta completa de un platillo: `lineas` de `{insumo_id, cantidad, unidad}`; reemplaza la anterior | `catalog` (Diego) |
| `compra` | Entrada de insumo: `insumo_id`, `cantidad`, `unidad` | `register_purchase()` |
| `merma` | Salida de insumo: `insumo_id`, `cantidad`, `unidad`, `motivo` | `register_waste()` |
| `cierre_turno` | Cierre del turno sin red (DEC-30): `turno_uuid`, `efectivo_final_centavos` | `close_session()` |

- Todas las operaciones nuevas llevan `uuid`, `marca_tiempo_dispositivo` y `usuario_id` (el Administrador cuyo PIN se validó). Las altas usan su `uuid` como referencia hasta que el servidor asigna el id; las ediciones llevan además `version_base`: la versión del registro que el dispositivo tenía al editar.

## 2. Procesamiento propuesto

1. **Orden.** Por `marca_tiempo_dispositivo`, en una sola secuencia para todos los tipos. Hay un solo dispositivo (§5-bis), así que su reloj da un orden total: una venta hecha antes de cambiar una receta se descuenta con la receta anterior, y una hecha después, con la nueva. **Esto sustituye el paso 2 de v1** («primero aperturas, luego ventas»), que se conserva para lotes v1.
2. **Autorización.** Los tipos nuevos y `apertura_turno` exigen que `usuario_id` sea un Administrador activo; si no, cuarentena `usuario_sin_permiso`.
3. **Conflicto de versión.** Si el registro cambió en el servidor después de `version_base` (por ejemplo, el Administrador editó el mismo platillo desde otra computadora con red), la operación va a cuarentena `conflicto_version`. El Administrador decide en la bandeja de revisión (3.4.9) cuál conservar.
4. **Referencias.** Un `insumo_id` o `platillo_id` que no existe, ni como id ni como `uuid` de un alta del mismo lote, va a cuarentena `referencia_desconocida`. Una unidad incompatible con el insumo, a `unidad_invalida`.
5. **Ventas.** Sin cambios: siguen las reglas 1, 2, 10 y 14. Si la venta se cobró con un precio editado sin red, «manda lo cobrado» (regla 14).
6. **Cierre de turno.** Por el orden cronológico, las ventas del turno anteriores al cierre ya se aplicaron cuando llega `cierre_turno`; el servidor genera el corte (regla 5) y registra la diferencia de efectivo. Si el turno no existe, ya estaba cerrado o hay ventas del turno con marca posterior al cierre, va a cuarentena (`turno_invalido`, `turno_ya_cerrado`, `venta_posterior_al_cierre`).

## 3. Decisiones de diseño (3-oct-2026, acordadas con Tarín)

### 3.1 Cuarentena: una envoltura genérica

- Los modelos de cada clase (`Sale`, `CashRegisterSession`, `Dish`, `Ingredient`, `Recipe`, compras y mermas) guardan **solo lo que se aplicó**.
- Lo que no se puede aplicar se guarda en **un solo modelo genérico** (propuesta: `QuarantinedOperation`) con: `uuid` único (regla 8), `tipo`, el **JSON original** de la operación, `motivo`, usuario, marca del dispositivo y del servidor, estado, y resolución (quién, cuándo, con qué salida). Lleva una referencia opcional al registro real cuando llega a crearse.
- Sustituye a `QuarantinedSale` y `QuarantinedCashSession` de v1, que aún no tienen migración. La idempotencia sigue garantizada por la unicidad del `uuid` en base de datos, ahora en una tabla menos. Los modelos los define Jesús.

### 3.2 Existencias sin red

- Cada venta sin red descuenta de la **copia local** de existencias recorriendo la receta y las personalizaciones (regla 2). Inventario y el Aviso de stock usan ese valor.
- La interfaz **no** dice «teórica»: muestra «Última sincronización: <fecha y hora>». Al sincronizar, el valor del servidor reemplaza la copia local (el servidor descuenta de verdad, regla 1).
- El descuento local debe dar lo mismo que `deduct_for_sale()`: **prueba de paridad** con un fixture compartido, como la de precios (`node --test` y `django.test`).

### 3.3 Salidas de la bandeja de revisión (3.4.9)

| Motivo | Salidas |
|---|---|
| `conflicto_version` (platillo, insumo o receta editados en ambos lados) | Conservar la versión del dispositivo · conservar la del servidor |
| `referencia_desconocida` (compra o merma de un insumo inexistente) | Asignarla a un insumo existente · descartar |
| `unidad_invalida` | Corregir cantidad y unidad, y aplicar · descartar |
| `usuario_sin_permiso` | Aplicar como Administrador (queda su nombre en el registro) · descartar |
| `turno_ya_cerrado` · `venta_posterior_al_cierre` | Reabrir el corte e incluir la venta · registrar la venta en el turno siguiente · descartar |
| Ventas y aperturas | Las tres salidas de la regla 9, sin cambios |

## 4. Pruebas mínimas que se derivarían

- una edición de precio sin red seguida de una venta: la venta se registra con lo cobrado y, si difiere del catálogo, queda para revisión;
- una receta editada sin red entre dos ventas: cada venta descuenta con la receta vigente a su hora;
- dos ediciones del mismo platillo (servidor y dispositivo): la del dispositivo va a `conflicto_version`;
- una compra de un insumo dado de alta en el mismo lote: se aplica;
- un lote v1 sigue funcionando igual;
- paridad del descuento: el mismo fixture da las mismas existencias en `deduct_for_sale()` y en el cliente;
- cada motivo de cuarentena ofrece exactamente las salidas de §3.3.

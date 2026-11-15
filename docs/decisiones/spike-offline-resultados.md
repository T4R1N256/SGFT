# Spike offline: resultados en el iPhone (WBS 5.4)

**Responsable:** Alejandro Tarín (con Jared Beltrán). **Dispositivo:** iPhone 17 Pro Max con iOS 26 · app instalada desde Safari en la pantalla de inicio. **Fechas de la prueba:** 13, 14 y 15 de noviembre de 2026.
**Sistema probado:** la versión desplegada en Railway (`https://sgft-production.up.railway.app`), no la rama del spike. La primera ronda fue el 13 y el 14 de noviembre; el 15, con #96 a #100 ya desplegados, se repitió la prueba 4 y se hicieron la 6, la 7 (al día siguiente) y la 12.

El spike (rama `tarin/spike-offline`, que no se fusiona) comprobó en Chromium el diseño de ADR-02: un solo camino de escritura, UUID por operación, cuarentena en lugar de rechazo y dinero en centavos. Lo que quedó pendiente fueron los riesgos propios de iOS. Esta tabla los cierra con el sistema real.

## 1. Preparación

1. En Safari, abrir el dominio y **Compartir → Agregar a pantalla de inicio**.
2. Abrir la app desde el ícono y activar el dispositivo con el PIN del Administrador.
3. Con red: abrir la caja, hacer una venta, y con el PIN abrir Productos, Inventario, Caja y Reportes una vez.

## 2. Pruebas

Estados: ✅ funciona como se espera · ⚠ funciona con un detalle (anotarlo) · ❌ no funciona.

| # | Prueba | Esperado | Resultado | Notas |
|---|---|---|---|---|
| 1 | Con la app abierta, activar el modo avión y recargar Nueva venta | Abre desde la caché y toma el modo sin red (menú, ticket, «Confirmar compra») | ✅ | |
| 2 | Cobrar 3 ventas en modo avión | «3 pendientes»; cada venta dice «guardada en el dispositivo» | ✅ | |
| 3 | Cerrar la app por completo (deslizar hacia arriba) y volver a abrirla sin red | La cola sigue con 3 pendientes | ✅ | |
| 4 | Quitar el modo avión con la app abierta | Se sincroniza sola en menos de 30 s (RNF-07), «0 pendientes», las ventas aparecen en Caja | ✅ | En la primera ronda ❌: no pasó nada hasta tocar «Sincronizar» (hallazgo 1). Repetida con #96: se envía sola. |
| 5 | Si la prueba 4 no sincronizó sola: tocar «Sincronizar» en el menú | Sincroniza (iOS no tiene Background Sync; hallazgo 5) | ✅ | Hecha en la primera ronda, cuando la 4 falló. |
| 6 | ¿La app instalada pidió activar el dispositivo aunque Safari ya tuviera sesión? | Sí: no comparten cookies (hallazgo 7); la activación se hace dentro de la app | ✅ | |
| 7 | Al día siguiente, sin red: abrir la app | La cola y el menú siguen ahí; caja cerrada → «Abrir caja» con PIN sin red | ✅ | |
| 8 | Abrir la caja sin red con el PIN y vender | El PIN se valida en el teléfono; la apertura y la venta se sincronizan al volver la red | ✅ | |
| 9 | Sin red, abrir Reportes desde el menú | Pide el PIN; con él muestra los datos de la última carga y «Sin conexión · N pendientes» | ✅ | |
| 10 | Con ventas pendientes, intentar cerrar la caja (con red, sin sincronizar) | Se niega y dice cuántas faltan (regla 5) | ⚠ | No se pudo provocar: al volver la red la cola se envía sola antes de cerrar. La negativa la cubre la E2E `test_close_is_refused_while_the_device_has_pending_sales`. |
| 11 | Tiempo de respuesta con red móvil (abrir Nueva venta, agregar un platillo) | Menos de 2 s (RNF-06) | ✅ | |
| 12 | Cinco PIN incorrectos en la activación | Se bloquea 15 minutos | ✅ | Probada en el diálogo «PIN de administrador» de Reportes: Safari ya tenía sesión y la activación redirige a Nueva venta. El contador es el mismo para la activación, los candados y Django Admin. |

## 3. Hallazgos

Lo que no salió como se esperaba, con el número de la prueba y su arreglo. Todos quedaron corregidos y desplegados antes de repetir las pruebas.

1. **Prueba 4 (#96).** Al quitar el modo avión no pasaba nada: el evento `online` de iOS llega antes de que la conexión funcione, ese único intento fallaba y nadie lo repetía. Ahora `offline.js` reintenta cada 10 s mientras haya pendientes y cada vez que la app vuelve al frente. Nueva E2E: `test_a_failed_sync_is_retried_without_touching_anything`.
2. **Sin red, pasado un minuto, la app no cargaba sus propios archivos (#98).** El service worker los guardaba al instalarse, pero ninguna ruta los leía desde #85. La página dependía de la caché HTTP, que WhiteNoise deja vencer a los 60 s. Se restauró la ruta que los sirve desde la caché. Nueva E2E: `test_the_app_files_come_from_the_worker_when_the_browser_cache_expired`.
3. **Prueba 12 de la primera ronda y uso diario (#99).** Con la caja abierta con red, en modo avión Nueva venta decía «Sin turno de caja abierto» y pedía abrirla otra vez. Abrir la caja no recargaba la página, así que el dispositivo seguía con los datos de cuando estaba cerrada. Esa segunda apertura choca con la regla 13 y va a cuarentena; fue el «bloqueo» de la primera ronda. Ahora abrir la caja recarga Nueva venta. Nueva E2E: `test_a_till_opened_with_network_stays_open_without_network`.
4. **iPhone en horizontal, sin red (#100).** Los productos quedaban apretados al lado de las categorías: las reglas del teléfono solo conocían los `id` de la venta con red. La venta sin red ahora tiene la misma estructura y clases equivalentes. Nueva E2E con el tamaño del iPhone: `test_without_network_the_landscape_phone_keeps_the_dishes_below_the_categories`.

## 4. Conclusión

Las pruebas 1 a 9 salieron ✅, igual que la 11 y la 12; la 10 queda ⚠ porque solo la cubre la prueba E2E. El modo sin conexión queda validado en el iPhone: la caché, la cola de IndexedDB, la sesión propia de la app instalada, el verificador del PIN sin red y la sincronización automática al volver la red funcionan con el sistema desplegado. Con esto se cierra el issue #28.

Para operar:
- Sincronizar antes de cada jornada: el verificador del PIN que permite abrir la caja sin red caduca a los 7 días sin sincronizar.
- Usar siempre la app instalada, no Safari: tienen sesiones y colas distintas.
- Abrir la caja una sola vez por día.

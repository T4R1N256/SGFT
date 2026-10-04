# DEC-28 — PIN de Administrador y su validación sin red

**Fecha:** 3 de octubre de 2026 · **Estado:** aprobada · **Dueños:** Alejandro Tarín (propuesta y cliente offline), Jesús Hernández (modelo), Diego Galindo (servicios de `accounts`) · **WBS:** 3.1.3, 3.4.3, 3.5.1

## Contexto

Desde la revisión 1.1 de Figma, solo el Administrador abre y cierra el turno de caja (DEC-27) y lo autoriza con un PIN. La apertura del turno funciona sin red (`CLAUDE.md` §5-bis), así que el PIN también debe poder validarse en el dispositivo cuando no hay conexión. El dispositivo es un iPhone con la PWA abierta en Safari, sin instalar.

## Decisión

1. **PIN de 6 dígitos**, propio de cada Administrador y distinto de su contraseña. En el servidor se guarda solo su hash, con el sistema de contraseñas de Django (`make_password` / `check_password`).
2. **Verificador para el dispositivo.** Con red y sesión iniciada, el dispositivo descarga un verificador por cada Administrador activo: `usuario_id`, `sal` (aleatoria, distinta del hash del servidor), `iteraciones` (600 000) y `verificador` = PBKDF2-SHA256(PIN, sal, iteraciones). El PIN nunca viaja ni se guarda en claro. Se descarga al iniciar sesión y en cada sincronización, y se guarda en Dexie.
3. **Validación.** Con red, el servidor valida el PIN. Sin red, el dispositivo deriva PBKDF2 con WebCrypto (`crypto.subtle`, del navegador; sin dependencias nuevas) y lo compara con el verificador.
4. **Autoría.** La operación `apertura_turno` lleva como `usuario_id` al Administrador cuyo PIN se validó. Al sincronizar, el servidor revalida que ese usuario exista, esté activo y sea Administrador; si no, la apertura va a cuarentena con motivo `usuario_sin_permiso` (regla 9). La forma del lote no cambia (`version_contrato` sigue en 1).
5. **Caducidad.** Un verificador que no se ha renovado en 7 días deja de aceptarse sin red. Si el PIN cambia o la cuenta se desactiva, el verificador se borra en la siguiente sincronización.
6. **Sin límite de intentos fallidos** por ahora (decisión del 3-oct-2026). Se puede agregar después sin cambiar el contrato.
7. **La PWA no se instala.** Recomendación operativa para el manual: **sincronizar antes de cada jornada**. iOS puede borrar los datos del sitio tras 7 días sin uso; sincronizar a diario renueva verificadores, catálogo y estado del turno. El cliente pide además almacenamiento persistente con `navigator.storage.persist()` cuando el navegador lo permita.

## Alternativas consideradas

- **Solo validación en el servidor** (como decía la nota del diálogo en Figma): impide abrir la caja sin red y contradice §5-bis.
- **PIN del Cajero en lugar del Administrador:** contradice DEC-27.
- **PIN de 4 dígitos** (como dibuja Figma): 10 000 combinaciones; se descartó por 6 dígitos (1 000 000).

## Riesgo aceptado

Quien extraiga los datos del navegador puede probar todos los PIN contra el verificador sin red; las iteraciones solo lo hacen más lento. El riesgo que se busca cubrir es que alguien abra la caja sin el Administrador presente, no un atacante con herramientas de desarrollo sobre el iPhone. La revalidación del rol al sincronizar y la cuarentena acotan el daño.

## Consecuencias

| Quién | Qué |
|---|---|
| Jesús | Campo del hash del PIN en el usuario (y fecha de cambio), con su migración. |
| Diego | Servicios para asignar y validar el PIN, y la vista que entrega los verificadores de los Administradores activos a una sesión iniciada. |
| Tarín + Yahir (pareja) | Tabla de verificadores en `static/pos/db.js`, validación con WebCrypto y caducidad de 7 días (Fase 6). |
| Tarín | Diálogo «Abrir caja» con **6 casillas** y nota «Si no hay conexión, el PIN se valida en este dispositivo». En Figma (si se autoriza escribir) cambiar las 4 casillas y la nota. |
| Diego | Manual de usuario: sincronizar antes de cada jornada. |

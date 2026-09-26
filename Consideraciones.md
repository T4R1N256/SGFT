# Consideraciones SGT (BORRADOR)

SGFT debe ser un PWA (Progressive Web App). No proviene de App Store asi que no
necesita el Apple Developer Program.

El usuario abre Safari en la URL indicada, la agrega a pantalla de inicio, y
ahi se crea un icono como cualquier otra App.

No hay necesidad de compilar en XCode. Ni de revision de Apple, certificados o
caducidad.

Safari no soporta background sync API. Por lo que la sincronizacion no puede
correr en segundo plano. Tiene que dispararse con la app abierta y visible.
Ademas el almacenamiento local puede desalojarse por lo que la aplicacion debe
bloquear la salida del usuario si no ha sincronizado la informacion.

Medidas:

- Instalar en la pantalla de inicio
- Pedir almacenamiento persistente (navigator.store.persist())
- Contador de pendientes por sincronizar
- Exportacion de emergencia: exportar la cola pendiente de sincronizar a un
  archivo de texto/JSON/etc. para copiarlo y luego enviarlo.

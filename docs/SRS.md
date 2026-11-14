# Especificación de Requisitos de Software (SRS) — Sistema de Gestión de Food Truck (SGFT)

**Universidad Autónoma de Ciudad Juárez** · Departamento de Ingeniería Eléctrica y Computación
Administración y Evaluación de Proyectos de Tecnologías de Información · Mtro. Abraham López Nájera

**Equipo:** Diego Adrián Galindo Mora (244970) · César Yahir Enríquez Jasso (246056) · Jesús Eduardo Hernández Garrido (249285) · Jared Gustavo Beltrán Herrada (234878) · Alejandro Tarín Gutiérrez (247521)

## 1. Introducción

El presente apartado establece la finalidad del documento de Especificación de Requisitos de Software (SRS) y delimita formalmente la frontera del producto que será construido en el marco del proyecto Sistema de Gestión de Food Truck (SGFT).

### 1.1 Propósito

Este documento tiene por objeto especificar de manera completa, precisa, verificable y libre de ambigüedades el conjunto de requisitos funcionales y no funcionales que deberá satisfacer el Sistema de Gestión de Food Truck (SGFT), solución web desarrollada para el establecimiento comercial «El Pardo», ubicado en Ciudad Juárez, Chihuahua, conforme a la autorización otorgada por su propietario en la carta de Apertura de Proyecto firmada el 13 de agosto de 2026 [1].

La especificación se elabora a partir de la información obtenida durante la fase de levantamiento de requisitos, la cual incluyó una entrevista directa al propietario del negocio [3], la observación y documentación de los cuatro procesos vigentes (toma de pedido y cobro, preparación de alimentos, control de inventario y cierre de caja) y el estudio de mercado realizado sobre el corredor comercial de la Avenida Vicente Guerrero [2]. Las decisiones de alcance y las definiciones metodológicas adoptadas durante esta fase constan en las minutas de reunión y en los reportes de avance del equipo [4].

De manera específica, el presente documento persigue los siguientes propósitos:

- Formalizar el entendimiento común entre el cliente y el equipo de desarrollo respecto a qué será construido, estableciendo un lenguaje unificado que evite interpretaciones divergentes durante la ejecución del proyecto.
- Construir la línea base de requisitos contra la cual se estructura y prioriza el Product Backlog, se derivan las historias de usuario y se planifica el contenido de cada Sprint bajo el marco de trabajo Scrum adaptado por el equipo.
- Proveer el insumo técnico para las actividades de diseño de la arquitectura del sistema, el modelado de la base de datos y la construcción modular del software.
- Servir como fuente para el diseño y ejecución de las pruebas, habilitando la trazabilidad requisito – caso de prueba (Apéndice B) y, con ello, la verificación objetiva del cumplimiento de lo acordado [5].
- Documentar los supuestos, restricciones y exclusiones, a fin de sustentar el control de cambios y prevenir la expansión no controlada del alcance.

### 1.2 Alcance

#### 1.2.1 Identificación del producto

Sistema de Gestión de Food Truck (SGFT) es una aplicación web responsiva e instalable (PWA), accesible desde el navegador de un teléfono, tableta o computadora, sin tienda de aplicaciones ni hardware especializado. El dispositivo principal de operación es un iPhone 17, que se instala la aplicación en su pantalla de inicio y puede vender sin conexión a internet.

Constituye un desarrollo nuevo: no sustituye ni se integra con ningún sistema informático preexistente, dado que el establecimiento opera actualmente mediante registros manuales en cuaderno y control empírico de existencias [2].

El sistema es operado exclusivamente por el personal del negocio bajo dos roles con distintos niveles de acceso: Administrador y Cajero. El comensal no constituye un actor del sistema. El sistema no recaba ni almacena información personal de los comensales.

#### 1.2.2 Situación actual y problemática que atiende

Los cuatro procesos operativos se ejecutan de forma manual: pedidos anotados en cuaderno, totales calculados mentalmente, existencias verificadas por conteo visual, compras registradas de memoria y corte de caja sumado a mano. Consecuencias:

- Riesgo de error en captura de pedidos, personalizaciones y cálculo de importes.
- Desconocimiento del nivel real de existencias → desabasto o mermas por caducidad y sobrecompra.
- Nula visibilidad del costo de venta y del margen real por producto y periodo.
- Tiempo improductivo en el cierre de caja y la conciliación de ingresos.
- Concentración del conocimiento operativo en una sola persona.
- Imposibilidad de analizar históricamente la demanda.

#### 1.2.3 Lo que el sistema hace

El SGFT digitaliza la operación diaria del food truck a través de cuatro módulos:

- **Punto de Venta.** Registra los pedidos desde el catálogo de platillos, permite personalizar cada línea quitando ingredientes o agregando extras, calcula el total de forma automática y registra el cobro con su método de pago (efectivo o transferencia). Una venta confirmada se corrige con un ajuste o una cancelación que deja rastro. Funciona con y sin internet: sin conexión, las ventas se guardan en el dispositivo y se envían al servidor al recuperar la red.
- **Gestión de Inventario y Productos.** Mantiene el catálogo de platillos, precios, insumos y recetas; descuenta los insumos automáticamente con base en la receta de cada platillo vendido; registra compras y mermas, y emite alertas cuando un insumo alcanza su nivel mínimo.
- **Gestión de Usuarios.** Controla el acceso con dos roles, Administrador y Cajero. Las cuentas se administran en Django Admin. El dispositivo se activa una vez con el PIN de un Administrador, y lo restringido pide ese PIN.
- **Reportes y Caja.** Registra la apertura y el cierre del turno de caja, automatiza el corte por método de pago y genera reportes de ventas por periodo, productos más vendidos, insumos usados, mermas y ganancia, además del PDF de las ventas del día.

#### 1.2.4 Lo que el sistema no hace

- No procesa pagos con tarjeta ni se integra con pasarelas de pago o terminales bancarias; únicamente registra el método de pago empleado.
- No gestiona pedidos a domicilio ni se integra con plataformas de reparto (Uber Eats, DiDi Food).
- No emite comprobantes fiscales digitales (CFDI) ni se integra con el SAT, ni genera tickets para el cliente.
- No registra pedidos fuera del menú: se vende lo que está en el catálogo, con sus personalizaciones.
- No incluye una vista de pedidos para cocina.
- No sustituye la contabilidad formal del negocio ni administra nómina.
- No incluye la adquisición, instalación ni configuración de hardware: equipos, impresoras de tickets o infraestructura de red.
- No es una aplicación móvil nativa ni se distribuye en tiendas de aplicaciones; se instala desde el navegador como PWA.
- No opera múltiples sucursales ni consolida información entre unidades.
- No incluye programas de lealtad, CRM ni funciones de mercadotecnia.
- No digitaliza los registros históricos del cuaderno; la carga inicial se limita a los catálogos del negocio.

### 1.3 Definiciones, acrónimos y abreviaturas

#### 1.3.1 Abreviaturas y términos técnicos

- **SRS:** Software Requirements Specification.
- **CRUD:** Create, Read, Update, Delete.
- **DB:** Database.
- **API:** Application Programming Interface.
- **PWA:** Progressive Web App; aplicación web que se instala desde el navegador y funciona sin conexión.
- **PIN de Administrador:** contraseña de 6 dígitos de la cuenta de un Administrador.
- **UUID:** identificador único que el dispositivo asigna a cada operación hecha sin conexión.
- **Cuarentena:** operación sincronizada que el servidor no pudo aplicar y que espera la resolución del Administrador.

#### 1.3.2 Léxico Extendido del Lenguaje

**Sujetos**

| Término | Definición | Noción | Sinónimos | Impacto |
|---|---|---|---|---|
| Cliente | Persona que compra en un establecimiento. | Una persona que llega al food truck para adquirir algún platillo. | Comprador, consumidor, adquiriente, prospecto de venta, comensal. | Es quien recibe el platillo. No es usuario del sistema. |
| Administrador | Dueño del negocio o establecimiento. | Es el propietario y administrador del food truck. | Propietario, dueño, encargado, gerente, titular, patrón. | Define precios, recetas y mínimos; registra compras y mermas; abre y cierra el turno de caja; consulta reportes y resuelve la bandeja de revisión. |
| Cajero | Persona que trabaja al servicio del establecimiento atendiendo la venta. | Empleado encargado de tomar pedidos y cobrar. | Trabajador, encargado de caja, colaborador. | Toma pedidos y cobra, con o sin red, mientras haya un turno abierto. No abre ni cierra el turno. |
| Teléfono celular | Equipo portátil para comunicación y acceso a internet. | Dispositivo en el que opera el sistema. | Móvil, celular, smartphone. | Un iPhone 17 con la PWA instalada; queda activado con la cuenta de cajero. |

**Verbos**

| Término | Definición | Noción | Sinónimos | Impacto |
|---|---|---|---|---|
| Surtir | Proveer a alguien de un producto. | Comprar insumos para reabastecer. | Comprar, adquirir, reabastecer, suministrar. | Registra una compra que suma existencia y actualiza el costo del insumo. |
| Vender | Traspasar a alguien un producto por el precio convenido. | Intercambiar platillos a cambio de dinero. | Despachar, cobrar, expender. | Registra la venta y descuenta los insumos de la receta cuando la venta llega al servidor. |
| Abrir caja | Registrar el efectivo inicial al comenzar la jornada. | El Administrador, con su PIN, abre el turno del día. | Iniciar turno, habilitar caja, registro de apertura. | Sin turno abierto no se puede vender. |
| Cerrar caja | Registrar el efectivo contado al terminar la jornada. | El Administrador, con su PIN, cierra el turno y obtiene el corte. | Corte de caja, cerrar turno, cuadrar caja. | Se niega si quedan ventas sin sincronizar; la diferencia de efectivo se registra. |
| Registrar | Dar de alta un platillo, insumo, receta, compra o merma. | Capturar sus datos en el sistema. | Dar de alta, catalogar, agregar, capturar. | Actualiza el catálogo o el inventario. |
| Actualizar | Modificar información previamente registrada. | Cambiar precio, receta o mínimo de un elemento existente. | Modificar, editar, cambiar. | Solo lo hace el Administrador. |
| Buscar producto | Localizar algo mediante algún criterio. | Consultar un platillo o insumo por nombre o categoría. | Consultar, filtrar, encontrar. | Agiliza la venta y la gestión del inventario. |
| Personalizar | Adaptar un platillo al gusto del comensal. | Quitar ingredientes o agregar extras a una línea del pedido. | Ajustar, adaptar, modificar. | Un ingrediente quitado no se descuenta; un extra descuenta su cantidad y puede cambiar el precio. |
| Activar dispositivo | Dejar el dispositivo en sesión con la cuenta de cajero. | Se hace una vez con el PIN de un Administrador. | Habilitar, registrar el dispositivo. | Permite vender sin iniciar sesión cada vez. |
| Desbloquear | Autorizar lo restringido con el PIN de Administrador. | Escribir el PIN para entrar a Productos, Inventario, Caja o Reportes. | Autorizar, validar. | Queda desbloqueado 30 minutos a nombre de ese Administrador. |
| Sincronizar | Enviar al servidor lo hecho sin conexión. | La cola del dispositivo se envía al volver la red o con «Sincronizar». | Enviar, actualizar, subir. | El servidor aplica cada operación una sola vez. |
| Pagar | Entregar dinero a cambio de los platillos. | El cliente liquida el total y se registra el método. | Liquidar, cubrir, saldar. | Confirma la venta. |
| Consultar inventario | Revisar el estado actual de los insumos. | Ver existencias y su nivel frente al mínimo. | Ver existencias, revisar stock. | Permite detectar necesidades de reabastecimiento. |
| Generar reporte | Producir información organizada de un periodo. | Resumen de ventas, más vendidos, insumos, mermas o ganancia. | Elaborar reporte, emitir informe. | Facilita la toma de decisiones. |

**Objetos**

| Término | Definición | Impacto |
|---|---|---|
| Platillo | Producto del menú con nombre, categoría y precio. | Es lo que se vende; su receta define qué insumos descuenta. |
| Insumo | Materia prima con unidad de medida (kg, g, L, ml o piezas), existencia, costo y mínimo. | Su existencia baja con las ventas y mermas y sube con las compras. |
| Receta | Cantidad de cada insumo que lleva un platillo. | Determina el descuento de inventario y el costo del platillo. |
| Pedido | Conjunto de líneas (platillo, unidades y personalizaciones) antes de cobrar. | Al cobrarse se convierte en venta. |
| Venta | Pedido cobrado, con método de pago, total y dos marcas de tiempo (dispositivo y servidor). | Es inmutable; alimenta la caja y los reportes. |
| Turno de caja | Jornada con efectivo inicial, efectivo final y diferencia. | Toda venta pertenece a un turno abierto. |
| Reporte | Información consolidada de un periodo. | Muestra ventas, ganancias y uso del inventario. |

**Estados**

| Grupo | Estado | Definición | Impacto |
|---|---|---|---|
| Insumo | Disponible | La existencia está arriba del mínimo. | Operación normal. |
| Insumo | Stock bajo | La existencia es menor o igual al mínimo. | Se muestra la alerta; la venta no se bloquea. |
| Insumo | Negativo | Una sincronización dejó la existencia bajo cero. | Se registra y la venta queda marcada para revisión. |
| Venta | En proceso | El pedido se está armando. | Se pueden agregar, quitar y personalizar líneas. |
| Venta | Pendiente de sincronizar | Se cobró sin conexión y está en la cola del dispositivo. | No descuenta inventario hasta llegar al servidor. |
| Venta | Confirmada | La venta se cobró y está registrada. | Es inmutable. |
| Venta | Ajustada o cancelada | Se corrigió con un ajuste o una cancelación con motivo. | La original se conserva con referencia a su corrección. |
| Venta | Para revisión | Llegó con precio distinto al catálogo o dejó una existencia negativa. | Aparece en la bandeja de revisión del Administrador. |
| Caja | Abierta | Hay un turno abierto. | Se pueden registrar ventas. |
| Caja | Cerrada | No hay turno abierto. | No se pueden registrar ventas. |
| Caja | Cuadrada / con diferencia | Tras el cierre, el efectivo contado coincide o no con el esperado. | La diferencia se registra como dato informativo y no bloquea. |
| Cuenta | Activa / desactivada | La cuenta puede o no operar. | Las cuentas se desactivan, nunca se borran. |
| Dispositivo | Bloqueado / desbloqueado | Lo restringido requiere o no el PIN de Administrador. | El desbloqueo dura 30 minutos. |

**Reglas de negocio**

1. El inventario se descuenta cuando la venta llega al servidor (en línea, al confirmar; sin conexión, al sincronizar), en la misma transacción que registra la venta, recorriendo la receta.
2. Las personalizaciones ajustan el descuento: quitar un ingrediente no lo descuenta; un extra descuenta la cantidad adicional y puede cambiar el precio de la línea.
3. La alerta de stock aparece cuando la existencia es menor o igual al mínimo; es visual y no bloquea la venta.
4. El pago es solo en efectivo o transferencia; se registra como atributo de la venta, nunca se ejecuta ni se concilia.
5. El corte de caja consolida las ventas del turno por método de pago. No se genera si hay ventas sin sincronizar: se niega e indica cuántas faltan. La diferencia de efectivo se anexa como dato informativo y no bloquea.
6. Precios, recetas y mínimos solo los define el Administrador.
7. Una venta es inmutable desde que se confirma el cobro, también en la cola sin conexión. Se corrige con un ajuste o una cancelación que deja rastro y referencia a la original.
8. Toda operación sin conexión lleva un UUID generado en el dispositivo; el servidor descarta los repetidos mediante una restricción de unicidad en la base de datos.
9. Lo que el servidor no puede aplicar va a cuarentena; nunca se rechaza. El Administrador la resuelve con una de tres salidas: aplicar con el catálogo actual, aplicar sin descontar inventario o descartar.
10. Una existencia puede quedar negativa tras sincronizar: se registra, se marca para revisión y la venta no se revierte.
11. El motivo del ajuste decide qué se revierte: el error de captura revierte dinero e inventario; la devolución revierte el dinero y registra el insumo como merma; la corrección de pago solo cambia el método al que se atribuye.
12. Toda venta requiere un turno de caja abierto; se valida antes de calcular, con o sin red.
13. Hay un turno por jornada, con una apertura y un cierre; solo el Administrador lo abre o lo cierra, con su PIN, también sin conexión.
14. Si al sincronizar el total del catálogo vigente difiere de lo cobrado, manda lo cobrado y la venta se marca para revisión; si lo cobrado no corresponde a las líneas de su propio pedido, va a cuarentena.

### 1.4 Visión general

El presente documento está dirigido a toda persona que requiera una comprensión completa del sistema: el cliente y los usuarios finales del food truck, el equipo de análisis, desarrollo y pruebas, el docente asesor de la asignatura y cualquier interesado que deba retomar el proyecto con posterioridad. Su redacción sigue las directrices del estándar IEEE 830-1998 para la especificación de requisitos de software, complementadas con las prácticas de ingeniería de requisitos establecidas en ISO/IEC/IEEE 29148.

El documento se organiza de lo general a lo particular: la sección 1 establece el propósito, el alcance y el vocabulario; la sección 2 describe el producto, sus usuarios, restricciones y supuestos; la sección 3 especifica los requisitos, su clasificación, los casos de uso y su priorización. Los apéndices reúnen el material de soporte y la matriz de trazabilidad de requisitos a pruebas.

Al ejecutarse el proyecto bajo la metodología Scrum, este documento es un artefacto vivo: se refina de forma incremental conforme avanzan los Sprints y se incorpora la retroalimentación del cliente. Toda modificación de la línea base deberá autorizarse antes de ser incorporada al Product Backlog.

### 1.5 Referencias

**a) Documentos internos del proyecto**

1. A. Cárdenas de la Mora, D. A. Galindo Mora y A. López Nájera, «Carta de Apertura del Proyecto: Sistema de Gestión de Food Truck (SGFT)», Universidad Autónoma de Ciudad Juárez, Ciudad Juárez, México, 13 de agosto de 2026. [Documento interno, Anexo 1 del Documento de Fase 1].
2. Equipo de desarrollo SGFT, «Sistema de Gestión de Food Truck (SGFT) — Fase 1: Información de la empresa y del proyecto», Universidad Autónoma de Ciudad Juárez, Departamento de Ingeniería Eléctrica y Computación, agosto de 2026. [Documento interno].
3. Equipo de desarrollo SGFT, «Entrevista de levantamiento de requisitos aplicada al propietario del food truck El Pardo», Ciudad Juárez, México, agosto de 2026. [Instrumento de recolección de datos, documento interno].
4. Equipo de desarrollo SGFT, «Minutas de reunión No. 1 a No. 6 y reportes de avance semanal, semanas 1 a 3», Universidad Autónoma de Ciudad Juárez, agosto de 2026. [Documentos internos, Anexo 2 del Documento de Fase 1].

**b) Normas, estándares y marcos metodológicos**

5. A. Llanque, V. Flores y A. Dávila, «Metodologías centradas en el usuario para la ingeniería de requisitos: un análisis comparativo utilizando ISO/IEC/IEEE 29148», *ReCIBE. Revista Electrónica de Computación, Informática, Biomédica y Electrónica*, vol. 11, núm. 1, 2022. doi: 10.32870/recibe.v11i1.242. [En línea]. Disponible: https://recibe.cucei.udg.mx/index.php/ReCIBE/article/view/242
6. «personalizar», Diccionario de la lengua española, Real Academia Española – Asociación de Academias de la Lengua Española. [En línea]. Disponible en: https://dle.rae.es/personalizar. [Accedido: 3 de sep. de 2026].
7. OWASP Foundation, «OWASP Top 10:2021». [En línea]. Disponible en: https://owasp.org/Top10/.

## 2. Descripción general

### 2.1 Perspectiva del producto

El producto conforma una solución nueva: es la primera solución tecnológica que se emplea en el food truck «El Pardo» para optimizar sus operaciones. Como el dueño no cuenta con presupuesto para servicios de pago, todo se construye con herramientas gratuitas o de código abierto y se despliega en planes gratuitos.

La arquitectura tiene dos partes:

- **Servidor:** una aplicación Django con base de datos PostgreSQL, que es la fuente de verdad. Aplica las reglas de negocio, registra las ventas y el inventario y genera los reportes. Se despliega en Railway con la base de datos en Neon.
- **Dispositivo:** la PWA instalada en el iPhone guarda en su almacenamiento local (IndexedDB) el menú, el estado del turno y una cola de operaciones. Sin conexión, cobra y abre el turno desde esa copia; al volver la red, envía la cola al servidor, que aplica cada operación una sola vez.

Las tecnologías que se utilizan son:

- PostgreSQL 16 o superior.
- Python 3.12 con Django 5.2 LTS, servido con Gunicorn y WhiteNoise.
- Plantillas de Django con HTMX 2 y Alpine.js 3.
- Tailwind CSS v4.
- Dexie.js (IndexedDB) y Workbox (service worker).

### 2.2 Funciones del producto

- Registrar ventas con y sin conexión a internet, con su método de pago.
- Mantener el catálogo de platillos, precios, insumos y recetas.
- Mantener el control del inventario: descuento por venta, compras, mermas y alertas de mínimo.
- Abrir y cerrar el turno de caja y obtener el corte.
- Generar reportes de ventas, más vendidos, insumos, mermas y ganancia, y el PDF de las ventas del día.
- Controlar quién interactúa con la aplicación mediante la activación del dispositivo y el PIN de Administrador.

### 2.3 Características del usuario

| Rol | Nivel técnico | Frecuencia de uso |
|---|---|---|
| Cajero | Conocimiento básico de operación de dispositivos móviles. | Diario. |
| Administrador (dueño) | Conocimiento básico de operación de dispositivos móviles. | Diario. |

### 2.4 Restricciones

**Técnicas y de lenguaje**

- PostgreSQL es el motor de base de datos de la aplicación.
- Django genera las páginas en el servidor; HTMX actualiza fragmentos de la página y Alpine.js guarda solo el estado local de la interfaz. El único JavaScript propio es el del modo sin conexión.
- El código se versiona con git: una rama por tarea y Pull Requests revisados antes de integrarse a la rama principal.
- Las dependencias se fijan en versiones concretas; una dependencia nueva se justifica y se aprueba antes de agregarse.

**Base de datos e infraestructura**

- La base de datos es SQL (PostgreSQL).
- El servidor es la fuente de verdad. Lo que el dispositivo registra sin conexión se aplica al sincronizar, y lo que no se puede aplicar va a cuarentena para que el Administrador lo resuelva.
- Cada operación hecha sin conexión lleva un UUID; la base de datos garantiza que no se aplique dos veces.
- El dinero nunca se representa en punto flotante: en el servidor se guarda como decimal exacto con dos decimales y en el dispositivo como enteros de centavos.
- El cálculo del total da el mismo resultado en el servidor y en el dispositivo; lo comprueba una prueba automática.
- La infraestructura no tiene costo para el cliente.

**Políticas y seguridad**

- Las contraseñas y el PIN se guardan con el hash del sistema de autenticación de Django (PBKDF2-SHA256), nunca en texto plano.
- El dispositivo nunca guarda el PIN; para abrir la caja sin conexión guarda un verificador PBKDF2 por Administrador, que caduca a los 7 días sin sincronizar.
- Solo el Administrador modifica precios, recetas, mínimos, inventario y cuentas.
- Lo restringido pide el PIN de Administrador y queda desbloqueado 30 minutos; después se vuelve a pedir.
- La autorización se valida en el servidor en cada petición, también al sincronizar.
- La protección contra CSRF está siempre activa.
- Solo se guardan datos personales del personal (nombre, rol y credenciales), conforme a la LFPDPPP.

**Limitaciones del proyecto**

- Finalización del proyecto: 15/11/2026.

### 2.5 Suposiciones y dependencias

- El proyecto se realiza en un plazo no menor a 2 meses.
- Las entrevistas con el cliente han sido suficientes para modelar su flujo de trabajo.
- El cliente cuenta con un iPhone para operar el sistema.
- Los roles dentro de la empresa están bien definidos: un Administrador (el dueño) y personal de caja.
- Railway y Neon mantienen sus planes gratuitos durante el proyecto.
- El dispositivo cuenta con espacio suficiente para la copia local del menú y la cola de operaciones.
- Hay conexión a internet al menos al inicio de cada jornada para sincronizar.
- Las tecnologías elegidas son estables y sus dependencias se mantienen en versiones fijas durante el proyecto.

## 3. Requisitos específicos

### 3.1 Requisitos funcionales

| ID | Requerimiento | Descripción |
|---|---|---|
| RF-01 | Registro rápido de pedidos | El sistema debe permitir registrar un pedido en menos de 1 minuto, seleccionando platillos del catálogo por categoría o búsqueda. |
| RF-02 | Personalización de platillos | El sistema debe permitir quitar ingredientes o agregar extras a cada línea del pedido; un extra puede cambiar el precio de la línea. |
| RF-03 | Cálculo automático de total | El sistema debe mostrar el total del pedido automáticamente, con el mismo resultado con y sin conexión. |
| RF-04 | Registro de pagos | El sistema debe registrar el método de pago de cada venta: efectivo o transferencia. |
| RF-05 | Ajuste y cancelación de ventas | El sistema debe permitir al Administrador ajustar o cancelar una venta confirmada con un motivo (error de captura, devolución o corrección de pago), conservando la original y su rastro. |
| RF-06 | Turno de caja | El sistema debe permitir al Administrador, con su PIN, abrir el turno con su efectivo inicial y cerrarlo con el efectivo contado, un turno por jornada; sin turno abierto no se vende. |
| RF-07 | Modo sin conexión | El sistema debe permitir vender y abrir el turno sin internet, guardar esas operaciones en el dispositivo y sincronizarlas automáticamente al recuperar la conexión. |
| RF-08 | Descuento automático de inventario | El sistema debe descontar los insumos de la receta al registrar una venta en el servidor, considerando sus personalizaciones. |
| RF-09 | Registro de insumos con unidad | El sistema debe permitir registrar insumos con unidad de medida (kilogramos, gramos, litros, mililitros o piezas). |
| RF-10 | Alertas de stock mínimo | El sistema debe permitir definir un mínimo por insumo y mostrar una alerta cuando la existencia lo alcance. |
| RF-11 | Registro de compras | El sistema debe permitir registrar compras de insumos con cantidad, costo unitario y fecha, sumando la existencia y actualizando el costo del insumo. |
| RF-12 | Cálculo de costo de platillos | El sistema debe calcular el costo y el margen de cada platillo con base en su receta y el costo de sus insumos. |
| RF-13 | Registro de mermas | El sistema debe registrar mermas con su motivo (caducidad, mal almacenamiento, daño en empaque, maduración u otro) y ajustar el inventario. |
| RF-14 | Gestión de cuentas con roles | El sistema debe permitir crear, cambiar de rol y desactivar cuentas con los roles Administrador y Cajero; las cuentas nunca se borran y siempre queda un Administrador activo. |
| RF-15 | Restricción de acceso | El sistema debe restringir Productos, Inventario, Caja y Reportes al Administrador, mediante su PIN. |
| RF-16 | Bandeja de revisión | El sistema debe mostrar al Administrador las ventas marcadas para revisión (precio distinto o existencia negativa) y las operaciones en cuarentena, y permitirle resolverlas. |
| RF-17 | Catálogo de platillos y recetas | El sistema debe permitir al Administrador crear y editar platillos con su categoría, precio, disponibilidad y receta. |
| RF-18 | Corte de caja | El sistema debe generar el corte del turno con el desglose por método de pago y la diferencia de efectivo, y negarlo si hay ventas sin sincronizar. |
| RF-19 | Reporte de ganancia neta | El sistema debe generar un reporte de ganancia neta (ingresos − costo de insumos) por día, semana o mes. |
| RF-20 | Reporte de productos más vendidos | El sistema debe generar un reporte de los platillos más vendidos del periodo. |
| RF-21 | Reporte de insumos y mermas | El sistema debe generar un reporte de insumos usados y mermas del periodo, y mostrar el inventario actual. |
| RF-22 | Exportación de reportes | El sistema debe exportar las ventas del día en formato PDF. |
| RF-23 | Activación del dispositivo | El sistema debe permitir activar el dispositivo una vez con el PIN de un Administrador, dejándolo en sesión con la cuenta de cajero. |
| RF-24 | Límite de intentos del PIN | El sistema debe bloquear el PIN durante 15 minutos tras 5 intentos fallidos seguidos, también en el inicio de sesión de Django Admin. |

### 3.2 Requisitos no funcionales

| ID | Requerimiento | Descripción |
|---|---|---|
| RNF-01 | Usabilidad táctil | La interfaz debe ser operable con una mano en la pantalla táctil de un smartphone (iPhone 17). |
| RNF-02 | Tamaño de botones | Los botones deben ser de tamaño mínimo 40 px para uso con dedos. |
| RNF-03 | Legibilidad en exteriores | La interfaz debe tener alto contraste y ser legible bajo luz solar directa. |
| RNF-04 | Ayudas visuales | La interfaz debe indicar en español el estado y la siguiente acción: caja cerrada, sin conexión, operaciones pendientes o PIN requerido. |
| RNF-05 | Atención en hora pico | Registrar una venta no debe depender de la red: el cobro se completa en el dispositivo aunque no haya conexión. |
| RNF-06 | Tiempo de respuesta | El sistema debe responder en menos de 2 segundos en condiciones de conexión móvil promedio. |
| RNF-07 | Sincronización | La sincronización debe completarse en menos de 30 segundos al recuperar la conexión. |
| RNF-08 | Operación sin internet | El punto de venta, incluida la apertura del turno, debe funcionar sin conexión a internet; Productos, Inventario, Caja y Reportes se consultan sin conexión con los datos de la última sincronización, con el PIN de Administrador validado en el dispositivo. |
| RNF-09 | Compatibilidad de navegadores | El sistema debe funcionar en las versiones actuales de Safari para iOS y de Chrome. |
| RNF-10 | Diseño responsivo | El sistema debe adaptarse a smartphone, tableta y computadora. |
| RNF-11 | Autenticación | El sistema debe requerir el PIN de Administrador para cualquier proceso administrativo, y usuario y contraseña en Django Admin. |
| RNF-12 | Rastro de operaciones | Cada venta, ajuste, movimiento de inventario, turno y resolución de cuarentena debe guardar quién la hizo y cuándo. |
| RNF-13 | Confidencialidad de reportes | Los reportes financieros solo deben ser visibles para el Administrador. |
| RNF-14 | Modularidad | El código debe organizarse en módulos independientes (usuarios, catálogo, inventario, punto de venta y reportes) con capas de vistas, servicios y modelos. |

### 3.3 Clasificación de requerimientos usando FURPS+

| Categoría | IDs |
|---|---|
| Funcionalidad (Functionality) | RF-01 a RF-24 |
| Usabilidad (Usability) | RNF-01, RNF-02, RNF-03, RNF-04, RNF-10 |
| Confiabilidad (Reliability) | RNF-07, RNF-08, RNF-12 |
| Rendimiento (Performance) | RNF-05, RNF-06 |
| Soporte (Supportability) | RNF-09, RNF-14 |
| Seguridad (+) | RNF-11, RNF-13 |

### 3.4 Casos de uso con descripción textual

#### Caso de uso 1: Registrar venta

| Elemento | Descripción |
|---|---|
| Nombre | Registrar venta |
| Actor principal | Cajero |
| Actores secundarios | Cliente |
| Propósito | Permitir al cajero registrar un pedido de forma rápida y precisa, incluidas sus personalizaciones, y cobrarlo. |
| Precondiciones | El dispositivo está activado y hay un turno de caja abierto. |
| Postcondiciones | La venta queda registrada con su método de pago y los insumos se descuentan al llegar al servidor; sin conexión, la venta queda en la cola del dispositivo hasta sincronizar. |

Flujo principal:

1. El cajero abre «Nueva venta».
2. El sistema muestra los platillos disponibles por categoría.
3. El cajero selecciona el platillo solicitado por el cliente.
4. El cajero personaliza la línea si hace falta (quitar ingredientes o agregar extras).
5. El sistema calcula y muestra el total del pedido.
6. El cajero selecciona el método de pago (efectivo o transferencia).
7. El cajero confirma la compra.
8. El sistema registra la venta (o la guarda en la cola si no hay conexión) y vacía el ticket.

#### Caso de uso 2: Gestionar inventario

| Elemento | Descripción |
|---|---|
| Nombre | Gestionar inventario |
| Actor principal | Administrador |
| Actores secundarios | — |
| Propósito | Permitir al Administrador registrar compras y mermas y monitorear el inventario para evitar desabastos y mermas. |
| Precondiciones | El Administrador desbloqueó Inventario con su PIN. |
| Postcondiciones | El inventario queda actualizado y el movimiento queda registrado a su nombre. |

Flujo principal:

1. El Administrador abre «Inventario».
2. El sistema muestra los insumos con su existencia y destaca los que están en su mínimo o por debajo.
3. El Administrador elige registrar una compra o una merma.
4. El Administrador selecciona el insumo e ingresa la cantidad (y el costo unitario, en una compra, o el motivo, en una merma).
5. El Administrador confirma.
6. El sistema registra el movimiento y actualiza la existencia.

#### Caso de uso 3: Abrir y cerrar el turno de caja

| Elemento | Descripción |
|---|---|
| Nombre | Abrir y cerrar el turno de caja |
| Actor principal | Administrador |
| Actores secundarios | Cajero |
| Propósito | Registrar el efectivo inicial y final de la jornada y obtener el corte. |
| Precondiciones | Para abrir, no hay un turno en la jornada; para cerrar, hay un turno abierto y ninguna venta pendiente de sincronizar. |
| Postcondiciones | El turno queda abierto para vender, o cerrado con su corte por método de pago y su diferencia de efectivo. |

Flujo principal:

1. El Administrador elige «Abrir caja» y escribe su PIN (con o sin conexión).
2. El Administrador captura el efectivo inicial; el sistema abre el turno a su nombre.
3. Durante la jornada se registran las ventas del turno.
4. Al terminar, el Administrador elige «Cerrar caja» en Caja y escribe su PIN.
5. El sistema muestra el efectivo esperado; el Administrador captura el efectivo contado.
6. El sistema cierra el turno y registra el corte con la diferencia, que no bloquea el cierre.

Flujo alterno: si quedan ventas sin sincronizar, el sistema niega el cierre e indica cuántas faltan.

### 3.5 Priorización de requerimientos por impacto en objetivos de negocio

Objetivos de negocio: #1 reducir tiempos de atención, #2 eliminar errores de cobro, #3 controlar el inventario, #4 conocer ganancias y costos, #5 optimizar el menú.

| Prioridad | ID | Requerimiento | Impacto en objetivos de negocio |
|---|---|---|---|
| Crítica (Must Have) | RF-01 | Registro rápido de pedidos | Objetivo #1 (reducción de tiempos). |
| Crítica (Must Have) | RF-02 | Personalización de platillos | Objetivo #2 (eliminar errores). |
| Crítica (Must Have) | RF-03 | Cálculo automático de total | Objetivo #2 (eliminar errores de cobro). |
| Crítica (Must Have) | RF-04 | Registro de pagos | Objetivo #4 (conocer ingresos por método). |
| Crítica (Must Have) | RF-06 | Turno de caja | Objetivos #2 y #4 (control del efectivo). |
| Crítica (Must Have) | RF-07 | Modo sin conexión | Objetivo #1 (continuidad operativa). |
| Crítica (Must Have) | RF-08 | Descuento automático de inventario | Objetivo #3 (control de inventario). |
| Crítica (Must Have) | RF-10 | Alertas de stock mínimo | Objetivo #3 (evitar desabastos). |
| Crítica (Must Have) | RF-14 | Gestión de cuentas con roles | Objetivos #2 y #4 (control y seguridad). |
| Crítica (Must Have) | RF-15 | Restricción de acceso | Objetivo #4 (confidencialidad). |
| Crítica (Must Have) | RF-18 | Corte de caja | Objetivo #4 (conocer ganancias). |
| Crítica (Must Have) | RF-23 | Activación del dispositivo | Objetivo #1 (vender sin iniciar sesión). |
| Crítica (Must Have) | RNF-01 | Usabilidad táctil | Objetivo #1 (velocidad de atención). |
| Crítica (Must Have) | RNF-08 | Operación sin internet | Objetivo #1 (continuidad operativa). |
| Crítica (Must Have) | RNF-11 | Autenticación | Objetivos #2 y #4 (control y seguridad). |
| Crítica (Must Have) | RNF-13 | Confidencialidad de reportes | Objetivo #4. |
| Importante (Should Have) | RF-05 | Ajuste y cancelación de ventas | Objetivo #2 (corregir con rastro). |
| Importante (Should Have) | RF-09 | Registro de insumos con unidad | Objetivo #3. |
| Importante (Should Have) | RF-11 | Registro de compras | Objetivos #3 y #4 (costos reales). |
| Importante (Should Have) | RF-12 | Cálculo de costo de platillos | Objetivo #4 (conocer costos reales). |
| Importante (Should Have) | RF-13 | Registro de mermas | Objetivo #3 (control de pérdidas). |
| Importante (Should Have) | RF-16 | Bandeja de revisión | Objetivo #2 (resolver diferencias). |
| Importante (Should Have) | RF-17 | Catálogo de platillos y recetas | Objetivos #3 y #4. |
| Importante (Should Have) | RF-19 | Reporte de ganancia neta | Objetivo #4 (conocer ganancias reales). |
| Importante (Should Have) | RF-24 | Límite de intentos del PIN | Seguridad de las cuentas. |
| Importante (Should Have) | RNF-02 | Tamaño de botones | Objetivo #1. |
| Importante (Should Have) | RNF-03 | Legibilidad en exteriores | Objetivo #1. |
| Importante (Should Have) | RNF-06 | Tiempo de respuesta | Objetivo #1. |
| Importante (Should Have) | RNF-07 | Sincronización | Objetivo #4 (datos al día). |
| Deseable (Could Have) | RF-20 | Reporte de productos más vendidos | Objetivo #5 (optimización de menú). |
| Deseable (Could Have) | RF-21 | Reporte de insumos y mermas | Objetivos #3 y #5. |
| Deseable (Could Have) | RF-22 | Exportación de reportes | Objetivo #4 (análisis externo). |
| Deseable (Could Have) | RNF-04 | Ayudas visuales | Objetivo #1. |
| Deseable (Could Have) | RNF-05 | Atención en hora pico | Objetivo #1. |
| Deseable (Could Have) | RNF-09 | Compatibilidad de navegadores | Objetivo #1. |
| Deseable (Could Have) | RNF-10 | Diseño responsivo | Objetivo #1. |
| Deseable (Could Have) | RNF-12 | Rastro de operaciones | Objetivo #2. |
| Deseable (Could Have) | RNF-14 | Modularidad | Mantenimiento futuro. |

### 3.6 Resumen de priorización por categoría

| Prioridad | Cantidad | IDs |
|---|---|---|
| Crítica (Must Have) | 16 | RF-01, RF-02, RF-03, RF-04, RF-06, RF-07, RF-08, RF-10, RF-14, RF-15, RF-18, RF-23, RNF-01, RNF-08, RNF-11, RNF-13 |
| Importante (Should Have) | 13 | RF-05, RF-09, RF-11, RF-12, RF-13, RF-16, RF-17, RF-19, RF-24, RNF-02, RNF-03, RNF-06, RNF-07 |
| Deseable (Could Have) | 9 | RF-20, RF-21, RF-22, RNF-04, RNF-05, RNF-09, RNF-10, RNF-12, RNF-14 |

## Apéndices

### Apéndice A. Diagramas y prototipos

| Material | Dónde está |
|---|---|
| Diagrama de casos de uso | Documento Word del SRS |
| Diagrama de procesos (WBS 1.4.1) | Documento Word del SRS |
| Diagrama SADT (WBS 1.5.1) | Documento Word del SRS |
| Modelo entidad-relación (WBS 1.6.1) | [`docs/diagramas/diagrama-er.md`](diagramas/diagrama-er.md), generado de los modelos |
| Wireframes (inicio, venta, inventario, caja, reportes) | Documento Word del SRS |
| Prototipos (venta bloqueada, venta, productos, reportes, inventario, menú lateral, cantidad, PIN de administrador) | Archivo de Figma del sistema de diseño «PuntoVenta» |

### Apéndice B. Matriz de trazabilidad (WBS 4.3)

Liga cada requisito de la sección 3 con la parte del sistema que lo atiende y las pruebas que lo comprueban.

**Estado:** ✅ implementado y con prueba automática · ✋ implementado; se verifica a mano en el dispositivo · ◐ prueba automática parcial; el resto se verifica a mano.

**Cómo leer «Pruebas»:** `Clase.método` en el archivo abreviado; si se nombra solo la clase, cuentan todas sus pruebas. `acc`/`acc-v` = `apps/accounts/tests.py`/`tests_views.py`; igual `cat` (catalog), `inv` (inventory), `pos` y `rep` (reports); `core` = `apps/core/tests.py`; `e2e` = `tests_e2e/test_*.py` (Playwright, `SGFT_E2E=1`); `node` = `tests_e2e/parity/*.mjs`.

#### B.1 Requisitos funcionales

| ID | Requisito | WBS | Estado | Pruebas |
|---|---|---|---|---|
| RF-01 | Registro rápido de pedidos | 3.3.1, 3.3.2 | ✅ | `pos-v` OrderBuilderTests, DishListTests, OrderSummaryTests · `e2e` SaleWithNetworkTests |
| RF-02 | Personalización de platillos | 3.3.3 | ✅ | `pos-v` OrderSummaryTests.test_modifiers_dialog_and_price, .test_a_line_with_the_same_modifiers_merges · `pos` ModifierTests · `inv` DeductForSaleTests.test_removed_ingredient_is_not_deducted, .test_extra_deducts_its_quantity_per_unit · `e2e` SaleWithNetworkTests |
| RF-03 | Cálculo automático de total | 3.3.4, 3.4.5 | ✅ | `pos` PricingParityTest · `node` test_pricing · `pos-v` OrderSummaryTests.test_add_item_sums_and_returns_ticket_and_card_out_of_band |
| RF-04 | Registro de pagos | 3.3.5 | ✅ | `pos-v` OrderSummaryTests.test_payment_method_selected_by_server, .test_invalid_payment_method_is_retargeted_to_messages · `pos` SaleServiceTests.test_malformed_order_or_payment_method |
| RF-05 | Ajuste y cancelación de ventas | 3.3.5 | ✅ | `pos` SaleAdjustmentTests, SaleServiceTests.test_cancel_for_capture_error_gives_money_and_inventory_back, .test_cancel_for_return_records_waste_and_keeps_stock, .test_cancel_needs_an_admin_a_valid_reason_and_happens_once, .test_adjust_units_of_a_line_and_then_cancel_the_rest, .test_payment_correction_only_moves_the_sale_to_the_other_method |
| RF-06 | Turno de caja | 3.5.1, 3.4.7 | ✅ | `pos` CashSessionServiceTests, CashRegisterSessionTests · `pos-v` OpenSessionTests, CloseSessionTests · `e2e` OpeningTests, CashCloseTests |
| RF-07 | Modo sin conexión | 3.4.1–3.4.7 | ✅ | `pos` SyncOperationsTests · `pos-v` PwaTests, OfflineDataTests, OfflineScreensTests · `node` test_pin_verifier · `e2e` SaleWithoutNetworkTests, OpeningTests, OfflineScreensTests |
| RF-08 | Descuento automático de inventario | 3.2.6 | ✅ | `inv` DeductForSaleTests · `pos` SaleServiceTests.test_online_sale_records_what_was_charged_and_deducts_inventory |
| RF-09 | Registro de insumos con unidad | 3.2.2 | ✅ | `cat` IngredientServicesTests · `cat-v` IngredientCreateTests |
| RF-10 | Alertas de stock mínimo | 3.2.4, 3.2.8 | ✅ | `inv` PurchaseWasteAndAlertTests.test_alert_when_stock_reaches_the_minimum, .test_check_min_stock_lists_the_most_urgent_first · `inv-v` IngredientListTests · `pos-v` OrderBuilderTests.test_low_stock_shows_the_alert · `cat` IngredientServicesTests.test_negative_minimum_is_rejected, .test_update_minimum_and_cost |
| RF-11 | Registro de compras | 3.2.5 | ✅ | `inv` StockMovementModelTests.test_purchase_adds_and_keeps_its_cost, PurchaseWasteAndAlertTests.test_purchase_adds_stock_and_updates_the_cost, .test_purchase_rejects_zero_negative_or_too_precise_quantities · `inv-v` StockFormTests.test_valid_purchase_adds_stock_in_the_admins_name_and_refreshes |
| RF-12 | Cálculo de costo de platillos | 3.2.3 | ✅ | `cat` RecipeServicesTests.test_cost_and_margin, .test_dish_without_recipe_costs_zero, DemoFixtureTests |
| RF-13 | Registro de mermas | 3.2.7 | ✅ | `inv` PurchaseWasteAndAlertTests.test_waste_subtracts_with_its_reason, .test_waste_needs_a_reason · `inv-v` StockFormTests.test_waste_dialog_lists_the_agreed_reasons, .test_waste_other_reason_is_required_and_limited |
| RF-14 | Gestión de cuentas con roles | 3.1.1, 3.1.3 | ✅ | `acc` UserModelTests, RoleTests, ChangeRoleTests, DeactivateUserTests, UserAdminTests, AccountEdgeCaseTests |
| RF-15 | Restricción de acceso | 3.1.3 | ✅ | `core` AdminPinRequiredTests, UnlockTests, RoleRequiredTests · `cat-v` AccessTests · `inv-v` AccessTests · `rep-v` AccessTests |
| RF-16 | Bandeja de revisión | 3.4.9 | ✅ | `pos` QuarantineResolutionTests, SalesAdminTests, SyncOperationsTests.test_review_reasons |
| RF-17 | Catálogo de platillos y recetas | 3.2.1, 3.2.3 | ✅ | `cat` DishServicesTests, RecipeServicesTests · `cat-v` DishCatalogTests, DishFormTests, RecipeTests |
| RF-18 | Corte de caja | 3.5.2 | ✅ | `rep` ReportServiceTests.test_cash_close_while_open_and_after_closing · `pos` CashSessionServiceTests.test_totals_by_method_net_of_reversions, .test_close_is_refused_with_unsynced_sales, .test_close_records_the_difference_without_blocking · `rep-v` CashTests · `e2e` CashCloseTests |
| RF-19 | Reporte de ganancia neta | 3.5.3 | ✅ | `rep` ReportServiceTests.test_ingredients_used_waste_and_profit, .test_period_ranges · `rep-v` ReportsTests.test_totals_of_the_week, .test_period_returns_columns_and_replaces_subtitle_out_of_band |
| RF-20 | Reporte de productos más vendidos | 3.5.4 | ✅ | `rep` ReportServiceTests.test_top_dishes_skip_cancelled_sales_and_reverted_units |
| RF-21 | Reporte de insumos y mermas | 3.5.3, 3.2.8 | ✅ | `rep` ReportServiceTests.test_ingredients_used_waste_and_profit · `inv-v` IngredientListTests |
| RF-22 | Exportación de reportes | 3.5.5 | ✅ | `rep` ReportServiceTests.test_daily_sales_pdf · `rep-v` ExportDailySalesPdfTests |
| RF-23 | Activación del dispositivo | 3.1.2 | ✅ | `acc-v` ActivateDeviceViewTests · `acc` VerifyAdminPinTests.test_activate_device_returns_the_cashier_account, .test_activate_device_without_cashier |
| RF-24 | Límite de intentos del PIN | 3.1.2, 4.4 | ✅ | `acc` VerifyAdminPinTests.test_five_failures_lock_the_pin_even_for_the_right_one, .test_lock_expires, AdminLoginLimitTests · `acc-v` ActivateDeviceViewTests.test_five_failures_lock_even_with_a_new_cookie |

#### B.2 Requisitos no funcionales

| ID | Requisito | Estado | Evidencia |
|---|---|---|---|
| RNF-01 | Usabilidad táctil | ✋ | Prueba en el iPhone (T31). |
| RNF-02 | Tamaño de botones | ✋ | Medidas del sistema de diseño «PuntoVenta»; prueba en el iPhone (T31). |
| RNF-03 | Legibilidad en exteriores | ✋ | Auditoría de contraste del sistema de diseño; prueba en el food truck (T31). |
| RNF-04 | Ayudas visuales | ✅ | `e2e` OfflineScreensTests.test_padlock_screens_open_without_network_after_the_pin · `pos-v` OrderBuilderTests.test_closed_cash_disables_content_and_offers_open · `core` AdminPinRequiredTests.test_locked_full_page_shows_pin_required_with_dialog · `rep-v` CashTests.test_pending_operations_are_shown_in_the_close_card |
| RNF-05 | Atención en hora pico | ✅ | `e2e` SaleWithoutNetworkTests |
| RNF-06 | Tiempo de respuesta | ✋ | Medición en el iPhone con red móvil (T30). |
| RNF-07 | Sincronización | ◐ | `e2e` SaleWithoutNetworkTests, OpeningTests sincronizan dentro del límite de 15 s de la prueba; medición en el iPhone (T30). |
| RNF-08 | Operación sin internet | ✅ | `pos-v` PwaTests, OfflineDataTests, OfflineScreensTests · `e2e` SaleWithoutNetworkTests, OpeningTests, OfflineScreensTests |
| RNF-09 | Compatibilidad de navegadores | ◐ | La E2E corre en Chromium; Safari para iOS se prueba en el iPhone (T30). |
| RNF-10 | Diseño responsivo | ✋ | Prueba en el iPhone y en computadora (T31). |
| RNF-11 | Autenticación | ✅ | `core` AdminPinRequiredTests, UnlockTests · `acc` VerifyAdminPinTests, AdminLoginLimitTests, AccessRestrictionTest · `acc-v` AdminPinViewTests |
| RNF-12 | Rastro de operaciones | ✅ | `inv` StockMovementModelTests · `inv-v` StockFormTests.test_valid_purchase_adds_stock_in_the_admins_name_and_refreshes · `pos` CashSessionServiceTests.test_admin_opens_the_session_in_their_name, SaleServiceTests.test_offline_sale_keeps_its_uuid_and_device_time_and_is_applied_once, QuarantineResolutionTests.test_only_an_active_admin_resolves_and_only_once |
| RNF-13 | Confidencialidad de reportes | ✅ | `rep-v` AccessTests · `core` RoleRequiredTests.test_cashier_is_rejected_from_admin_only_view |
| RNF-14 | Modularidad | ✋ | Apps `accounts`, `catalog`, `inventory`, `pos` y `reports` con capas `views` → `services` → `models`. |

#### B.3 Reglas de negocio (sección 1.3.2)

| # | Regla | Pruebas |
|---|---|---|
| 1 | El inventario se descuenta al llegar la venta al servidor, en la misma transacción | `inv` DeductForSaleTests.test_follows_the_recipe_times_the_units, .test_same_sale_is_deducted_only_once · `pos` SaleServiceTests.test_online_sale_records_what_was_charged_and_deducts_inventory · `e2e` SaleWithoutNetworkTests (sin descuento hasta sincronizar) |
| 2 | Las personalizaciones ajustan el descuento | `inv` DeductForSaleTests.test_removed_ingredient_is_not_deducted, .test_extra_deducts_its_quantity_per_unit · `pos-v` OrderSummaryTests.test_modifiers_dialog_and_price |
| 3 | Alerta visual con `existencia <= min_stock` | `inv` PurchaseWasteAndAlertTests.test_alert_when_stock_reaches_the_minimum · `inv-v` IngredientListTests.test_level_follows_rule_3 · `pos-v` OrderBuilderTests.test_low_stock_shows_the_alert |
| 4 | Solo efectivo o transferencia | `pos` SaleServiceTests.test_malformed_order_or_payment_method · `pos-v` OrderSummaryTests.test_payment_method_selected_by_server, .test_invalid_payment_method_is_retargeted_to_messages |
| 5 | El corte se niega con ventas sin sincronizar; la diferencia no bloquea | `pos` CashSessionServiceTests.test_close_is_refused_with_unsynced_sales, .test_close_records_the_difference_without_blocking · `pos-v` CloseSessionTests.test_pending_operations_are_409_in_the_dialog · `rep-v` CashTests.test_pending_operations_are_shown_in_the_close_card · `e2e` CashCloseTests |
| 6 | Precios, recetas y mínimos solo del Administrador | `cat-v` AccessTests · `inv-v` AccessTests · `core` RoleRequiredTests.test_cashier_is_rejected_from_admin_only_view, AdminPinRequiredTests |
| 7 | Venta inmutable; se corrige con ajuste o cancelación; dos marcas de tiempo | `pos` SaleAdjustmentTests, SaleServiceTests.test_offline_sale_keeps_its_uuid_and_device_time_and_is_applied_once, .test_adjust_units_of_a_line_and_then_cancel_the_rest, .test_sale_of_a_closed_session_cannot_be_changed |
| 8 | UUID por operación; unicidad en la base de datos | `pos` SaleTests.test_uuid_is_unique, CashRegisterSessionTests.test_uuid_is_unique, QuarantinedOperationTests.test_uuid_is_unique, SyncOperationsTests.test_the_same_batch_twice_applies_once, .test_a_uuid_already_used_in_another_table_is_a_duplicate · `e2e` SaleWithoutNetworkTests |
| 9 | Cuarentena en lugar de rechazo, con tres salidas | `pos` SyncOperationsTests.test_quarantine_reasons, SaleServiceTests.test_quarantine_reasons, QuarantineResolutionTests, SalesAdminTests.test_quarantine_actions |
| 10 | Existencia negativa se registra y se marca | `inv` DeductForSaleTests.test_stock_may_go_negative_and_is_reported, PurchaseWasteAndAlertTests.test_waste_may_leave_stock_negative · `pos` SaleServiceTests.test_negative_stock_is_kept_and_marked_for_review, SyncOperationsTests.test_review_reasons |
| 11 | El motivo del ajuste decide qué se revierte | `pos` SaleServiceTests.test_cancel_for_capture_error_gives_money_and_inventory_back, .test_cancel_for_return_records_waste_and_keeps_stock, .test_payment_correction_only_moves_the_sale_to_the_other_method · `inv` DeductForSaleTests.test_revert_gives_the_stock_back_as_an_adjustment, .test_return_records_the_ingredients_as_waste_without_changing_stock · `rep` ReportServiceTests.test_sales_by_period_nets_cancellations_and_payment_corrections |
| 12 | Toda venta requiere turno abierto, validado antes de calcular | `pos` SaleServiceTests.test_needs_an_open_session_and_checks_it_before_pricing, CashSessionServiceTests.test_require_open_session · `pos-v` OrderSummaryTests.test_add_item_without_open_cash_is_409, ConfirmSaleTests.test_closed_cash_is_409 |
| 13 | Un turno por jornada, solo el Administrador lo abre o cierra, también sin red | `pos` CashSessionServiceTests.test_admin_opens_the_session_in_their_name, .test_cashier_cannot_open_or_close, .test_only_one_session_per_day, .test_offline_opening_keeps_its_uuid_and_device_time, CashRegisterSessionTests · `pos-v` OpenSessionTests.test_second_session_of_the_day_is_422 · `node` test_pin_verifier · `e2e` OpeningTests |
| 14 | Manda lo cobrado; si no cuadra con sus líneas, cuarentena | `pos` SaleServiceTests.test_what_was_charged_wins_over_the_current_catalog, .test_quarantine_reasons (`total_inconsistente`), QuarantineResolutionTests.test_apply_uses_the_current_catalog_and_keeps_what_was_charged, SyncOperationsTests.test_review_reasons |

#### B.4 Pruebas por módulo

| Módulo | Servicios, modelos y acceso (`tests.py`) | Vistas (`tests_views.py`) | Otras |
|---|---:|---:|---|
| Usuarios (`accounts`, `core`) | 72 | 18 | 4 en Node (verificador del PIN) |
| Productos (`catalog`) | 25 | 23 | — |
| Inventario (`inventory`) | 29 | 15 | — |
| Punto de venta y turno (`pos`) | 102 | 52 | Paridad de precios en Node · 9 E2E |
| Reportes (`reports`) | 7 | 19 | — |
| **Total** | **235** | **127** | 362 de Django, 9 E2E y 31 de Node |

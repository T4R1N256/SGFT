# SGFT — Sistema de Gestión de FoodTruck

Sistema web de gestión administrativa y operativa desarrollado para el foodtruck **"El Pardo"**.

> **Estado del proyecto:**
>   - Levantamiento y análisis de requisitos completado.
>   - En proceso de diseño de arquitectura y planificación del Product Backlog.

---

## Tabla de contenido

- [Descripción general](#descripción-general)
- [Contexto del negocio](#contexto-del-negocio)
- [Problemática](#problemática)
- [Objetivos](#objetivos)
- [Alcance del proyecto](#alcance-del-proyecto)
- [Módulos del sistema](#módulos-del-sistema)
- [Roles de usuario](#roles-de-usuario)
- [Metodología de trabajo](#metodología-de-trabajo)
- [Fases y entregables](#fases-y-entregables)
- [Equipo de trabajo](#equipo-de-trabajo)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Stack tecnológico](#stack-tecnológico)
- [Documentación](#documentación)
- [Referencias](#referencias)
- [Licencia](#licencia)

---

## Descripción general

**SGFT (Sistema de Gestión de FoodTruck)** es una solución tecnológica diseñada para optimizar la administración operativa, el control de inventarios y el punto de venta en negocios gastronómicos de formato móvil. El sistema busca transformar la toma de decisiones del negocio mediante la digitalización de sus procesos clave: registro de ventas, control de insumos, gestión de accesos y generación de reportes financieros.

El proyecto se desarrolla como una plataforma web responsiva, accesible desde cualquier dispositivo con navegador (computadora, tablet o teléfono), con el fin de facilitar su uso dentro de un establecimiento móvil sin requerir infraestructura costosa ni equipos especializados.

## Contexto del negocio

**"El Pardo"** es un foodtruck fundado en 2026 en Ciudad Juárez, Chihuahua, especializado en burritos tradicionales, desayunos al gusto y guisados por porción, complementado con bebidas. Opera con una estructura reducida de tres colaboradores (cocina, atención al cliente y cobro/compras) y se ubica en el corredor comercial de la Av. Vicente Guerrero, zona de alta demanda impulsada por el Hospital General Regional No. 2 del IMSS.

El análisis de mercado identificó que la totalidad de la competencia directa en la zona (puestos de burritos) opera de forma informal, con cobro únicamente en efectivo/transferencia y sin sistemas de punto de venta ni presencia digital, dejando una oportunidad de diferenciación para "El Pardo" mediante la tecnificación de su operación.

## Problemática

Actualmente, "El Pardo" gestiona sus operaciones de forma manual (registro de pedidos en cuaderno, conteo visual de inventario, cálculo mental de compras y cierre de caja aritmético), lo que genera:

- Inconsistencias en el rastreo de insumos en tiempo real.
- Riesgo de desabasto o merma de materia prima.
- Nula visibilidad sobre márgenes de ganancia y desempeño de productos.
- Mayor tiempo de atención al cliente y probabilidad de error humano en cobros y pedidos.

## Objetivos

### Objetivo general

Desarrollar e implementar un sistema web para la gestión administrativa del foodtruck "El Pardo" durante el semestre, mediante la integración de módulos de punto de venta, inventario, usuarios y reportes, con el fin de optimizar la atención al cliente y el control del negocio.

### Objetivos específicos

- **Punto de Venta:** construir un módulo intuitivo que permita registrar pedidos, cobros y personalizaciones de platillos, reduciendo el tiempo de toma de orden.
- **Gestión de Inventario:** desarrollar un módulo que descuente automáticamente los insumos en cada venta e identifique niveles críticos de stock para evitar mermas.
- **Gestión de Usuarios:** implementar control de accesos por roles que restrinja funciones según el perfil del usuario.
- **Reportes:** implementar un módulo de reportes financieros que registre ingresos y egresos diarios para facilitar el análisis de ventas.

## Alcance del proyecto

### Dentro del alcance

- Desarrollo de un sistema web responsivo accesible desde navegador para registro de ventas, administración de insumos, usuarios y reportes.
- Modelado de recetas para el descuento automático de ingredientes en cada venta.
- Registro de cobros en efectivo o transferencia.
- Pruebas funcionales de cada módulo implementado y documentación técnica (SRS, diagramas de procesos y manuales).

### Fuera del alcance

- Integración con pasarelas de pago bancarias o procesamiento directo de tarjetas de crédito/débito.
- Adquisición, donación o configuración de hardware (computadoras, tabletas, impresoras térmicas, infraestructura de red).
- Mantenimiento técnico, soporte o actualización del software posterior a la finalización del semestre académico.

## Módulos del sistema

| Módulo | Descripción |
|---|---|
| **Punto de Venta** | Registro rápido de pedidos a partir de un catálogo de productos con precios, personalización de platillos (agregar/retirar ingredientes), cálculo del total y registro del cobro (efectivo o transferencia). |
| **Gestión de Inventario** | Descuento automático de insumos según receta en cada venta, definición de niveles mínimos de stock por insumo y alertas visuales al alcanzar niveles críticos. |
| **Gestión de Usuarios** | Administración de cuentas y roles con permisos diferenciados, restringiendo el acceso a funciones sensibles como la modificación del inventario. |
| **Reportes** | Registro de ingresos y egresos diarios, automatización del cierre de caja y reportes de productos más vendidos para apoyar la toma de decisiones. |

## Roles de usuario

| Rol | Permisos principales |
|---|---|
| **Administrador** | Acceso completo: gestión de inventario, usuarios, reportes y supervisión general del negocio. |
| **Cajero** | Toma de pedidos, personalización de órdenes y registro de cobros. |
| **Cocinero** | Consulta de órdenes para la preparación de alimentos. |

## Metodología de trabajo

El proyecto combina prácticas de ingeniería de requisitos con un marco de trabajo ágil:

1. **Levantamiento de requisitos:** entrevista directa con el dueño del negocio para identificar procesos, problemas y necesidades.
2. **Especificación de requisitos:** documentación clara y sin ambigüedades para evitar retrabajo y desalineación con las necesidades reales del cliente.
3. **Modelado de procesos:** diagramas de flujo de los procesos actuales del negocio para identificar pasos redundantes y áreas críticas.
4. **Desarrollo ágil (Scrum):** el desarrollo se organiza en *sprints* de dos semanas, permitiendo entregas incrementales, retroalimentación continua del cliente y ajustes progresivos del Product Backlog.

## Fases y entregables

| # | Fase | Descripción |
|---|---|---|
| 1 | **Levantamiento y análisis de requisitos** | Entrevista al dueño del negocio, identificación de necesidades, diagramas de proceso preliminares y documentación de requisitos. |
| 2 | **Diseño de arquitectura y planificación del Backlog** | Definición de la arquitectura del sistema, prototipos de interfaz, criterios de aceptación y priorización de historias de usuario por sprint. |
| 3 | **Desarrollo modular** | Codificación iterativa (semanal) de interfaz, lógica de negocio y base de datos para cada módulo (POS, Inventario, Usuarios, Reportes). |
| 4 | **Pruebas, validación y cierre** | Pruebas funcionales, integración del sistema, corrección de errores según retroalimentación del cliente y entrega de documentación técnica. |

### Entregables principales

**Documentales**
- Documento de Fases (información de la empresa, carta de apertura, minutas de trabajo y anexos).
- Diagramas de procesos propuestos.
- Documento de Especificación de Requisitos de Software (SRS) y Product Backlog.

**De software**
- Sistema web funcional y responsivo que integra los módulos de Punto de Venta, Gestión de Inventario, Control de Accesos y Reportes diarios.

## Equipo de trabajo

| Integrante | Rol | Responsabilidad |
|---|---|---|
| Diego Adrián Galindo Mora | Product Owner / Analista de requisitos | Representar las necesidades del cliente, priorizar el backlog, realizar entrevistas y documentar requisitos. |
| Alejandro Tarin Gutiérrez | Scrum Master / Desarrollador | Facilitar los eventos de Scrum, apoyar la organización del equipo, resolver impedimentos y participar en el desarrollo front-end. |
| Jesús Eduardo Hernández Garrido | Analista de requisitos / Desarrollador | Analizar necesidades, apoyar la documentación de requisitos y participar en el desarrollo back-end. |
| Jared Gustavo Beltrán Herrada | Desarrollador / Tester | Apoyar el desarrollo back-end, diseñar y ejecutar pruebas funcionales. |
| Cesar Yahir Enriquez Jasso | Desarrollador / Tester | Apoyar la programación back-end y realizar pruebas sobre los módulos implementados. |

**Docente asesor:** Mtro. Abraham López Nájera

## Estructura del repositorio

> Estructura sugerida; ajustar conforme avance el desarrollo del sistema.

```
SGFT/
├── docs/                  # Documentación del proyecto (SRS, minutas, diagramas)
├── backend/                # Lógica de negocio, API y base de datos
├── frontend/                # Interfaz de usuario (web responsiva)
├── tests/                  # Pruebas funcionales por módulo
└── README.md
```

## Stack tecnológico

> El stack tecnológico definitivo fue acordado por el equipo durante la fase de definición de arquitectura. Completar esta sección con el detalle de lenguajes, frameworks y motor de base de datos seleccionados.

- **Frontend:** _por documentar_
- **Backend:** _por documentar_
- **Base de datos:** _por documentar_
- **Compatibilidad:** aplicación web responsiva, accesible desde cualquier dispositivo con navegador (incluyendo iOS).

## Documentación

La documentación completa del proyecto (información de la empresa, análisis de mercado, carta de apertura, minutas de trabajo y anexos) se encuentra en la carpeta [`docs/`](./docs).

## Referencias

1. A. Cisneros, "Ejemplos de Estudios de Mercado," scribd.com, ago. 2011. [En línea]. Disponible: https://www.scribd.com/doc/62644748/Ejemplo-Estudio-de-Mercado
2. Deep Market Insights, "Mexico Food Trucks Market Size, Share & Trends Report By 2034," deepmarketinsights.com, mar. 2026. [En línea]. Disponible: https://deepmarketinsights.com/vista/insights/food-trucks-market/mexico
3. Ingeniería de Software de Élite, "03 - Ingeniería de Requerimientos - Recolección de requerimientos," YouTube, 31 mar. 2021. [En línea]. Disponible: https://www.youtube.com/watch?v=73fuqZ78uhg
4. J. Martins, "Qué es Scrum: marco ágil, sprints, roles y artefactos," Asana, 9 abr. 2026. [En línea]. Disponible: https://asana.com/es/resources/what-is-scrum?exp=mm
5. Miro, "¿Qué es un diagrama de flujo de proceso? | Guía Completa," miro.com. [En línea]. Disponible: https://miro.com/es/diagrama-de-flujo/que-es-diagrama-flujo-proceso/

## Licencia

Proyecto académico desarrollado para la Universidad Autónoma de Ciudad Juárez (UACJ). Uso educativo — sin licencia comercial definida.

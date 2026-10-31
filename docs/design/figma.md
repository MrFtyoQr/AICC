# Figma

Equipo: *Joseph Quintana's team* (plan Starter). Los diagramas viven en FigJam y se regeneran desde el texto
Mermaid de este repo cuando cambia la arquitectura, para que Figma y el código nunca se contradigan.

## Diagramas (FigJam)

| Diagrama | Enlace | Fuente en el repo |
|---|---|---|
| Arquitectura | [AICC - Arquitectura](https://www.figma.com/board/1nE8TRKOzUToUPykwVS8jk) | README · [orquestacion.md](../architecture/orquestacion.md) |
| Ciclo de vida de una tarea | [AICC - Ciclo de vida de una tarea](https://www.figma.com/board/NWzvNxu4btMJWoaVJTxCKu) | [orquestacion.md §3](../architecture/orquestacion.md) |
| Flujo UX "pedir y aprobar" | [AICC - Flujo UX pedir y aprobar](https://www.figma.com/board/Zj8p93tqmKJmPEhVbEHn6A) | [principios-ux.md §3](../ux/principios-ux.md) |
| Roadmap de sprints | [AICC - Roadmap de sprints Etapa A](https://www.figma.com/board/RG7J9hLReprlflqXm6LRiE) | [sprints.md](../planning/sprints.md) |
| Los 3 caminos (Conectar, BYOC, Administrado) | [AICC - Los 3 caminos](https://www.figma.com/board/BFKDHkxOWHG04OCguE8X9H) | [modelo-operacion.md §3](../architecture/modelo-operacion.md) |
| Receta estándar (pasos administrables) | [AICC - Receta estándar](https://www.figma.com/board/nbt8z29egWprfJiKZrslDE) | [modelo-operacion.md §4](../architecture/modelo-operacion.md) |
| Camino Conectar (OpenClaw, n8n, Hermes, a medida) | [AICC - Camino Conectar](https://www.figma.com/board/NDb60yjgBfmfNaiN6iCjjP) | [modelo-operacion.md §3A](../architecture/modelo-operacion.md) |
| AICC como intermediario entre cliente y nubes | [AICC - Intermediario y nubes](https://www.figma.com/board/HdWIVgaLZbrGTfnnAguGCG) | [ADR-019](../decisions/ADR-019-nube-estandar.md) |

> La primera vez que abras cada enlace, Figma te pide **reclamarlo** ("claim") para guardarlo en tus borradores.
> Hazlo con los ocho; después muévelos a un proyecto `AICC` dentro del equipo.

## Pantallas (Figma Design)

Proceso por incremento (ver [principios-ux.md §7](../ux/principios-ux.md)): flujo → wireframe → prototipo →
revisión → ticket `APP`. Las pantallas de M0 y M1 ya existen en código; sus capturas del emulador son la
referencia hasta pasarlas a Figma.

| Incremento | Pantallas | Estado en Figma |
|---|---|---|
| M0 | Estado de conexión | Pendiente (capturas en el PR #1) |
| M1 | Login, registro, inicio provisional | Pendiente (capturas en el PR #2) |
| M2 | Chip de contexto, selector, actividad | En código (S3); capturas del emulador en el PR de S3. Pasar a Figma cuando el asiento lo permita |
| M3 | Command Center, tarjeta de tarea, lista | En código (S4); capturas del emulador en el PR de S4. Pasar a Figma cuando el asiento lo permita |

Limitación actual: tu asiento en el plan Starter es de tipo **View**, así que crear y editar archivos de diseño
puede estar restringido (FigJam sí funciona). Si hace falta editar pantallas desde aquí, habrá que cambiar el
asiento a **Full/Dev** o crear los archivos en tus borradores.

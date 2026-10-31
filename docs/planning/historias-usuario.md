# Historias de usuario (Etapa A)

Cada historia agrupa tareas técnicas del [plan maestro](plan-maestro.md) (códigos `F0-BE-01`…) y se entrega
completa en un sprint. Calendario en [sprints.md](sprints.md). Este archivo **es fuente** del backlog de Jira:
`python -I scripts/generar-backlog-jira.py` crea Epic → Historia → Subtarea a partir de aquí y del plan maestro.

**Formato obligatorio** (lo lee el generador): encabezado `### HU-NN · Título`, líneas `- **Campo:** valor`,
y criterios numerados en formato *Dado / cuando / entonces*.

**Roles**

| Rol | Quién es |
|---|---|
| Dueño de negocio | Usuario final; describe objetivos y aprueba gastos |
| Operador | Miembro del workspace que ejecuta y vigila tareas |
| Administrador | Dueño o admin del workspace; gestiona miembros, reglas y presupuestos |
| Equipo AICC | Quien desarrolla y opera la plataforma |

**Puntos:** Fibonacci (1, 2, 3, 5, 8, 13). Una historia de más de 8 puntos se divide.

---

## Epic F0 · Fundamentos

### HU-01 · Entorno reproducible en cualquier equipo
- **Rol:** Equipo AICC
- **Historia:** Como integrante del equipo quiero clonar el repo y levantar la infraestructura con un comando para empezar a trabajar sin configuración manual.
- **Fase:** F0
- **Sprint:** S0
- **Puntos:** 3
- **Prioridad:** Highest
- **Estado:** Done
- **Tareas:** F0-OPS-01, F0-OPS-03, F0-OPS-04, F0-OPS-06, F0-DOC-01

**Criterios de aceptación**
1. Dado un clon limpio, cuando ejecuto `docker compose up -d`, entonces PostgreSQL y Redis quedan *healthy*.
2. Dado el repositorio, cuando busco secretos, entonces solo existe `.env.example` con valores ficticios.
3. Dado un cambio de fase, cuando ejecuto `scripts/medir-entorno.sh`, entonces obtengo una medición comparable con la línea base.

### HU-02 · API observable
- **Rol:** Operador
- **Historia:** Como operador quiero saber si la API y sus dependencias están vivas y rastrear cada petición para diagnosticar problemas rápido.
- **Fase:** F0
- **Sprint:** S0
- **Puntos:** 5
- **Prioridad:** Highest
- **Estado:** Done
- **Tareas:** F0-BE-01, F0-BE-02, F0-BE-04, F0-BE-05

**Criterios de aceptación**
1. Dado que la API corre, cuando llamo `GET /health`, entonces recibo 200 con versión y entorno.
2. Dado que Redis o PostgreSQL no responden, cuando llamo `GET /health/ready`, entonces recibo 503 indicando cuál falla, sin exponer hosts ni credenciales.
3. Dada cualquier petición, cuando recibo la respuesta, entonces trae `X-Request-ID` y el log JSON tiene el mismo id.
4. Dado que falta `DATABASE_URL`, cuando arranca la API, entonces falla con un mensaje que nombra la variable.

### HU-03 · Esquema versionado y contrato publicado
- **Rol:** Equipo AICC
- **Historia:** Como desarrollador quiero migraciones controladas y un contrato OpenAPI versionado para que la app y la API no se desincronicen.
- **Fase:** F0
- **Sprint:** S0
- **Puntos:** 3
- **Prioridad:** High
- **Estado:** Done
- **Tareas:** F0-BE-03, F0-BE-06

**Criterios de aceptación**
1. Dada una base vacía, cuando ejecuto `alembic upgrade head`, entonces queda en la última revisión.
2. Dado un cambio en la API, cuando olvido regenerar `shared/contracts/openapi.json`, entonces una prueba falla.

### HU-04 · Ver si la app está conectada
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero abrir la app y ver de inmediato si AICC está listo para saber si puedo trabajar.
- **Fase:** F0
- **Sprint:** S0
- **Puntos:** 5
- **Prioridad:** High
- **Estado:** Done
- **Tareas:** F0-APP-01, F0-APP-02, F0-APP-03, F0-UX-01, F0-UX-02

**Criterios de aceptación**
1. Dada la API sana, cuando abro la app, entonces veo "AICC está listo" con el estado de cada dependencia.
2. Dada una dependencia caída, cuando reviso, entonces veo "Funcionando a medias" y cuál falla.
3. Dada la API apagada, cuando abro la app, entonces veo un mensaje humano y un botón para reintentar, sin que la app se congele.
4. Dado el tema oscuro del sistema, cuando abro la app, entonces todos los estados se leen con contraste suficiente.

### HU-05 · Calidad automática en cada cambio
- **Rol:** Equipo AICC
- **Historia:** Como desarrollador quiero que cada PR ejecute lint, pruebas y escaneo de secretos para que nada roto o inseguro llegue a `main`.
- **Fase:** F0
- **Sprint:** S1
- **Puntos:** 5
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** F0-OPS-02, F0-OPS-05

**Criterios de aceptación**
1. Dado un PR, cuando se abre o actualiza, entonces corren los jobs de backend (ruff, pytest con PostgreSQL y Redis, contrato) y mobile (format, analyze, test).
2. Dado un secreto en el diff, cuando corre la CI, entonces el job de secretos falla.
3. Dado `main`, cuando alguien intenta empujar sin PR o con CI roja, entonces GitHub lo impide (o, si el plan no lo permite, queda documentada la alternativa).

### HU-06 · Crear cuenta e iniciar sesión
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero registrarme e iniciar sesión con email y contraseña para acceder a mi información de forma segura.
- **Fase:** F0
- **Sprint:** S1
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** F0-SEC-01

**Criterios de aceptación**
1. Dado un email nuevo, cuando me registro con una contraseña válida, entonces se crea mi cuenta y la contraseña se guarda solo como hash Argon2id.
2. Dadas credenciales válidas, cuando inicio sesión, entonces recibo un access token de 15 min y un refresh token.
3. Dado un refresh token válido, cuando lo uso, entonces recibo un par nuevo y el anterior queda revocado.
4. Dado un refresh token ya usado, cuando alguien lo reutiliza, entonces se revoca toda la familia de tokens.
5. Dadas credenciales inválidas, cuando intento entrar, entonces recibo el mismo error genérico exista o no el email.

### HU-07 · API protegida contra abuso
- **Rol:** Administrador
- **Historia:** Como responsable de la plataforma quiero límites de tamaño, frecuencia y origen para que la API resista abusos básicos.
- **Fase:** F0
- **Sprint:** S1
- **Puntos:** 3
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** F0-SEC-02

**Criterios de aceptación**
1. Dado un cuerpo mayor al límite, cuando lo envío, entonces recibo 413.
2. Dados demasiados intentos de login desde el mismo origen, cuando supero el límite, entonces recibo 429 con `Retry-After`.
3. Dado un origen no permitido, cuando un navegador llama la API, entonces CORS lo bloquea.

### HU-08 · Iniciar sesión desde el móvil
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero iniciar sesión en la app y que recuerde mi sesión de forma segura para no escribir mi contraseña cada vez.
- **Fase:** F0
- **Sprint:** S1
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** F0-APP-04

**Criterios de aceptación**
1. Dado que no tengo sesión, cuando abro la app, entonces veo la pantalla de inicio de sesión con opción de registrarme.
2. Dadas credenciales correctas, cuando entro, entonces llego a la pantalla principal y los tokens quedan en almacenamiento seguro del sistema.
3. Dado un access token vencido, cuando la app llama la API, entonces lo renueva sola sin que yo lo note.
4. Dado que cierro sesión, cuando vuelvo a abrir la app, entonces me pide iniciar sesión.

---

## Epic F1 · Identidad y Workspace

### HU-09 · Mi espacio de trabajo listo al registrarme
- **Rol:** Dueño de negocio
- **Historia:** Como usuario nuevo quiero tener un espacio de trabajo con un proyecto inicial para empezar sin configurar nada.
- **Fase:** F1
- **Sprint:** S2
- **Puntos:** 5
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** F1-BE-01, F1-BE-02

**Criterios de aceptación**
1. Dado que me registro, cuando entro por primera vez, entonces tengo un workspace personal, un proyecto "General" y un ambiente `development`.
2. Dado el esquema, cuando aplico y revierto la migración, entonces ambas operaciones funcionan.

### HU-10 · Nadie ve los datos de otro workspace
- **Rol:** Administrador
- **Historia:** Como dueño de un negocio quiero la garantía de que ningún otro usuario puede ver o tocar mis datos para confiar en la plataforma.
- **Fase:** F1
- **Sprint:** S2
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** F1-SEC-01, F1-SEC-03, F1-DOC-01

**Criterios de aceptación**
1. Dado un workspace ajeno, cuando envío su id en `X-Workspace-Id`, entonces recibo 404 (no 403, para no revelar que existe).
2. Dados dos usuarios con datos, cuando corre la suite de aislamiento, entonces ninguno puede listar, leer, modificar ni borrar recursos del otro.
3. Dada la CI, cuando cualquier PR toca el backend, entonces la suite de aislamiento corre siempre.

### HU-11 · Roles y permisos por miembro
- **Rol:** Administrador
- **Historia:** Como administrador quiero asignar roles (owner, admin, operator, viewer) para controlar qué puede hacer cada persona.
- **Fase:** F1
- **Sprint:** S2
- **Puntos:** 5
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** F1-SEC-02

**Criterios de aceptación**
1. Dado un viewer, cuando intenta una acción de escritura, entonces recibe 403.
2. Dada la matriz de permisos documentada, cuando corren las pruebas, entonces cada rol y acción coincide con la matriz.

### HU-12 · Gestionar workspaces, proyectos, ambientes y miembros
- **Rol:** Administrador
- **Historia:** Como administrador quiero crear y organizar proyectos, ambientes y miembros para separar cada iniciativa de negocio.
- **Fase:** F1
- **Sprint:** S3
- **Puntos:** 8
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** F1-BE-04

**Criterios de aceptación**
1. Dado mi workspace, cuando creo un proyecto, entonces nace con ambiente `development`.
2. Dado un email, cuando invito a alguien, entonces queda una invitación pendiente con rol asignado (sin envío de email todavía).
3. Dado el contrato OpenAPI, cuando reviso, entonces todos los endpoints CRUD están documentados.

### HU-13 · Registro de actividad
- **Rol:** Administrador
- **Historia:** Como administrador quiero ver quién hizo qué y cuándo para tener trazabilidad completa.
- **Fase:** F1
- **Sprint:** S3
- **Puntos:** 5
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** F1-BE-03, F1-APP-02

**Criterios de aceptación**
1. Dada cualquier acción de escritura, cuando termina, entonces existe un registro de auditoría con actor, acción, recurso y resultado.
2. Dado el registro, cuando lo reviso, entonces no contiene contraseñas, tokens ni secretos.
3. Dada la app, cuando abro Actividad, entonces veo la lista paginada en lenguaje claro.

### HU-14 · Saber y cambiar el contexto en un toque
- **Rol:** Operador
- **Historia:** Como operador quiero ver siempre en qué workspace, proyecto y ambiente estoy y cambiarlo en un toque para no equivocarme de lugar.
- **Fase:** F1
- **Sprint:** S3
- **Puntos:** 5
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** F1-APP-01, F1-UX-01

**Criterios de aceptación**
1. Dada cualquier pantalla, cuando la miro, entonces veo el chip de contexto arriba.
2. Dado el ambiente `production`, cuando lo selecciono, entonces el chip se distingue en rojo.
3. Dado el chip, cuando lo toco, entonces un panel inferior me deja cambiar de contexto.

---

## Epic O1 · Tareas

### HU-15 · Pedir algo con mis palabras
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero escribir lo que necesito en lenguaje natural para crear una tarea sin formularios complicados.
- **Fase:** O1
- **Sprint:** S4
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** O1-BE-01, O1-BE-04, O1-APP-01, O1-UX-01

**Criterios de aceptación**
1. Dado el Command Center, cuando escribo y envío, entonces se crea una tarea en Borrador en menos de 3 toques.
2. Dada una tarea creada, cuando la abro, entonces veo su detalle y puedo cancelarla.

### HU-16 · Estados claros y confiables
- **Rol:** Operador
- **Historia:** Como operador quiero que cada tarea tenga un estado preciso y su historial para confiar en lo que veo.
- **Fase:** O1
- **Sprint:** S4
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** O1-BE-02, O1-BE-03, O1-BE-05, O1-UX-02

**Criterios de aceptación**
1. Dada una transición no permitida, cuando se intenta, entonces se rechaza con error.
2. Dada cualquier transición, cuando ocurre, entonces se registran evento y auditoría en la misma transacción.
3. Dadas dos modificaciones simultáneas, cuando la segunda llega, entonces recibe 409.
4. Dado cualquier estado, cuando se muestra al usuario, entonces usa el texto del diccionario de estados.

### HU-17 · Ver y filtrar mis tareas
- **Rol:** Operador
- **Historia:** Como operador quiero ver mis tareas filtradas por estado para saber qué necesita atención.
- **Fase:** O1
- **Sprint:** S4
- **Puntos:** 3
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** O1-APP-02

**Criterios de aceptación**
1. Dada la lista, cuando filtro por estado, entonces solo veo esas tareas.
2. Dado cada estado, cuando se muestra, entonces lleva color, icono y texto.

---

## Epic O2 · Planner

### HU-18 · Catálogo de capacidades
- **Rol:** Equipo AICC
- **Historia:** Como equipo quiero un catálogo declarativo de lo que AICC sabe hacer, con su esquema y riesgo, para que el planner solo use acciones conocidas.
- **Fase:** O2
- **Sprint:** S5
- **Puntos:** 5
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** O2-BE-01

**Criterios de aceptación**
1. Dado `GET /capabilities`, cuando lo llamo, entonces veo cada capacidad con esquema de entrada y nivel de riesgo.
2. Dada una capacidad nueva, cuando se registra sin esquema, entonces el arranque falla.

### HU-19 · Motor de IA intercambiable y probable
- **Rol:** Equipo AICC
- **Historia:** Como equipo quiero una interfaz única para proveedores de IA y un motor falso determinista para probar sin red ni costo.
- **Fase:** O2
- **Sprint:** S5
- **Puntos:** 5
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** O2-BE-02, O2-BE-03

**Criterios de aceptación**
1. Dada la suite de pruebas, cuando corre, entonces no hace llamadas de red a proveedores.
2. Dado el proveedor real, cuando se usa, entonces la clave solo existe en el backend.

### HU-20 · Recibir un plan estructurado
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero que AICC convierta mi pedido en un plan de pasos para entender qué se hará antes de hacerlo.
- **Fase:** O2
- **Sprint:** S5
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** O2-BE-04, O2-BE-06, O2-DOC-01

**Criterios de aceptación**
1. Dada una tarea en Borrador, cuando pido plan, entonces recibo un plan versionado con pasos, supuestos y dependencias.
2. Dado un plan, cuando se guarda, entonces nada se ejecuta.

### HU-21 · Planes siempre válidos y seguros
- **Rol:** Administrador
- **Historia:** Como administrador quiero que ningún plan inválido o manipulado llegue a mostrarse para que la IA no pueda saltarse las reglas.
- **Fase:** O2
- **Sprint:** S6
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** O2-BE-05, O2-SEC-01

**Criterios de aceptación**
1. Dado un plan con una capacidad inexistente, un ciclo o entradas inválidas, cuando se valida, entonces se rechaza con razón legible.
2. Dado un texto con instrucciones maliciosas, cuando se planifica, entonces no altera reglas, riesgos ni costos (casos documentados).
3. Dadas 20 descripciones de prueba, cuando se planifican, entonces el 100 % son válidas o se rechazan con razón.

### HU-22 · Ver el plan y su costo antes de decidir
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero ver los pasos en lenguaje natural y el costo estimado para decidir con información.
- **Fase:** O2
- **Sprint:** S6
- **Puntos:** 8
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** O2-BE-07, O2-APP-01, O2-UX-01

**Criterios de aceptación**
1. Dado un plan, cuando lo abro, entonces veo cada paso en lenguaje claro con su detalle técnico plegado.
2. Dado un plan, cuando lo reviso, entonces veo costo estimado, moneda, fecha de la tarifa y supuestos.

---

## Epic O3 · Políticas y aprobaciones

### HU-23 · Reglas que deciden qué requiere aprobación
- **Rol:** Administrador
- **Historia:** Como administrador quiero reglas deterministas que permitan, nieguen o pidan aprobación para controlar el riesgo sin depender de la IA.
- **Fase:** O3
- **Sprint:** S7
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** O3-BE-01, O3-BE-02, O3-DOC-01

**Criterios de aceptación**
1. Dado un paso, cuando se evalúa, entonces recibe allow, deny o require_approval con la regla aplicada y una razón.
2. Dada una regla de workspace, cuando intenta permitir acciones destructivas, entonces se rechaza.

### HU-24 · Aprobar, rechazar o pedir cambios
- **Rol:** Dueño de negocio
- **Historia:** Como responsable quiero aprobar, rechazar o pedir cambios a un plan para que nada sensible ocurra sin mi decisión.
- **Fase:** O3
- **Sprint:** S7
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** O3-BE-03, O3-BE-04, O3-SEC-01

**Criterios de aceptación**
1. Dado un plan con pasos de envío o gasto, cuando no hay aprobación registrada, entonces no puede pasar a Aprobada.
2. Dado "pedir cambios", cuando lo uso, entonces se genera la versión 2 conservando la 1.
3. Dado un viewer, cuando intenta aprobar, entonces recibe 403.

### HU-25 · Bandeja de decisiones en el móvil
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero una bandeja con todo lo que espera mi decisión para resolverlo en segundos.
- **Fase:** O3
- **Sprint:** S7
- **Puntos:** 5
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** O3-APP-01, O3-APP-02, O3-UX-01

**Criterios de aceptación**
1. Dadas decisiones pendientes, cuando miro la navegación, entonces la pestaña Aprobar muestra el número.
2. Dada una aprobación, cuando la abro, entonces responde qué pasará, cuánto cuesta y si se puede deshacer.
3. Dada una acción de gasto o envío externo, cuando apruebo, entonces debo deslizar para confirmar.

---

## Epic O4 · Ejecución en vivo

### HU-26 · Ejecución fuera de la app
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero que mis tareas aprobadas sigan ejecutándose aunque cierre la app.
- **Fase:** O4
- **Sprint:** S8
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** O4-BE-01, O4-BE-02, O4-OPS-01

**Criterios de aceptación**
1. Dada una tarea aprobada, cuando se encola, entonces el worker la ejecuta sin que la app esté abierta.
2. Dado un paso que falla por error transitorio, cuando es idempotente, entonces se reintenta con espera creciente.
3. Dado el gate, cuando se mide, entonces queda registrada la latencia de encolado y la RAM del worker.

### HU-27 · Ejecución paso a paso con controles
- **Rol:** Operador
- **Historia:** Como operador quiero que cada paso se revalide antes de ejecutarse y que se pause si necesita algo de mí.
- **Fase:** O4
- **Sprint:** S8
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** O4-BE-03, O4-BE-04

**Criterios de aceptación**
1. Dado un paso que depende de otro, cuando se ejecuta, entonces recibe la salida del anterior.
2. Dado un paso sensible, cuando llega su turno, entonces la ejecución se pausa hasta mi aprobación.
3. Dada una regla que cambió, cuando se reevalúa el paso, entonces se aplica la regla vigente.

### HU-28 · Cancelar y recuperarse de fallos
- **Rol:** Operador
- **Historia:** Como operador quiero cancelar una ejecución y que el sistema se recupere si el worker se cae.
- **Fase:** O4
- **Sprint:** S9
- **Puntos:** 5
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** O4-BE-05

**Criterios de aceptación**
1. Dada una ejecución en marcha, cuando la cancelo, entonces se detiene al terminar el paso actual.
2. Dado un worker que muere, cuando pasa el tiempo límite, entonces la ejecución huérfana se marca y se puede reintentar.
3. Dadas 50 ejecuciones con fallos inyectados, cuando terminan, entonces no hay estados inconsistentes.

### HU-29 · Seguir la ejecución en vivo
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero ver cada paso avanzar en tiempo real para saber qué está pasando sin refrescar.
- **Fase:** O4
- **Sprint:** S9
- **Puntos:** 8
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** O4-BE-06, O4-APP-01, O4-UX-01

**Criterios de aceptación**
1. Dada una ejecución, cuando la abro, entonces la línea de tiempo se actualiza sola.
2. Dada una pérdida de conexión, cuando vuelve, entonces la app recupera los eventos perdidos.
3. Dado un paso fallido, cuando ocurre, entonces se expande con opciones de reintentar o cancelar.

### HU-30 · Ver y descargar resultados
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero ver los resultados de una tarea y recibir aviso al terminar.
- **Fase:** O4
- **Sprint:** S9
- **Puntos:** 3
- **Prioridad:** Medium
- **Estado:** To Do
- **Tareas:** O4-BE-07, O4-APP-02

**Criterios de aceptación**
1. Dada una tarea terminada, cuando la abro, entonces veo sus artefactos legibles y descargables.
2. Dada una tarea que termina, cuando estoy en la app, entonces recibo una notificación interna.

---

## Epic O5 · Conectores

### HU-31 · Conectar servicios de forma segura
- **Rol:** Administrador
- **Historia:** Como administrador quiero conectar servicios externos sin que las credenciales queden expuestas.
- **Fase:** O5
- **Sprint:** S10
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** O5-BE-01, O5-BE-02

**Criterios de aceptación**
1. Dada una credencial, cuando la guardo, entonces queda cifrada y las tablas de negocio solo tienen una referencia.
2. Dado cualquier conector, cuando falla, entonces devuelve un error normalizado con reintentos y timeout propios.

### HU-32 · Llamar APIs web permitidas
- **Rol:** Operador
- **Historia:** Como operador quiero que una tarea consulte APIs web autorizadas y nada más.
- **Fase:** O5
- **Sprint:** S10
- **Puntos:** 5
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** O5-BE-03

**Criterios de aceptación**
1. Dado un dominio fuera de la allowlist, cuando una tarea lo llama, entonces se bloquea.
2. Dada una IP privada o de metadatos, cuando se intenta, entonces se bloquea (prueba SSRF).

### HU-33 · Enviar emails desde una tarea
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero que una tarea pueda enviarme o enviar emails con mi aprobación.
- **Fase:** O5
- **Sprint:** S10
- **Puntos:** 5
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** O5-BE-04

**Criterios de aceptación**
1. Dado un paso de email, cuando se planifica, entonces requiere aprobación.
2. Dado el modo sandbox, cuando se envía, entonces llega a la cuenta de prueba.

### HU-34 · Disparar workflows de n8n
- **Rol:** Operador
- **Historia:** Como operador quiero que una tarea dispare workflows de n8n para reutilizar automatizaciones existentes.
- **Fase:** O5
- **Sprint:** S11
- **Puntos:** 5
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** O5-BE-05, O5-OPS-01, O5-DOC-01

**Criterios de aceptación**
1. Dado `docker compose --profile connectors up`, cuando arranca, entonces n8n queda disponible solo en local.
2. Dado un workflow de ejemplo, cuando la tarea lo dispara, entonces se ejecuta y su resultado vuelve como artefacto.
3. Dada la licencia de n8n, cuando se revisa, entonces queda documentado el uso permitido (ADR‑017).

### HU-35 · Usar herramientas MCP
- **Rol:** Equipo AICC
- **Historia:** Como equipo quiero exponer herramientas de servidores MCP como capacidades permitidas para ampliar AICC sin código nuevo.
- **Fase:** O5
- **Sprint:** S11
- **Puntos:** 8
- **Prioridad:** Medium
- **Estado:** To Do
- **Tareas:** O5-BE-06

**Criterios de aceptación**
1. Dado un servidor MCP de prueba, cuando se registra, entonces solo sus herramientas en allowlist aparecen como capacidades.
2. Dada una herramienta MCP, cuando se usa, entonces pasa por el mismo motor de políticas.

### HU-36 · Administrar conexiones desde el móvil
- **Rol:** Administrador
- **Historia:** Como administrador quiero ver, probar y desconectar servicios desde la app.
- **Fase:** O5
- **Sprint:** S11
- **Puntos:** 5
- **Prioridad:** Medium
- **Estado:** To Do
- **Tareas:** O5-APP-01, O5-UX-01

**Criterios de aceptación**
1. Dado un servicio, cuando lo conecto, entonces el flujo toma 3 pasos y explica qué permisos pide.
2. Dada una conexión, cuando la pruebo, entonces veo si funciona.

---

## Epic O6 · Consumo y presupuesto

### HU-37 · Saber cuánto cuesta cada ejecución
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero saber cuánto costó realmente cada ejecución frente a lo estimado.
- **Fase:** O6
- **Sprint:** S12
- **Puntos:** 5
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** O6-BE-01, O6-BE-04

**Criterios de aceptación**
1. Dada cualquier llamada con costo, cuando termina, entonces queda un evento de consumo.
2. Dada una ejecución terminada, cuando la reviso, entonces veo estimado frente a real.

### HU-38 · Presupuestos que me protegen
- **Rol:** Administrador
- **Historia:** Como administrador quiero presupuestos con alertas y pausa automática para no llevarme sorpresas.
- **Fase:** O6
- **Sprint:** S12
- **Puntos:** 8
- **Prioridad:** Highest
- **Estado:** To Do
- **Tareas:** O6-BE-02, O6-BE-03, O6-APP-02

**Criterios de aceptación**
1. Dado el 70 % del presupuesto, cuando se alcanza, entonces recibo alerta; al 90 % se pide confirmación; al 100 % se pausa.
2. Dada la app, cuando abro Consumo, entonces veo la barra de presupuesto con colores por umbral.

### HU-39 · Métricas técnicas del sistema
- **Rol:** Equipo AICC
- **Historia:** Como equipo quiero métricas técnicas para detectar degradaciones antes que los usuarios.
- **Fase:** O6
- **Sprint:** S12
- **Puntos:** 3
- **Prioridad:** Medium
- **Estado:** To Do
- **Tareas:** O6-OPS-01

**Criterios de aceptación**
1. Dado `/metrics`, cuando Prometheus lo consulta, entonces obtiene latencias, errores y colas.
2. Dado el perfil `observability`, cuando lo levanto, entonces Grafana muestra un panel básico.

### HU-40 · Todo de un vistazo
- **Rol:** Dueño de negocio
- **Historia:** Como usuario quiero abrir la app y ver qué está activo, qué espera mi decisión y cuánto he gastado.
- **Fase:** O6
- **Sprint:** S13
- **Puntos:** 5
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** O6-APP-01

**Criterios de aceptación**
1. Dado el Inicio, cuando lo abro, entonces veo tareas activas, aprobaciones pendientes y gasto del mes.

### HU-41 · Producto validado con usuarios reales
- **Rol:** Equipo AICC
- **Historia:** Como equipo quiero validar el orquestador con personas reales y documentarlo para cerrar el MVP con confianza.
- **Fase:** O6
- **Sprint:** S13
- **Puntos:** 5
- **Prioridad:** High
- **Estado:** To Do
- **Tareas:** O6-UX-01, O6-DOC-01

**Criterios de aceptación**
1. Dadas 3–5 sesiones de usabilidad, cuando terminan, entonces los hallazgos críticos quedan corregidos.
2. Dado el MVP, cuando se entrega, entonces existen el manual de usuario v1 y el ADR‑015.

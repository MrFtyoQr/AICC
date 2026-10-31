# Modelo de operación: AICC como intermediario entre el cliente y la nube

> Este documento fija **qué es AICC y qué no es**, y los **caminos** por los que un cliente orquesta desde la app.
> Cuando contradice a la guía original (§20 y §22), **gana este documento**; las diferencias están en la §7.
> Diagramas: ver [figma.md](../design/figma.md) ("Los 3 caminos", "Receta estándar", "Camino Conectar", "Nubes").

## 1. Qué es AICC (y qué no)

| AICC **sí** | AICC **no** |
|---|---|
| Entrega **soluciones** ya probadas (recetas) y las opera | No es un generador de ideas ni de planes de negocio |
| Estandariza los **pasos** para montar y operar la infraestructura en las nubes principales | No improvisa una arquitectura nueva para cada cliente |
| Es el **tercero intermediario** entre el cliente y la nube: el cliente pide, AICC ejecuta pasos administrables y auditados | No reemplaza a la nube ni esconde de quién es la cuenta |
| Orquesta lo que el cliente **ya tiene** (OpenClaw, n8n, Hermes, automatizaciones a medida) | No obliga a migrar lo que ya funciona |

La IA **interpreta** lo que el cliente necesita y **elige y rellena** una receta del catálogo. Lo que se ejecuta
siempre son pasos estandarizados, validados por un motor determinista y aprobados por el cliente (ADR-012, ADR-014).

## 2. Dos ejes que no hay que confundir

| Sigla | Significa | Pregunta que responde |
|---|---|---|
| **BYOK** | *Bring Your Own Key* | ¿De quién son las **llaves de IA** (Anthropic, OpenAI, Grok…)? Del cliente (BYOK) o de AICC (incluidas en el plan). |
| **BYOC** | *Bring Your Own Cloud* | ¿En la **cuenta de nube** de quién corre la solución? Del cliente (BYOC) o de AICC (administrado). |

Los dos ejes se combinan libremente: un cliente puede usar la nube de AICC con su propia llave de IA, o su nube con la llave de AICC.

## 3. Los tres caminos

```
                                ┌──────────────── App AICC (Flutter) ────────────────┐
                                │  pedir · aprobar · ver estado · ver costos          │
                                └───────────────────────┬─────────────────────────────┘
                                                        │
                                          AICC (orquestador + recetas + auditoría)
                    ┌───────────────────────────────────┼────────────────────────────────────┐
                    ▼                                   ▼                                    ▼
          A · CONECTAR                         B · TU NUBE (BYOC)                   C · ADMINISTRADO
   "Ya tengo mi stack"                  "Tengo cuenta en AWS/GCP/Azure"        "Háganlo ustedes"
   OpenClaw · n8n · Hermes · a medida   AICC despliega la receta EN SU cuenta  AICC despliega en SU cuenta de AICC
   AICC solo orquesta por conectores    con un rol delegado de permisos        (una cuenta aislada por cliente)
   El cliente paga su infra             mínimos. El cliente paga la nube.      AICC factura nube + operación
```

### A · Conectar (el cliente ya tiene su propio stack)

- **Para quién:** quien ya corre **OpenClaw**, **n8n**, **Hermes** o una **automatización a medida** y quiere mandarla desde la app.
- **Qué hace AICC:** registra el runtime como **conexión** del ambiente, y cada runtime se vuelve *capabilities* del catálogo
  (`runtime.trigger`, `runtime.status`, `runtime.result`). Una tarea de la app dispara el runtime, espera su resultado
  (callback o consulta periódica) y lo guarda como artefacto. Aprobaciones, presupuesto y auditoría funcionan igual.
- **Contrato mínimo de un runtime** (lo que implementa cada adaptador):

  | Operación | Para qué |
  |---|---|
  | `health()` | Ponerlo "en verde" en la app |
  | `list_actions()` | Saber qué workflows/agentes/herramientas expone |
  | `trigger(action, inputs, idempotency_key)` | Lanzar una ejecución |
  | `status(run_id)` / callback firmado | Seguirla sin bloquear |
  | `result(run_id)` | Traer el resultado como artefacto |

- **Cómo se conecta:** por la API/webhook o el servidor MCP que exponga cada runtime, con credenciales guardadas como
  secreto del workspace. Si el runtime está en una red privada, se usará un **puente saliente** ligero (el runtime llama
  a AICC; AICC no abre puertos en la red del cliente). La interfaz exacta de OpenClaw y de Hermes se confirma en un
  spike antes de construir su adaptador (§6).
- **Responsabilidad:** el runtime y su infraestructura son del cliente; AICC responde por la orquestación.

### B · Tu nube (BYOC)

- **Para quién:** quien tiene (o quiere) cuenta propia en AWS, Google Cloud o Azure y quiere ser dueño de todo.
- **Qué hace AICC:** despliega la **misma receta** que en el camino C, pero en la cuenta del cliente, usando un **acceso
  delegado de permisos mínimos y revocable**. Nunca pide la contraseña principal de la cuenta.

  | Nube | Mecanismo de acceso delegado |
  |---|---|
  | AWS | Rol IAM entre cuentas con `ExternalId` (el cliente lo crea con una plantilla de un clic) |
  | Google Cloud | Cuenta de servicio con *impersonation* / Workload Identity Federation |
  | Azure | App multi-tenant con consentimiento del administrador (o Azure Lighthouse) |
  | Cloudflare | API token con permisos acotados (ya probado en Forja) |

- **Responsabilidad:** el cliente paga la nube directamente; AICC opera la receta mientras la conexión esté vigente.
  Si el cliente revoca el acceso, su solución sigue corriendo: es suya.

### C · Administrado (nuestra nube)

- **Para quién:** quien no quiere saber nada de nubes.
- **Qué hace AICC:** despliega en **la nube estándar de AICC** (ADR-019), en una **cuenta aislada por cliente**. AICC
  factura infraestructura + operación y muestra el costo real.
- **Salida limpia:** como cada cliente tiene su propia cuenta, pasar de C a B es **transferir esa cuenta** al cliente, sin
  volver a desplegar.

### Híbrido

Mezclas de los anteriores en un mismo proyecto (p. ej. su n8n por el camino A + un bot nuevo por el camino C).
Cada recurso registra a qué camino pertenece, quién es dueño de la cuenta y quién paga.

## 4. La receta estándar (lo que AICC estandariza)

Una **receta** (Solution Template) es una solución probada, versionada, con pasos fijos. El cliente no ve "un plan":
ve una receta con sus parámetros, su costo y sus pasos. Las mismas fases sirven para B y C (y para A cuando se conecta
un runtime). Están tomadas de lo que ya funciona en la instalación asistida de Forja (`create-tts-agent`):

| Fase | Qué pasa | Regla que la hace administrable |
|---|---|---|
| **0 · Explicar y cotizar** | Qué se va a crear, dónde vive, quién es dueño y cuánto cuesta | Nada se toca sin aprobación explícita del cliente (ADR-014) |
| **1 · Plataforma** | Cuenta/acceso a la nube y recursos base | Nombres **únicos por cliente y receta** (`<receta>-<slug>-<uid>`). Antes de crear, se comprueba que no existan; si existen, **se detiene** |
| **2 · Configuración** | Datos del negocio, idioma, conocimiento | Configuración en caliente separada de la identidad fija (no exige volver a desplegar) |
| **3 · Conexiones** | Canales, llaves (BYOK), avisos | Los secretos van **directo al gestor de secretos**; jamás pasan por el chat ni por logs. Cada conexión se pone "en verde" con su health check |
| **4 · Prueba final** | Mensaje/ejecución real de punta a punta | La receta no queda "lista" con un rojo en el panel |
| **Operar** | Monitoreo, costos, actualizaciones, reversión | Cada versión se puede revertir; cada acción queda auditada |

**Checkpoints:** cada paso guarda su estado (en Forja, `.bot-setup.json`; en AICC, `provisioning_jobs` / `step_runs`).
Si algo falla o el cliente se va, se **reanuda desde el último paso**, nunca desde cero. Todos los pasos son
**idempotentes**: repetirlos no duplica recursos.

Forja (bot en Cloudflare Workers) es la **primera receta de referencia**: ya tiene las cuatro fases, el checkpoint, los
nombres únicos y el manejo de secretos. AICC la convierte de "instrucciones para un asistente" a pasos ejecutables por el
worker, con aprobación desde la app.

## 5. Cómo encaja con lo que ya está construido

| Pieza existente | Rol en este modelo |
|---|---|
| Workspace / Project / Environment (F1, ya en código) | El cliente y sus soluciones. Las conexiones (A) y los despliegues (B/C) cuelgan de un **ambiente** (ADR-010) |
| Roles (HU-11) | `task.run` lanza recetas; `task.approve` aprueba gastos y despliegues |
| Imagen `aicc-api` (ADR-018) | Es el **plano de control** de AICC; corre en la nube estándar. Las recetas de los clientes son otra cosa y viven en su cuenta |
| Orquestador O1–O6 | Ejecuta los pasos de la receta: tasks, aprobaciones, worker, eventos SSE |
| Conectores O5 | Se generaliza de "n8n" a **runtimes externos** (n8n, OpenClaw, Hermes, a medida) |
| Etapa B (S1 catálogo, S2 provisionamiento) | Catálogo de recetas + adaptadores por nube (AWS primero) |

## 6. Pruebas de validación antes de construir cada camino

Antes de programar un camino se hace un **spike** corto con un resultado medible. Si el spike falla, se ajusta el
diseño aquí antes de escribir código de producto.

| Spike | Qué se prueba | Resultado esperado | Cuándo |
|---|---|---|---|
| **V-A1** Conectar n8n | n8n local en Docker; AICC dispara un workflow y recibe el resultado por callback firmado | Ida y vuelta < 5 s, idempotente | Antes de S11 (O5) |
| **V-A2** Conectar OpenClaw y Hermes | Confirmar su interfaz real (API, webhook o MCP) y si necesitan puente saliente | Contrato `trigger/status/result` cubierto o brecha documentada | Antes de S11 |
| **V-B1** Acceso delegado AWS | Rol con `ExternalId` en una cuenta sandbox; AICC lista y crea un recurso etiquetado y lo borra | Sin credenciales permanentes; revocar corta el acceso | Inicio de Etapa B |
| **V-C1** Cuenta aislada por cliente | AWS Organizations: crear cuenta hija, desplegar, medir costo, transferirla | Costo real visible; transferencia sin redeploy | Inicio de Etapa B |
| **V-R1** Receta Forja | Desplegar `create-tts-agent` en una cuenta de prueba de Cloudflare siguiendo sus fases | Las 4 fases mapeadas 1:1 a pasos de AICC | Antes de S1 (catálogo) |

## 7. Diferencias con la guía original y cómo se resuelven

| Guía original | Ahora | Por qué |
|---|---|---|
| §20: AICC administrado / BYOC / híbrido | Se añade el camino **A · Conectar** como modalidad de primera clase | Muchos clientes ya tienen su stack; orquestarlo es valor inmediato sin infraestructura |
| §22: comparar AWS vs Hostinger caso por caso | **Nube estándar** para administrado (ADR-019) y un conjunto fijo de nubes para BYOC | Estandarizar pasos solo es posible con un número pequeño de destinos bien probados |
| §22.1: el motor "genera alternativas" | El motor elige **entre recetas y destinos ya soportados**; no diseña arquitecturas nuevas | AICC da soluciones, no planes |
| `orquestacion.md` §4: el LLM propone un plan de steps libre | El plan es una **receta del catálogo instanciada** con parámetros; el LLM solo elige y rellena (ver `orquestacion.md` §4) | Mismo motivo; además reduce riesgo y hace los costos predecibles |
| HU-34 solo n8n | HU-34 cubre runtimes externos (n8n primero; OpenClaw, Hermes y a medida tras V-A2) | Camino A |

Nada del código actual (auth, workspaces, roles, aislamiento) cambia por estas decisiones.

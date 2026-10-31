# UX / UI del Command Center

Meta: **una consola de mando que cualquier dueño de negocio entienda en 10 segundos.**
Detrás hay un orquestador complejo; delante debe haber una conversación, una lista de cosas por decidir
y una línea de tiempo que muestra lo que está pasando.

## 1. Principios

1. **Una pregunta, un botón.** Cada pantalla tiene una acción principal evidente.
2. **Lenguaje de negocio primero.** "3 leads atendidos", no "step_run succeeded". El detalle técnico existe, plegado.
3. **Nada pasa sin que lo sepas.** Todo lo que cuesta dinero o sale hacia fuera se muestra antes y se confirma.
4. **Siempre sabes dónde estás.** El contexto (workspace › proyecto › ambiente) está visible en todo momento; producción se distingue con color.
5. **En vivo, no refrescando.** Los estados cambian solos (SSE); el usuario nunca tira para recargar para enterarse de algo.
6. **Errores con salida.** Todo error dice qué pasó, qué no se perdió y qué hacer.
7. **Progresivo.** La primera vez se ve lo mínimo; las opciones avanzadas aparecen cuando se usan.
8. **Una mano, un pulgar.** Acciones principales en la mitad inferior de la pantalla.

## 2. Arquitectura de información

Navegación inferior con **4 destinos** (nunca más de 5):

| Pestaña | Contenido | Incremento |
|---|---|---|
| **Inicio** | Resumen: activas, pendientes de ti, gasto del mes, últimos resultados | M8 (antes: lista de tareas) |
| **Comando** | Entrada "¿Qué necesitas?" + conversación + tareas | M3 |
| **Aprobar** | Bandeja de decisiones con contador | M5 |
| **Más** | Conectores, Actividad, Consumo, Ajustes, Cuenta | M2+ |

Elementos persistentes:

- **Chip de contexto** arriba: `Mi negocio › General · Dev`. Toque → bottom sheet para cambiar.
- **Badge** en "Aprobar" con el número de decisiones pendientes.
- **Banner de conexión** solo cuando no hay red o la API no responde.

## 3. Flujos clave

### 3.1 Pedir algo (núcleo del producto)

```
Comando ─▶ escribe "Resume los leads de hoy y mándamelos por email"
       ─▶ [Enviar]
       ─▶ Tarjeta de tarea aparece: "Preparando un plan…" (animación sutil)
       ─▶ Propuesta: 3 pasos en lenguaje natural · costo estimado · "1 paso necesita tu aprobación"
       ─▶ [Aprobar y ejecutar]  ·  [Pedir cambios]  ·  (ver detalle técnico)
       ─▶ Línea de tiempo viva: ✓ Leer leads · ⟳ Resumir · ○ Enviar email
       ─▶ Resultado: tarjeta con el resumen + "Email enviado a ti@…" · costo real
```

Objetivo: de idea a ejecución en **≤ 4 toques** cuando no hay pasos sensibles.

### 3.2 Decidir (aprobaciones)

Cada tarjeta de aprobación responde siempre a tres preguntas:

1. **¿Qué va a pasar?** ("Enviar 1 email a cliente@ejemplo.com")
2. **¿Cuánto cuesta?** ("≈ $0.02 · dentro de tu presupuesto")
3. **¿Se puede deshacer?** ("No: el email no se puede retirar")

Acciones: **Aprobar** (deslizar si es `spend`/`write_external`), **Rechazar**, **Pedir cambios** (abre campo de texto).

### 3.3 Seguir una ejecución

Línea de tiempo vertical; cada paso muestra icono de estado, título humano, duración y costo.
Un paso fallido se expande solo y ofrece **Reintentar** o **Cancelar tarea**.

### 3.4 Conectar un servicio (M7)

1. Elegir servicio → 2. Autorizar / pegar credencial (con explicación de qué permisos y por qué) → 3. Probar conexión ✓.

## 4. Componentes del sistema de diseño

| Componente | Uso | Inc. |
|---|---|---|
| `StatusPill` | Estado con color + icono + texto (nunca solo color) | M0 |
| `ConnectionBanner` | Sin red / API caída | M0 |
| `ContextChip` + `ContextSheet` | Contexto actual y cambio | M2 |
| `CommandInput` | Entrada multilínea con enviar y sugerencias | M3 |
| `TaskCard` | Tarjeta central: título, estado, progreso, siguiente acción | M3 |
| `PlanStepTile` | Paso de plan con detalle plegable | M4 |
| `CostTag` | Costo estimado/real con moneda y tooltip de supuestos | M4 |
| `ApprovalCard` | Las tres preguntas + acciones | M5 |
| `SlideToConfirm` | Confirmación reforzada | M5 |
| `LiveTimeline` | Pasos en vivo | M6 |
| `ArtifactViewer` | Texto, JSON legible, archivo | M6 |
| `EmptyState` / `ErrorState` / `LoadingSkeleton` | Estados estándar | M0 |
| `BudgetBar` | 70 % ámbar, 90 % naranja, 100 % rojo | M8 |

## 5. Tokens de diseño (base)

| Token | Valor inicial | Nota |
|---|---|---|
| Tipografía | Inter (o la del sistema) · escalas 12/14/16/20/24/32 | Texto base 16 |
| Espaciado | 4 · 8 · 12 · 16 · 24 · 32 | Retícula de 4 dp |
| Radio | 8 (controles) · 16 (tarjetas) · 28 (sheets) | Material 3 |
| Color primario | A definir en F0-UX-02 | Generado con `ColorScheme.fromSeed` |
| Semánticos | `success`, `warning`, `danger`, `info`, `running`, `waiting` | Cada uno con su pareja claro/oscuro |
| Ambiente | `dev` neutro · `staging` ámbar · `production` rojo en el chip de contexto | Evita errores de ambiente |
| Movimiento | 150–250 ms, curvas estándar; respetar "reducir movimiento" | — |

## 6. Diccionario de estados (copy)

| Estado interno | Texto al usuario | Color |
|---|---|---|
| `DRAFT` | Borrador | neutral |
| `PLANNING` | Preparando un plan… | running |
| `PLANNING_FAILED` | No pude armar un plan | danger |
| `AWAITING_APPROVAL` | Esperando tu aprobación | waiting |
| `REJECTED_BY_POLICY` | No permitido por tus reglas | danger |
| `REJECTED` | Rechazada | neutral |
| `APPROVED` | Aprobada, en cola | info |
| `RUNNING` | En marcha | running |
| `PAUSED` | En pausa: necesita algo de ti | waiting |
| `DONE` | Lista | success |
| `FAILED` | Falló | danger |
| `CANCELLED` | Cancelada | neutral |

## 7. Proceso de diseño por incremento

1. Boceto de flujo (texto/diagrama en este repo).
2. Wireframe de baja fidelidad (Figma u otro; enlazar en el ticket).
3. Prototipo interactivo de las pantallas del incremento.
4. Revisión rápida (≥ 2 personas) → ajustes.
5. Solo entonces se abre el ticket `APP` correspondiente.

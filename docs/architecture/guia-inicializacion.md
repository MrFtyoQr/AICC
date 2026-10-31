AI COMMAND CENTER

Guía detallada para la inicialización del proyecto

Arquitectura base: Flutter + Python/FastAPI + PostgreSQL + Redis + Docker

Objetivo: dejar un repositorio reproducible, ejecutable localmente y preparado para crecer sin introducir complejidad prematura.

## 1. Propósito y alcance

Esta guía establece cómo crear la primera versión técnica de AICC (AI Command Center). AICC será una plataforma para definir, ejecutar y supervisar agentes y automatizaciones de IA. La aplicación Flutter será el cliente; el backend será responsable de identidad, autorización, planificación, ejecución, límites de consumo, auditoría e integración con proveedores.

La inicialización no pretende entregar todavía un producto con agentes autónomos completos. El resultado esperado es una base funcional: aplicación Flutter que consulta una API FastAPI, backend conectado a PostgreSQL y Redis, configuración por variables de entorno, pruebas mínimas y documentación.

Decisión arquitectónica inicial: monolito modular en el backend y workers separados para tareas asíncronas. No se recomienda comenzar con microservicios, Kubernetes o Kafka. Esta decisión reduce el número de piezas operativas mientras el dominio y la carga real todavía están por validarse.

## 2. Arquitectura objetivo

```
┌──────────────────────────────────────────────────────────────┐
│                    Clientes Flutter                           │
│              Android  |  iOS  |  Web (fase posterior)          │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTPS / JSON / SSE
┌──────────────────────────────▼───────────────────────────────┐
│                    API Python / FastAPI                       │
│ Auth · Workspaces · Agents · Tasks · Approvals · Usage         │
└──────────────┬─────────────────────────────┬─────────────────┘
               │                             │
       ┌───────▼────────┐            ┌───────▼────────┐
       │  PostgreSQL    │            │     Redis      │
       │ datos fuente   │            │ cola/cache     │
       └────────────────┘            └───────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Python Worker   │
                                    │ ejecución       │
                                    └────────┬────────┘
                                             │
                                  Proveedores / MCP / n8n
```

Regla fundamental: Flutter no debe ejecutar trabajos largos ni contener secretos de proveedores. La app envía solicitudes y presenta estados; el backend valida políticas y coordina la ejecución. Así, una tarea puede continuar aunque el usuario cierre la aplicación.

## 3. Decisiones técnicas de la primera versión

| Área | Tecnología | Responsabilidad |
|---|---|---|
| Cliente | Flutter / Dart | Interfaz compartida para Android e iOS. |
| Estado y navegación | Riverpod + GoRouter (cuando se incorporen) | Estado de UI y navegación. |
| API | Python + FastAPI | Contratos HTTP, validación y casos de uso. |
| Persistencia | PostgreSQL | Fuente de verdad para usuarios, tareas y auditoría. |
| Cola | Redis | Cola y coordinación de trabajos asíncronos. |
| Worker | Python | Ejecución fuera del ciclo de petición HTTP. |
| Contenedores | Docker Compose | Entorno local reproducible. |
| Contratos | OpenAPI + esquemas Pydantic | Contrato verificable entre Flutter y backend. |

## 4. Prerrequisitos

### 4.1 Herramientas comunes

- Git y una cuenta/repositorio remoto (por ejemplo, GitHub).
- Docker Desktop o Docker Engine con Docker Compose.
- Editor de código (VS Code, Android Studio o Cursor).
- Flutter SDK estable y Dart incluido con Flutter.
- Python 3.12 o una versión estable compatible con las dependencias seleccionadas.
- Un navegador moderno para probar documentación OpenAPI.

### 4.2 Requisitos por plataforma

- Android: Android Studio, Android SDK, herramientas de plataforma y un emulador o dispositivo con depuración USB.
- iOS: macOS, Xcode, Command Line Tools y simulador/dispositivo iOS. La compilación y firma iOS requieren macOS.
- Windows: permite desarrollar el backend y compilar/ejecutar Android; no permite generar una compilación iOS nativa.
- macOS: permite trabajar con Android e iOS, siempre que estén instalados los SDK y herramientas correspondientes.

## 5. Crear el repositorio y la estructura

Se recomienda un monorepo durante el MVP para versionar cliente, backend, contratos e infraestructura de forma coordinada.

```
mkdir ai-command-center
cd ai-command-center
git init
 
mkdir apps backend shared infrastructure docs
mkdir docs/architecture docs/decisions docs/security docs/api
```

Estructura objetivo inicial:

```
ai-command-center/
├── apps/
│   └── mobile/                 # Flutter: Android e iOS
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── orchestration/
│   │   ├── workers/
│   │   └── main.py
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── shared/
│   └── contracts/              # OpenAPI exportado y ejemplos
├── infrastructure/
│   ├── docker/
│   └── migrations/
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── security/
│   └── api/
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

No es necesario crear todos los módulos vacíos desde el primer día. La estructura es una guía de límites: cada módulo se incorpora cuando exista una responsabilidad real.

## 6. Inicializar la aplicación Flutter

1. Verificar la instalación:

```
flutter --version
flutter doctor -v
```

1. Crear la aplicación dentro de apps/mobile:

```
cd apps
flutter create --org com.treetech.aicc mobile
cd mobile
flutter run
```

Si el identificador de organización final todavía no está definido, utiliza uno temporal coherente y documenta el cambio antes de publicar. El identificador de paquete/bundle debe mantenerse estable una vez que la aplicación se distribuya.

1. Comprobar los destinos disponibles:

```
flutter devices
flutter doctor
```

1. Ejecutar en Android:

```
flutter run -d <device_id>
# Para listar los identificadores:
flutter devices
```

1. Ejecutar en iOS desde macOS:

```
open -a Simulator
flutter run -d ios
```

No añadas todos los paquetes desde el primer commit. Primero confirma que la plantilla Flutter compila. Después incorpora dependencias de manera incremental y registra sus versiones en pubspec.lock.

### 6.1 Estructura interna recomendada

```
lib/
├── main.dart
├── bootstrap.dart
├── app/
│   ├── app.dart
│   ├── router/
│   └── theme/
├── core/
│   ├── config/
│   ├── network/
│   ├── errors/
│   ├── security/
│   └── utils/
├── shared/
│   └── widgets/
└── features/
    ├── authentication/
    ├── dashboard/
    ├── command_center/
    ├── agents/
    ├── executions/
    ├── approvals/
    ├── connectors/
    ├── artifacts/
    └── settings/
```

Dentro de cada feature, separar presentation, domain y data cuando la complejidad lo justifique. Evita crear capas que solo reenvíen llamadas sin aportar reglas, aislamiento o testabilidad.

### 6.2 Dependencias que se pueden incorporar después

- flutter_riverpod: gestión de estado y dependencias.
- go_router: navegación declarativa.
- dio: cliente HTTP, interceptores y manejo de errores.
- freezed y json_serializable: modelos inmutables y serialización.
- flutter_secure_storage: almacenamiento seguro de tokens de sesión, no de claves maestras del servidor.
- drift: base local SQLite si se necesita historial offline.
- firebase_messaging: notificaciones push, cuando se implemente el flujo de notificaciones.

## 7. Inicializar el backend FastAPI

Desde la raíz del repositorio, crea un entorno virtual para aislar las dependencias Python.

```
cd backend
python -m venv .venv
 
# Windows PowerShell
.venv\Scripts\Activate.ps1
 
# macOS / Linux
source .venv/bin/activate
 
python -m pip install --upgrade pip
pip install fastapi uvicorn[standard] pydantic-settings sqlalchemy psycopg[binary] redis pytest httpx
pip freeze > requirements.txt
```

Para un proyecto mantenible, fija las versiones probadas y usa un único mecanismo de gestión de dependencias en el equipo. No mezcles pip, Poetry y uv en el mismo flujo sin una decisión documentada.

### 7.1 Crear la aplicación mínima

```
# backend/app/main.py
from fastapi import FastAPI
 
app = FastAPI(
    title="AICC API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
 
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "aicc-api"}
```

Ejecutar en desarrollo:

```
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verificar en el navegador: http://127.0.0.1:8000/health y http://127.0.0.1:8000/docs. En producción no se debe exponer el servidor de desarrollo ni dejar documentación interactiva pública sin una decisión de seguridad.

### 7.2 Límites de módulos

- api: endpoints, dependencias HTTP y traducción de solicitudes/respuestas.
- application: casos de uso y coordinación de operaciones.
- domain: entidades, reglas de negocio e invariantes.
- infrastructure: base de datos, proveedores, cola y almacenamiento.
- orchestration: planificación, políticas, selección de capacidades y ejecución.
- workers: consumidores de cola y ejecución de tareas fuera de HTTP.
- core: configuración, logging, errores y utilidades transversales.

## 8. Levantar PostgreSQL y Redis con Docker Compose

Crea docker-compose.yml en la raíz. Para desarrollo local, los puertos se publican solo en localhost. Los volúmenes conservan los datos entre reinicios.

```
services:
  postgres:
    image: postgres:16
    container_name: aicc-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: aicc
      POSTGRES_USER: aicc
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aicc -d aicc"]
      interval: 5s
      timeout: 3s
      retries: 10
 
  redis:
    image: redis:7
    container_name: aicc-redis
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
 
volumes:
  postgres_data:
  redis_data:
```

Crea un archivo .env local (no lo subas al repositorio):

```
POSTGRES_PASSWORD=cambia_esto_por_un_secreto_largo
DATABASE_URL=postgresql+psycopg://aicc:cambia_esto_por_un_secreto_largo@localhost:5432/aicc
REDIS_URL=redis://localhost:6379/0
APP_ENV=development
```

Crea .env.example con valores de ejemplo no funcionales y nombres de variables, nunca con secretos reales. Añade .env, .venv/, __pycache__/, .dart_tool/, build/, .DS_Store y archivos de IDE a .gitignore.

Levantar y comprobar servicios:

```
docker compose up -d
docker compose ps
docker compose logs -f postgres
docker compose exec postgres pg_isready -U aicc -d aicc
docker compose exec redis redis-cli ping
```

Para apagar sin borrar los datos: docker compose down. Para eliminar también los volúmenes (acción destructiva): docker compose down -v. No ejecutes el último comando si necesitas conservar la base local.

## 9. Configuración y conexión backend

La configuración debe leerse desde variables de entorno. No codifiques contraseñas, tokens, claves de proveedores ni URLs privadas dentro del código.

```
# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
 
class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str
    redis_url: str
 
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
 
settings = Settings()
```

La conexión SQLAlchemy, los pools y las sesiones deben vivir en infrastructure/database. Las migraciones deben gestionarse con Alembic antes de que el esquema de datos sea compartido por más de una persona o entorno.

No uses create_all() como sustituto permanente de migraciones. Es útil para pruebas muy simples, pero no ofrece un historial controlado de cambios del esquema.

## 10. Primer contrato API y conexión Flutter

Comienza con un contrato mínimo y estable. No implementes todavía endpoints que impliquen ejecutar agentes reales.

| Método | Ruta | Propósito inicial |
|---|---|---|
| GET | /health | Verificar disponibilidad de API. |
| GET | /api/v1/me | Obtener identidad autenticada (cuando exista auth). |
| GET | /api/v1/workspaces | Listar espacios del usuario. |
| GET | /api/v1/tasks | Consultar tareas del usuario. |
| POST | /api/v1/tasks/plan | Solicitar una propuesta de plan; no ejecutarla automáticamente. |

En Flutter, centraliza la URL base y el cliente HTTP en core/network. No distribuyas llamadas HTTP directamente por widgets. En Android Emulator, localhost del emulador no es el localhost de la computadora; normalmente se usa 10.0.2.2 para acceder al host. En iOS Simulator se puede usar localhost del Mac. Para un dispositivo físico, utiliza la IP LAN del equipo y configura el firewall; no uses HTTP inseguro en producción.

```
// Ejemplo conceptual: centralizar la URL base
const apiBaseUrl = String.fromEnvironment(
  'AICC_API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);
 
// Ejecutar Android Emulator con URL configurable:
flutter run --dart-define=AICC_API_BASE_URL=http://10.0.2.2:8000
```

El valor por defecto anterior es solo para Android Emulator local. Define valores separados para simulador iOS, dispositivo físico, staging y producción.

## 11. Seguridad mínima desde el primer commit

- Secretos: nunca guardar claves de OpenAI, Anthropic, Twilio u otros proveedores en Flutter, en el repositorio, en logs ni en archivos de configuración versionados.
- Sesiones: usar tokens de acceso de vida corta y mecanismo seguro de renovación; almacenar material de sesión con almacenamiento seguro del sistema operativo.
- Autorización: comprobar en backend que cada recurso pertenece al usuario/workspace que lo solicita. No confiar en IDs enviados por el cliente.
- Validación: validar entrada con esquemas; limitar tamaño, frecuencia y longitud de solicitudes.
- Ejecución: las herramientas se habilitan por allowlist y permisos; no permitir ejecución arbitraria de comandos ni acceso ilimitado a URLs.
- Aprobaciones: operaciones sensibles (publicar, enviar mensajes, modificar sistemas externos o generar costos) deben requerir política explícita y, cuando corresponda, aprobación humana.
- Auditoría: registrar quién solicitó qué acción, qué política se aplicó, qué herramienta se invocó y el resultado, evitando registrar secretos o datos innecesarios.
- Red: usar HTTPS fuera del entorno local; proteger endpoints administrativos; restringir CORS a orígenes conocidos.
- Aislamiento: cada consulta a datos debe aplicar el contexto del usuario/workspace en el servidor.

No se debe interpretar que tener un prompt de sistema o un agente especializado es una frontera de seguridad. Las decisiones de autorización deben imponerse en código determinista del backend.

## 12. Pruebas y calidad

Antes de añadir funciones, establece verificaciones automáticas que cualquier integrante pueda repetir.

```
# Backend
cd backend
pytest
 
# Flutter (desde apps/mobile)
flutter analyze
flutter test
```

Pruebas iniciales recomendadas:

- Backend: GET /health devuelve 200 y el esquema esperado.
- Backend: configuración falla de forma explícita si faltan variables obligatorias.
- Backend: pruebas de repositorios con base de datos de test aislada.
- Flutter: la app inicia y muestra una pantalla de estado/conexión.
- Flutter: el cliente maneja timeout, error HTTP y API no disponible sin bloquear la UI.
- Integración: Flutter puede consultar /health en emulador y dispositivo de prueba.
- Seguridad: un usuario no puede consultar recursos pertenecientes a otro workspace.

Activa análisis estático de Dart y Python, formato automático y revisión de dependencias. No desactives reglas del analizador solo para ocultar advertencias; justifica excepciones puntuales.

## 13. Flujo Git y documentación

```
git add .
git commit -m "chore: initialize AICC monorepo"
 
# Convención sugerida:
feat: nueva funcionalidad
fix: corrección
chore: configuración/mantenimiento
docs: documentación
test: pruebas
refactor: cambio interno sin cambio funcional
```

Mantén README.md con: propósito, arquitectura resumida, requisitos, pasos de arranque, variables de entorno, pruebas y solución de problemas. Registra decisiones importantes como ADR (Architecture Decision Records), por ejemplo: ADR-001 monolito modular; ADR-002 Flutter como cliente multiplataforma; ADR-003 PostgreSQL como fuente de verdad.

## 14. Orden recomendado de ejecución

1. Instalar y verificar Git, Flutter, Python, Docker y las herramientas de plataforma necesarias.
1. Crear el monorepo, README, .gitignore y .env.example.
1. Crear Flutter y comprobar que arranca en Android; en macOS, comprobar también iOS.
1. Crear FastAPI con /health y verificar /docs.
1. Levantar PostgreSQL y Redis con Docker Compose.
1. Configurar variables de entorno y comprobar conectividad desde backend.
1. Definir el primer contrato OpenAPI y centralizar el cliente HTTP en Flutter.
1. Mostrar desde Flutter el estado de conexión con el backend.
1. Añadir pruebas mínimas y análisis estático.
1. Documentar las decisiones y crear el primer commit estable.

## 15. Definición de terminado (DoD) de la inicialización

- El repositorio se clona en otra máquina y los pasos documentados permiten arrancar el entorno.
- Flutter compila y se ejecuta en al menos un destino Android; iOS se valida en macOS.
- FastAPI responde correctamente en /health y publica el esquema OpenAPI local.
- PostgreSQL y Redis aparecen healthy en Docker Compose.
- El backend carga configuración desde entorno y no depende de secretos versionados.
- Flutter puede llamar a la API usando una URL configurable por entorno.
- Las pruebas y analizadores básicos pasan.
- README y .env.example están actualizados y no contienen credenciales reales.

## 16. Qué NO implementar todavía

- Microservicios, Kubernetes, Kafka o service mesh.
- Marketplace público de agentes.
- Ejecución arbitraria de código o control irrestricto de computadora.
- Telefonía, publicación automática en redes o pagos reales en el primer incremento.
- Sistema complejo de facturación, multi-tenancy empresarial avanzado o colaboración en tiempo real.
- Múltiples proveedores de IA antes de tener una interfaz AgentRuntime y un caso de uso validado.

El objetivo de esta fase es validar el circuito cliente → API → datos/cola → respuesta, no construir toda la plataforma de agentes en un solo sprint.

## 17. Próximo incremento después de inicializar

Una vez cumplida la definición de terminado, el siguiente sprint puede implementar autenticación y workspaces; después, el flujo de creación de una tarea en estado DRAFT, su validación de políticas y una propuesta de plan sin ejecución. Solo cuando ese flujo esté probado se incorpora la cola de trabajos y el primer worker.

```
Flujo inicial seguro:
Flutter
  └─ POST /api/v1/tasks/plan
       └─ FastAPI valida identidad, workspace y entrada
            └─ Planner propone un plan estructurado
                 └─ Policy Engine valida capacidades y límites
                      └─ API devuelve plan + estado DRAFT
                           └─ Usuario revisa y aprueba
                                └─ En una fase posterior: enqueue + worker
```

## 18. Referencias técnicas (APA 7)

Dart. (s. f.). Multi-platform apps. https://dart.dev/multiplatform-apps

Docker. (s. f.). Docker Compose documentation. https://docs.docker.com/compose/

FastAPI. (s. f.). FastAPI documentation. https://fastapi.tiangolo.com/

Flutter. (s. f.). Install Flutter. https://docs.flutter.dev/get-started/install

Flutter. (s. f.). Architectural overview. https://docs.flutter.dev/resources/architectural-overview

Flutter. (s. f.). Deployment. https://docs.flutter.dev/deployment

OWASP Foundation. (s. f.). Application Security Verification Standard (ASVS). https://owasp.org/www-project-application-security-verification-standard/

OWASP Foundation. (s. f.). Mobile Application Security Verification Standard (MASVS). https://mas.owasp.org/MASVS/

PostgreSQL Global Development Group. (s. f.). PostgreSQL documentation. https://www.postgresql.org/docs/

Redis. (s. f.). Redis documentation. https://redis.io/docs/latest/

## Nota de mantenimiento

Las versiones de SDK, imágenes de contenedor y dependencias deben confirmarse al iniciar cada entorno y fijarse en el proyecto una vez validadas. Esta guía define el procedimiento y los límites arquitectónicos; no sustituye la verificación de compatibilidad de las versiones instaladas ni una revisión de seguridad previa a producción.

## AMPLIACIÓN ESTRATÉGICA: AICC COMO PLATAFORMA DE SERVICIOS INTELIGENTES

Versión ampliada 1.1 · Modelo de producto, despliegue, cotización y operación

## 19. Qué producto estamos construyendo realmente

AICC debe concebirse como una plataforma de orquestación y provisión de soluciones. No se limita a conectar agentes ya existentes ni a generar agentes desde cero: permite descubrir una necesidad, diseñar una solución, seleccionar componentes, calcular su costo, desplegarla, administrarla y medir sus resultados desde una interfaz móvil.

La aplicación móvil es el centro de mando. La ejecución real sucede en servicios backend, workers, infraestructura de AICC o infraestructura del cliente y proveedores externos. El teléfono permite describir objetivos, revisar propuestas, aprobar gastos y acciones, consultar ejecuciones, recibir alertas y administrar el servicio.

La propuesta de valor se resume así: el usuario expresa el resultado que necesita; AICC convierte esa intención en una solución técnica y comercial verificable.

| Capacidad | Qué hace AICC | Qué recibe el cliente |
|---|---|---|
| Orquestar | Conecta APIs, agentes, workflows y servicios que ya existen. | Una solución integrada sin tener que operar cada herramienta. |
| Generar | Crea componentes nuevos: agentes, lógica, prompts, workflows o artefactos. | Capacidades personalizadas para su proceso. |
| Provisionar | Prepara entornos, recursos, credenciales y despliegues. | Una instancia lista para operar. |
| Administrar | Monitorea disponibilidad, errores, consumo, permisos y versiones. | Control y soporte desde el teléfono. |
| Optimizar | Compara costos y propone migraciones o cambios de proveedor. | Una solución que puede evolucionar sin rehacerse por completo. |

## 20. Modelo de servicio: tres modalidades de infraestructura

> **Actualizado:** esta sección y la §22 quedan precisadas por [modelo-operacion.md](modelo-operacion.md) (ADR-011, ADR-019).

No se debe imponer un proveedor único. AICC debe ofrecer tres modalidades, explicando quién es dueño de la cuenta, quién paga la infraestructura y quién tiene la responsabilidad operativa.

| Modalidad | Propiedad y facturación | Ventajas | Cuándo ofrecerla |
|---|---|---|---|
| AICC administrado | La infraestructura se despliega en cuentas controladas por AICC. AICC factura infraestructura, operación y plataforma. | Experiencia sencilla, despliegue rápido y soporte centralizado. | Emprendedores o negocios que no quieren administrar servidores. |
| Infraestructura del cliente (BYOC) | El cliente conecta su propia cuenta de AWS, Hostinger u otro proveedor y paga directamente al proveedor. | Mayor control, transparencia de facturación y propiedad del entorno. | Empresas con cuenta cloud, equipo técnico o requisitos de propiedad. |
| Híbrido | AICC administra algunos componentes y otros corren en cuentas o servicios del cliente. | Flexibilidad para migrar por etapas y separar datos/servicios. | Clientes con sistemas existentes o restricciones parciales. |

BYOC significa Bring Your Own Cloud/Infrastructure. AICC debe solicitar permisos mínimos y preferir roles o credenciales delegadas de corta duración cuando el proveedor lo permita. No debe pedir la contraseña principal de la cuenta cloud.

## 21. El espacio del cliente: Workspace y Environment

Cada usuario u organización tendrá un Workspace lógico dentro de AICC. Dentro de él podrá tener uno o varios Environments (por ejemplo, development, staging y production). El workspace no equivale necesariamente a un servidor: es el límite lógico de identidad, recursos, permisos, presupuesto y auditoría.

```
Workspace
├── Members / Roles
├── Projects
│   ├── Lead Management
│   │   ├── Development Environment
│   │   └── Production Environment
│   └── Content Studio
├── Connections / Credentials (secretos cifrados)
├── Deployments / Infrastructure
├── Agents / Workflows
├── Budgets / Usage
├── Approvals
└── Audit Log
```

Reglas de diseño:

- Aislamiento por workspace aplicado en backend y base de datos; nunca confiar en el workspace_id enviado por la app sin verificar membresía.
- Separar ambientes de pruebas y producción, con credenciales, webhooks y presupuestos independientes.
- Permitir que un cliente tenga varios proyectos y que un proyecto use varios proveedores.
- Los recursos desplegados deben tener propietario, proveedor, región, identificador externo, versión, costo estimado y estado.
- La eliminación de un workspace debe tener un flujo de exportación, confirmación y política de retención; no borrar recursos cloud sin una confirmación explícita.

## 22. Motor de recomendación y selección de infraestructura

La decisión entre AWS, Hostinger u otro proveedor no debe tomarla un LLM libremente. El modelo puede interpretar la necesidad y explicar alternativas, pero un motor determinista debe comparar capacidades, límites, costos, región, disponibilidad, seguridad y requisitos de operación.

### 22.1 Flujo de decisión

1. Descubrir requisitos: tipo de solución, volumen esperado, concurrencia, datos sensibles, integraciones, disponibilidad, crecimiento y presupuesto.
1. Traducirlos a un perfil de carga: CPU/RAM, almacenamiento, transferencia, base de datos, colas, backups, tráfico y número de instancias.
1. Filtrar proveedores que no cumplan requisitos obligatorios de región, seguridad, capacidad o compatibilidad.
1. Generar al menos dos alternativas cuando sea viable: económica y administrada/escalable.
1. Calcular costo recurrente, costo variable y costo de operación AICC por separado.
1. Mostrar supuestos, límites, riesgos, costos no incluidos y nivel de confianza de la estimación.
1. Solicitar aprobación del cliente antes de crear recursos o comprometer gasto.
1. Provisionar mediante adaptadores, verificar salud y registrar identificadores y costos reales.

### 22.2 Comparación de proveedores

| Criterio | AWS (ej. Lightsail) | Hostinger VPS | Cómo debe decidir AICC |
|---|---|---|---|
| Modelo | Ecosistema cloud con servicios administrados y opciones de VPS. | VPS orientado a despliegue y administración de servidor. | Comparar el servicio exacto, no solo la marca. |
| Costo | Puede ser predecible en planes simples; otros servicios generan cargos separados. | Planes VPS con precio por plan y periodo contratado. | Calcular costo total: cómputo, disco, backups, tráfico, IP, impuestos y operación. |
| Escalabilidad | Amplia gama de servicios y opciones de crecimiento. | Adecuado para cargas VPS; evaluar límites y opciones disponibles. | Prever migración si crece la carga o se requieren servicios gestionados. |
| Operación | Más opciones, pero también más decisiones y configuración. | Puede simplificar el arranque de una aplicación en VPS. | Incluir horas de mantenimiento, parches, backups y respuesta a incidentes. |
| Uso sugerido | Cargas con necesidad de servicios cloud, controles y escalado. | MVP, workloads sencillos y cargas previsibles si cumple requisitos. | Elegir según requisitos y precio actualizado, no por preferencia fija. |

AICC no debe guardar precios como constantes permanentes en el código. Debe consultar APIs o catálogos de precios cuando existan, y usar cotizaciones fechadas o tarifas manuales revisadas cuando no exista una API confiable. Toda cotización mostrará moneda, fecha/hora, región, periodo, impuestos incluidos/excluidos y supuestos.

## 23. Ejemplo de producto: automatización de captura y respuesta de leads

Un nuevo usuario puede escribir en el Command Center: “Quiero capturar los leads que llegan de mi formulario, guardarlos, avisarme y responderles automáticamente”. AICC no debe saltar directamente a crear un servidor. Primero debe descubrir los canales, reglas comerciales y nivel de automatización que necesita el negocio.

### 23.1 Conversación de descubrimiento

- ¿De dónde llegan los leads? Formulario web, Facebook/Instagram, landing page, llamadas, WhatsApp o carga manual.
- ¿Dónde deben guardarse? CRM existente, hoja de cálculo, base de datos o bandeja de AICC.
- ¿Qué respuesta se envía? Confirmación, preguntas de calificación, catálogo, agenda o transferencia a una persona.
- ¿Qué volumen aproximado se espera? Leads por día/mes y horarios de atención.
- ¿Qué canal se usará para responder? Email, WhatsApp oficial, WhatsApp Web mediante una solución compatible o SMS.
- ¿Qué presupuesto mensual máximo acepta el cliente?

### 23.2 Arquitectura inicial recomendada

```
Formulario / Webhook / CRM
          │
          ▼
     AICC API Gateway
          │
          ▼
  Lead Intake Workflow (n8n)
          │
          ├── Validar y normalizar datos
          ├── Detectar duplicados
          ├── Guardar lead en CRM/DB
          ├── Clasificar prioridad (reglas o IA)
          ├── Enviar alerta al negocio
          └── Solicitar respuesta al canal elegido
                         │
                         ▼
                 Mensajería Adapter
                  ├── Email
                  ├── WhatsApp Cloud API
                  └── Evolution API (con evaluación de riesgo)
```

Para el primer MVP, el flujo puede ejecutarse en una instancia de n8n gestionada por AICC, con un workflow diseñado y mantenido por el equipo. El cliente consume el resultado desde AICC y no necesita entrar al editor de n8n. Esta distinción es importante para respetar las condiciones de licencia aplicables.

### 23.3 Evolución del canal de WhatsApp

| Alternativa | Ventaja | Riesgo/condición | Recomendación |
|---|---|---|---|
| Email o formulario + notificación | Costo y complejidad inicial bajos. | No resuelve conversación en WhatsApp. | Primera opción para validar captura y seguimiento. |
| Evolution API con Baileys/WhatsApp Web | Puede reducir el costo directo de API y permite prototipos. | Depende de un mecanismo no oficial de WhatsApp Web; puede desconectarse, cambiar o generar restricciones de cuenta. No prometer continuidad ni equivalencia oficial. | Solo piloto controlado, con consentimiento informado y alternativa de salida. |
| Evolution API conectado a WhatsApp Cloud API | Aprovecha la capa de integración y el canal oficial. | Se aplican las condiciones, políticas y tarifas de Meta; Evolution no elimina esos costos. | Opción de producción cuando se requiera WhatsApp confiable. |
| Proveedor BSP/CPaaS | Puede simplificar onboarding, soporte y operación. | Añade tarifas del proveedor y debe compararse con Cloud API directa. | Para clientes que priorizan soporte y rapidez. |

Importante: WhatsApp Business Platform permite automatización bajo sus políticas; fuera de la ventana de atención de 24 horas pueden requerirse plantillas aprobadas y se aplican las reglas y tarifas vigentes. AICC debe validar las políticas actuales antes de activar cada número. No debe diseñar un producto cuyo único camino dependa de una sesión no oficial.

## 24. Catálogo de soluciones y plantillas desplegables

En vez de pedirle a un agente que invente una infraestructura completa cada vez, AICC debe mantener un catálogo versionado de Solution Templates. Cada plantilla define componentes, recursos mínimos, variables requeridas, permisos, costos estimables, políticas y procedimiento de rollback.

| Plantilla | Componentes | Resultado |
|---|---|---|
| Lead Capture Starter | Webhook, n8n workflow, base de leads, notificación y canal de respuesta. | Captura, clasifica y responde leads. |
| Content Production | Brief, research, guion, generación de voz/imagen/video, revisión y almacenamiento. | Producción de contenido con aprobación. |
| Customer Support Assistant | Base de conocimiento, agente, canales, escalamiento humano y analítica. | Atención asistida con control de calidad. |
| Document Processing | Carga, OCR/extracción, validación, almacenamiento y revisión humana. | Procesamiento de documentos y trazabilidad. |

Cada plantilla debe incluir:

- template_id, versión semántica y compatibilidad de componentes.
- Parámetros configurables y secretos requeridos.
- Recursos mínimos y recursos recomendados.
- Permisos solicitados y acciones que requieren aprobación.
- Costo estimado por escenario y límites de uso.
- Health checks, métricas, logs y procedimiento de actualización.
- Plan de rollback y exportación de datos.

## 25. Generación interna frente a orquestación externa

AICC debe distinguir entre reutilizar capacidades externas y crear capacidades nuevas. El planner puede decidir entre ambas, pero debe justificar por qué. Crear todo desde cero aumenta tiempo, costo y mantenimiento; reutilizar sin evaluar licencias, seguridad o límites también puede ser incorrecto.

| Situación | Estrategia |
|---|---|
| Existe un servicio/API que cumple el objetivo | Orquestar el servicio mediante un conector con permisos limitados. |
| Existe workflow reutilizable | Instanciar una plantilla versionada y configurar sus parámetros. |
| Falta una regla de negocio específica | Generar lógica propia dentro de un componente controlado y probado. |
| Falta una capacidad de IA | Seleccionar un proveedor/modelo mediante AgentRuntime y límites de costo. |
| El proveedor no cumple presupuesto o requisitos | Proponer alternativa y migración; no cambiar en producción sin aprobación. |

## 26. Pipeline de generación de videos desde el teléfono

El usuario podrá pedir: “Crea un video de 30 segundos para promocionar mi restaurante”. AICC debe convertirlo en un pipeline de etapas, no en una única llamada opaca. Algunas etapas pueden usar proveedores externos y otras capacidades internas.

```
Brief
  │
  ▼
Planner + estimador
  │
  ├── Investigación / referencias
  ├── Guion y storyboard
  ├── Voz / música con derechos adecuados
  ├── Generación de imágenes o clips
  ├── Render / composición
  ├── Revisión y correcciones
  └── Exportación + almacenamiento
          │
          ▼
   Aprobación del usuario
          │
          ▼
 Publicación o descarga del artefacto
```

Antes de ejecutar, la cotización debe pedir o inferir:

- Duración final, formato (9:16, 16:9, 1:1) y resolución.
- Cantidad de escenas, clips generados y número de variantes.
- Si se requiere voz, avatar, subtítulos, música o traducción.
- Proveedor/modelo y nivel de calidad seleccionado.
- Número de revisiones incluidas y costo de regeneración.
- Almacenamiento, transferencia y tiempo de conservación.

No se debe cobrar únicamente por “un video”. El costo depende de las operaciones reales de generación y render. AICC debe mostrar un desglose antes de ejecutar y detenerse si se alcanza el presupuesto aprobado.

## 27. Modelo de costos y precios de AICC

La regla comercial recomendada es separar los costos de terceros del valor de AICC. El usuario debe poder entender qué paga por infraestructura, qué paga por consumo de proveedores y qué paga por la plataforma y su operación.

```
Precio al cliente =
    Infraestructura (real o estimada)
  + Consumo de proveedores (LLM, voz, video, mensajería, storage)
  + Operación administrada (soporte, backups, monitoreo, actualizaciones)
  + Tarifa AICC (plataforma/orquestación)
  + Impuestos aplicables
```

```
Margen bruto AICC =
    Ingreso AICC - costos directos atribuibles a AICC
```

### 27.1 Componentes de precio

| Componente | Cómo cobrarlo | Ejemplo de unidad |
|---|---|---|
| Plataforma AICC | Suscripción por workspace o nivel de servicio. | Mensual. |
| Infraestructura | Costo de proveedor trasladado con desglose; o incluido en un paquete con límites. | Servidor/mes, almacenamiento GB/mes. |
| Consumo IA | Costo variable medido por proveedor y modelo, con margen o tarifa de gestión claramente indicada. | Tokens, segundos de audio, imágenes, minutos de video. |
| Mensajería | Costo del canal/proveedor y tarifa de operación, separado del plan AICC. | Conversación, mensaje o unidad facturada por proveedor. |
| Implementación | Cargo único por configuración, integración, migración y pruebas. | Proyecto o paquete de horas. |
| Soporte administrado | Nivel de servicio con alcance y tiempos de respuesta definidos. | Mensual. |

### 27.2 Tres niveles comerciales iniciales

| Nivel | Incluye | Límites y objetivo |
|---|---|---|
| Starter / BYO | AICC para gestionar proyectos y conectores; el cliente aporta cuentas/proveedores. | Menor costo fijo; límites de ejecuciones y soporte comunitario/estándar. |
| Managed | Workspace y solución desplegada/administrada por AICC, monitoreo y backups según paquete. | Cuota mensual + consumo; para negocios que no quieren operar infraestructura. |
| Business | Ambientes separados, roles, políticas, auditoría, soporte prioritario e integraciones a medida. | Cotización por uso, requisitos y nivel de servicio. |

No publicar precios definitivos hasta medir costos reales de al menos tres perfiles de carga y definir márgenes. Durante el MVP, se pueden mostrar estimaciones y cotizaciones sujetas a confirmación, pero no presentar un costo variable como precio garantizado.

## 28. Cotizador inteligente y control de presupuesto

El usuario debe ver una pantalla de propuesta antes del despliegue con:

- Objetivo y alcance exacto de la solución.
- Diagrama resumido de componentes y flujo de datos.
- Alternativa recomendada y otras opciones comparables.
- Costo inicial de implementación y costo recurrente estimado.
- Consumo variable esperado y supuestos de volumen.
- Costos excluidos, límites, riesgos y dependencias de terceros.
- Propiedad de cuentas, datos y recursos.
- Botón de aprobación; sin aprobación no se crean recursos ni se activa facturación.

Los presupuestos deben existir por workspace, proyecto y ejecución. Se recomiendan límites configurables: alerta al 70 %, confirmación al 90 % y pausa automática al 100 %, siempre con posibilidad de definir excepciones explícitas.

Las cifras son estimaciones cuando dependen de tráfico, tokens, generación multimedia, tarifas regionales o impuestos. Registrar la cotización original y compararla con el gasto real permite aprender y mejorar la predicción.

## 29. Arquitectura backend adicional necesaria

La arquitectura inicial FastAPI/PostgreSQL/Redis se mantiene, pero se deben agregar módulos de catálogo, cotización, provisión, medición de consumo y ciclo de vida de recursos.

```
backend/app/
├── catalog/
│   ├── solution_templates/
│   ├── capabilities/
│   └── provider_catalog/
├── provisioning/
│   ├── providers/
│   │   ├── aws/
│   │   ├── hostinger/
│   │   └── docker/
│   ├── deployment_plans/
│   └── lifecycle/
├── pricing/
│   ├── estimators/
│   ├── quotes/
│   └── price_sources/
├── metering/
│   ├── usage_events/
│   ├── budgets/
│   └── reconciliation/
├── orchestration/
├── connectors/
│   ├── messaging/
│   ├── automation/
│   ├── llm/
│   └── media/
└── workers/
```

Interfaces recomendadas para evitar acoplamiento:

```
class InfrastructureProvider:
    async def estimate(self, requirements): ...
    async def provision(self, approved_plan): ...
    async def get_status(self, resource_id): ...
    async def resize(self, resource_id, target): ...
    async def backup(self, resource_id): ...
    async def destroy(self, resource_id, approval): ...
```

```
class PricingProvider:
    async def get_current_prices(self, region, usage_profile): ...
```

```
class MessagingProvider:
    async def send_message(self, destination, content, policy_context): ...
```

```
class MediaGenerationProvider:
    async def estimate(self, media_request): ...
    async def generate(self, approved_request): ...
```

Los métodos son contratos conceptuales: cada adaptador deberá implementar autenticación, idempotencia, reintentos, límites, timeouts, telemetría y manejo de errores propios del proveedor.

## 30. Modelo de datos ampliado

| Entidad | Campos/relación esenciales | Propósito |
|---|---|---|
| workspaces | id, owner_id, name, plan, status | Contenedor lógico y límite de aislamiento. |
| environments | id, workspace_id, name, type, region | Separación dev/staging/prod. |
| projects | id, workspace_id, name, solution_type | Agrupa una solución de negocio. |
| solution_templates | id, version, schema, policy, status | Catálogo de soluciones versionadas. |
| deployments | id, project_id, environment_id, provider, external_ref, status | Despliegues e infraestructura real. |
| provider_connections | id, workspace_id, provider, auth_type, secret_ref | Conexiones a proveedores; el secreto vive cifrado fuera de la tabla. |
| quotes | id, workspace_id, estimate, currency, expires_at, assumptions, status | Cotización aprobable y auditable. |
| quote_items | quote_id, component, unit, quantity, unit_price, subtotal | Desglose de costos. |
| usage_events | workspace_id, provider, metric, quantity, unit_cost, occurred_at | Medición de consumo. |
| budgets | workspace_id, project_id, period, limit, action_thresholds | Límites de gasto. |
| provisioning_jobs | deployment_id, idempotency_key, status, attempts | Provisionamiento seguro y recuperable. |
| audit_logs | actor, action, resource, result, timestamp | Trazabilidad de acciones. |

## 31. API inicial ampliada

| Método | Endpoint propuesto | Función |
|---|---|---|
| POST | /api/v1/discovery/sessions | Iniciar descubrimiento conversacional. |
| POST | /api/v1/solutions/recommend | Proponer solución a partir de requisitos. |
| GET | /api/v1/catalog/templates | Consultar plantillas disponibles. |
| POST | /api/v1/quotes | Crear cotización estimada. |
| GET | /api/v1/quotes/{id} | Consultar desglose y supuestos. |
| POST | /api/v1/quotes/{id}/approve | Aprobar gasto y alcance. |
| POST | /api/v1/deployments | Crear solicitud de despliegue aprobada. |
| GET | /api/v1/deployments/{id} | Consultar estado y recursos. |
| POST | /api/v1/deployments/{id}/pause | Pausar una solución. |
| POST | /api/v1/deployments/{id}/destroy | Solicitar eliminación con confirmación. |
| GET | /api/v1/usage/summary | Consultar consumo y costos. |
| GET | /api/v1/budgets | Consultar límites y alertas. |

## 32. Seguridad y gobierno del provisionamiento

- Separación estricta de tenants: validar workspace, proyecto y environment en cada operación.
- Credenciales cloud: usar roles IAM o credenciales delegadas con permisos mínimos; evitar llaves root o de administrador.
- Secret manager: cifrar secretos con KMS/Vault o solución equivalente; guardar referencias, no valores en tablas de negocio.
- Provisionamiento: requerir plan aprobado, idempotency key, límites de gasto y allowlist de regiones/servicios.
- Destrucción: nunca eliminar instancias, bases o buckets de producción por una interpretación del agente; requerir confirmación explícita y comprobar backups/retención.
- Red: aislar redes y servicios; no exponer paneles n8n, Redis, PostgreSQL o interfaces administrativas a Internet sin controles.
- Datos de leads: minimizar datos, definir retención, consentimiento/base legal y mecanismos de exportación/eliminación conforme a la normativa aplicable.
- Agentes: ningún LLM puede autorizar sus propias acciones, elevar privilegios o cambiar límites de presupuesto.
- Auditoría: guardar quién aprobó el gasto, qué plan se ejecutó, proveedor, región, costos estimados y reales y resultado.

## 33. Experiencia móvil: Command Center como consola de operaciones

La app debe organizarse alrededor de los trabajos del usuario, no alrededor de nombres técnicos de proveedores.

| Pantalla | Responsabilidad |
|---|---|
| Command Center | Entrada conversacional para describir objetivos y consultar estado. |
| Solution Proposal | Comparación de alternativas, diagrama, precio, riesgos y aprobación. |
| Workspaces | Cambiar de negocio, proyecto y ambiente. |
| Automations | Ver flujos, ejecuciones, errores y métricas de negocio. |
| Agents | Crear, configurar, versionar y asignar capacidades. |
| Media Studio | Solicitar videos, revisar etapas, costo y artefactos. |
| Infrastructure | Ver proveedor, estado, recursos, consumo y mantenimiento. |
| Approvals | Aprobar gastos, publicaciones, mensajes y cambios sensibles. |
| Usage & Billing | Consumo por proveedor, costo estimado/real, límites y facturas. |
| Activity / Audit | Historial de cambios y acciones ejecutadas. |

La interfaz debe mostrar primero el lenguaje del negocio (“leads atendidos”, “videos generados”, “tareas completadas”) y permitir abrir detalles técnicos cuando el usuario los necesite.

## 34. Roadmap revisado por fases

| Fase | Entregable | Criterio para avanzar |
|---|---|---|
| 0. Fundamentos | Flutter, FastAPI, PostgreSQL, Redis, Docker, CI y autenticación base. | Entorno reproducible y pruebas verdes. |
| 1. Workspace | Workspaces, proyectos, ambientes, roles y auditoría. | Aislamiento verificado entre usuarios. |
| 2. Command Center | Chat de descubrimiento y planner que produce propuestas estructuradas. | No ejecuta acciones sin política/aprobación. |
| 3. Catálogo y cotizador | Plantillas, perfiles de carga, comparador y cotización desglosada. | Costos y supuestos visibles antes de desplegar. |
| 4. Provisionamiento | Primer adaptador de infraestructura y ciclo de vida. | Despliegue idempotente, health check y rollback. |
| 5. Primera solución | Lead Capture Starter con webhook, n8n y almacenamiento. | Captura, deduplicación, notificación y pruebas. |
| 6. Mensajería | Adaptador email y evaluación de WhatsApp; piloto controlado y luego canal oficial. | Políticas, consentimiento, escalamiento humano y medición. |
| 7. Media Studio | Pipeline de video con estimación, generación y aprobación. | Costo por etapa y límites de regeneración. |
| 8. Operación comercial | Planes, facturación, soporte, alertas y métricas. | Margen y costo de servicio medidos en pilotos. |

## 35. Recomendación de estrategia para el MVP comercial

No intentaría lanzar desde el primer día un marketplace que aprovisione cualquier servicio cloud y cualquier agente. El MVP comercial debe demostrar una experiencia completa con pocas plantillas bien soportadas.

- Primera solución vendible: Lead Capture Starter para pequeños negocios.
- Canales iniciales: formulario/webhook y email/notificación; WhatsApp como módulo opcional sujeto a revisión de canal y políticas.
- Infraestructura inicial: una opción administrada sencilla y una opción BYOC; agregar más proveedores cuando haya demanda y pruebas.
- n8n: mantener los workflows bajo operación del equipo cuando el modelo de licencia lo permita; no exponer el editor al cliente sin validar licencia comercial.
- Generación de video: lanzar como pipeline separado con cotización por trabajo, no como consumo ilimitado dentro de una suscripción.
- AICC cobra plataforma, implementación/operación y consumo; el costo de terceros debe estar separado y trazable.
- Medir durante pilotos: costo real por lead procesado, costo por conversación, costo por video, horas de soporte y margen por cliente.

## 36. Decisiones que deben quedar como ADR

- ADR-010: AICC separa Workspace lógico de infraestructura física.
- ADR-011: Soporta AICC-managed, BYOC y modalidad híbrida.
- ADR-012: Un motor determinista compara proveedores y valida el plan; el LLM solo propone y explica.
- ADR-013: Las soluciones se despliegan desde plantillas versionadas y adaptadores.
- ADR-014: La cotización y aprobación preceden a cualquier gasto o provisionamiento.
- ADR-015: El sistema de medición registra costo estimado y real por proveedor y workspace.
- ADR-016: El canal de mensajería es intercambiable; WhatsApp no debe depender exclusivamente de una conexión no oficial.
- ADR-017: El uso comercial de n8n se valida contra su licencia antes de ofrecer edición o hosting a clientes.

## 37. Referencias adicionales (APA 7)

Amazon Web Services. (s. f.). Amazon Lightsail FAQs. https://aws.amazon.com/lightsail/faq/

Evolution Foundation. (2026). Evolution API [Repositorio de software]. GitHub. https://github.com/evolution-foundation/evolution-api

Meta. (2026, 23 de septiembre). WhatsApp Business Messaging Policy. https://whatsappbusiness.com/policy/

n8n. (2026, 6 de octubre). Which license do I need for my use case? n8n Help Center. https://support.n8n.io/article/can-i-use-your-license-for-my-use-case

n8n. (s. f.). n8n documentation. https://docs.n8n.io/

## Nota crítica sobre precios y licencias

Esta ampliación define la lógica del producto, no una cotización de proveedores. Los precios cloud, multimedia y mensajería cambian por región, volumen, modalidad, impuestos y condiciones comerciales. Antes de publicar tarifas, AICC debe consultar fuentes vigentes, registrar fecha y moneda y ejecutar pruebas de costo real. Asimismo, las licencias de n8n y las políticas de WhatsApp deben revisarse para el modelo comercial concreto antes de ofrecer el servicio.

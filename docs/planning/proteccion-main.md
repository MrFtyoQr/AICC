# Protección de la rama `main`

## Qué es y por qué importa

`main` es la versión "oficial" del proyecto: de ahí sale lo que se despliega en la nube. La protección es un
conjunto de reglas que GitHub **impone por sí mismo**, para que nadie (tampoco tú por accidente, ni una
herramienta automática con tus permisos) pueda:

| Sin protección puede pasar… | Con protección… |
|---|---|
| Subir un commit directo a `main` con un error o un secreto | Todo cambio entra por un Pull Request revisable |
| Hacer merge con la CI en rojo | El botón de merge se bloquea hasta que las pruebas pasen |
| `git push --force` y borrar historial | Prohibido reescribir o borrar `main` |
| Borrar la rama `main` | Prohibido |

Ahora que el repositorio es **público**, cualquiera puede leer el código y el historial. La protección no oculta
nada, pero garantiza que lo que se publica pasó primero por las pruebas, incluido el escaneo de secretos.

## Configuración recomendada (ruleset "Proteger main")

GitHub → *Settings* → *Rules* → *Rulesets* → *New branch ruleset*:

| Regla | Valor | Motivo |
|---|---|---|
| Target | rama por defecto (`main`) | — |
| Enforcement | **Active** | — |
| Bypass list | vacío (o solo tú, para emergencias) | Que la regla aplique de verdad |
| Restrict deletions | ✅ | No se puede borrar `main` |
| Block force pushes | ✅ | No se puede reescribir el historial |
| Require a pull request before merging | ✅, 0 aprobaciones mientras trabajes solo | Todo pasa por PR; con equipo, subir a 1 |
| Require status checks to pass | ✅ `secretos (gitleaks)`, `backlog coherente` | Ver la nota sobre los demás checks |
| Require linear history | Opcional | Historial más limpio si se usa *squash/rebase* |

### Nota sobre los checks obligatorios

Los workflows `backend` y `mobile` solo corren cuando cambian sus carpetas (para ahorrar minutos). Si se marcan
como obligatorios, un PR que solo toca documentación quedaría **bloqueado para siempre** esperando un check que
nunca llega. Hay dos opciones:

1. **Ahora:** exigir solo `secretos (gitleaks)` y `backlog coherente`, que corren en todos los PR.
2. **Mejor (tarea propuesta para S2):** unir la CI en un workflow con un job final `ci-ok` que siempre reporta
   y falla si falló cualquier parte relevante; entonces se exige solo `ci-ok`.

## Otras protecciones gratuitas para repos públicos (recomendadas)

| Función | Dónde | Qué hace |
|---|---|---|
| **Secret scanning + push protection** | Settings → *Code security* | GitHub rechaza el `git push` si detecta una clave real (segunda barrera además de gitleaks) |
| **Dependabot alerts** | Settings → *Code security* | Avisa si una dependencia tiene una vulnerabilidad conocida |
| **Private vulnerability reporting** | Settings → *Code security* | Permite que alguien reporte un fallo de seguridad sin hacerlo público (ver [SECURITY.md](../../SECURITY.md)) |

## Qué cuidar ahora que es público

- `.env` nunca se sube (está en `.gitignore`; gitleaks y push protection lo vigilan).
- El correo de los commits es visible. Para ocultarlo en adelante: GitHub → *Settings → Emails* →
  "Keep my email addresses private", y en este repo
  `git config user.email "<id>+MrFtyoQr@users.noreply.github.com"` (GitHub muestra la dirección exacta).
  Los commits ya publicados conservan el correo anterior.
- Sin datos de clientes, capturas con información real ni claves de proveedores en issues, PR o documentos.

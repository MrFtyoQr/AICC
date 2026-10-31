# ADR-007: El plan es una receta del catálogo instanciada

**Estado:** Aceptado · **Fecha:** 2026-10-31

## Contexto
AICC entrega soluciones probadas, no planes improvisados (ADR-011, [modelo-operacion.md](../architecture/modelo-operacion.md)).
El diseño original dejaba que el LLM propusiera una lista libre de pasos, lo que vuelve impredecibles el riesgo, el costo y
la calidad.

## Decisión
- Una **receta** (`app/domain/catalog/recipes.py`) es una solución versionada con **pasos fijos**, un esquema de
  parámetros (Pydantic) y supuestos propios. Cada paso usa una **capacidad** del catálogo.
- Al registrarse, cada receta se valida: capacidades existentes, referencias `{{params.x}}` y `{{steps.k.output}}`
  correctas, dependencias solo hacia pasos anteriores, máximo 10 pasos. Una receta mal definida impide arrancar.
- La IA devuelve solo `RecipeChoice`: `recipe_key`, `params`, `assumptions` (máx. 3, se recortan), `reason`.
  Nunca devuelve pasos, riesgos, costos ni aprobaciones.
- El plan (`plans` + `plan_steps`) se construye **expandiendo la receta** con los parámetros validados. Es inmutable:
  pedir otro plan crea una versión nueva. Guarda receta y versión, versión del prompt, modelo y tokens usados.
- Si la IA elige `ninguna`, una receta inexistente o parámetros inválidos, la tarea pasa a **No pude armar un plan**
  con la razón en lenguaje claro y se puede editar para volver a Borrador.

## Consecuencias
- Agregar una solución = agregar una receta (y, si hace falta, una capacidad) con sus pruebas; no se toca el planner.
- El catálogo de Etapa B (S1: Solution Templates, cotizador) crece sobre esta misma estructura.
- Los costos por paso (HU-22) se calculan desde la capacidad y la receta, no desde lo que diga la IA.

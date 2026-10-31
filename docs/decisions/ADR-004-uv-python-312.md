# ADR-004: uv y Python 3.12 para el backend

**Estado:** Aceptado · **Fecha:** 2026-10-31

## Contexto
La guía exige un único mecanismo de dependencias. El equipo tiene Python 3.15 en el sistema, demasiado
nuevo para garantizar wheels de todas las dependencias (psycopg, argon2, etc.).

## Decisión
- `uv` gestiona intérprete, entorno virtual y dependencias (`pyproject.toml` + `uv.lock`).
- Python **3.12** fijado en `backend/.python-version`; `uv` lo instala si falta.
- Prohibido mezclar `pip install`, Poetry o requirements sueltos.

## Consecuencias
- `uv sync` reproduce el entorno exacto en cualquier máquina y en CI.
- Las versiones se actualizan de forma deliberada (`uv lock --upgrade-package ...`).

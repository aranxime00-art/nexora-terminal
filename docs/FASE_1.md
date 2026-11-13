# Documentación - Fase 1: Preparación del Entorno

## Objetivos de la Fase
- Verificación del entorno Windows 11.
- Configuración de Python 3.12.
- Configuración de Git.
- Creación de la estructura base del proyecto.
- Configuración de dependencias mínimas.

## Decisiones Técnicas
- Se aisló el entorno usando `venv`.
- Se eligió `pydantic` para garantizar validación estricta de la configuración.
- Se configuró `pytest` para pruebas continuas y `ruff` + `mypy` para calidad de código.
- La arquitectura inicial solo incluye lo necesario para el arranque.

## Comandos Ejecutados
1. `py -3.12 -m venv .venv`
2. `.\.venv\Scripts\Activate.ps1`
3. `pip install -e .[dev]`
4. `pytest`
5. `ruff check .`
6. `mypy src`

## Resultados
(Los resultados se anexarán una vez ejecutados en el entorno local).

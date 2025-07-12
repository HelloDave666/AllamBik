# Alambik v3.0

Kindle highlight extraction tool with modern architecture.

## Architecture

Clean Architecture / Hexagonal pattern with:
- Domain layer (pure business logic)
- Application layer (use cases)
- Infrastructure layer (external dependencies)
- Presentation layer (GUI/API)

## Setup

poetry install
poetry run python -m src.main

## Development

poetry run pytest
poetry run black .
poetry run ruff check .

## Lancement app
poetry run python main.py
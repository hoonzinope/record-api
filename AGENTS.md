# Repository Guidelines

## Project Structure & Module Organization
- `router/` defines the FastAPI HTTP endpoints (see `router/controller.py`).
- `service/` contains business logic orchestrating persistence (`service/logic.py`).
- `repository/` holds data-access layers for MySQL and Redis (`repository/rdb_proc.py`, `repository/kv_proc.py`).
- `model/` contains core data structures such as `GameRecord` (`model/game_record.py`).
- `utils/` hosts small utilities and interfaces (UUID generation, verifier interfaces).
- `env.py` loads configuration from `.env`; `requirements.txt` pins Python dependencies.

## Build, Test, and Development Commands
- `python -m venv venv` creates a local virtual environment (already present here).
- `source venv/bin/activate` activates the virtual environment.
- `pip install -r requirements.txt` installs runtime dependencies.
- `uvicorn router.controller:app --reload` runs the API locally with auto-reload.

## Coding Style & Naming Conventions
- Use 4-space indentation and PEP 8 conventions for Python.
- Prefer `snake_case` for functions/variables and `PascalCase` for classes.
- Keep endpoint handlers thin in `router/` and move logic into `service/`.

## Testing Guidelines
- No project-specific test suite is present.
- If you add tests, place them under a new `tests/` directory and use `test_*.py` naming.

## Commit & Pull Request Guidelines
- This repo does not include Git history, so no established commit style is available.
- Use clear, imperative commit summaries (e.g., "Add ranking lookup in Redis") and include rationale in the body.
- PRs should describe the change, list impacted endpoints/modules, and include example requests when modifying API behavior.

## Configuration & Runtime Notes
- Set database and Redis connection values in `.env` (keys: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `REDIS_HOST`, `REDIS_PORT`).
- The service expects MySQL and Redis to be available during runtime.

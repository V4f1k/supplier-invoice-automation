# 13. Coding Standards

These standards are mandatory for ensuring code quality, consistency, and maintainability. They will be used to guide AI-driven development.

## 13.1. Core Standards

-   **Language & Runtime:** Python 3.11.9
-   **Style & Linting:**
    -   **Linter:** `Ruff` will be used for linting to enforce PEP 8 and other best practices.
    -   **Formatter:** `Black` will be used for automatic code formatting to ensure a consistent style.
    -   **Configuration:** A `pyproject.toml` file will contain the configurations for both Ruff and Black.
-   **Test Organization:** Test files will be located in the `tests/` directory and will mirror the structure of the `app/` directory. Test filenames must be prefixed with `test_`.

## 13.2. Naming Conventions

| Element | Convention | Example |
| :--- | :--- | :--- |
| **Modules** | `snake_case` | `ocr_service.py` |
| **Classes** | `PascalCase` | `CacheService` |
| **Functions** | `snake_case` | `get_from_cache` |
| **Variables** | `snake_case` | `invoice_data` |
| **Constants** | `UPPER_SNAKE_CASE` | `REDIS_TTL` |

## 13.3. Critical Rules

-   **Type Hinting:** All function signatures and variable declarations MUST include type hints.
-   **Configuration:** All configuration, especially secrets, MUST be loaded from environment variables via the `config.py` service. Do NOT hardcode configuration values.
-   **Error Handling:** Use the custom exception hierarchy defined in the Error Handling section. Do not use generic `Exception` catches where a more specific exception can be used.
-   **Logging:** Use the configured `Loguru` logger for all logging. Do not use `print()` statements in the application logic.

---

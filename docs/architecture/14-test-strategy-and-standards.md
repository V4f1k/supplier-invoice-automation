# 14. Test Strategy and Standards

A comprehensive testing strategy is essential for a reliable service.

## 14.1. Testing Philosophy

-   **Approach:** Test-After-Development. While TDD is not strictly enforced, all new code must be accompanied by tests.
-   **Coverage Goals:** A target of **90%** line coverage is set for all new code.
-   **Test Pyramid:** The focus will be on a strong base of unit tests, with a smaller number of integration tests and a minimal set of end-to-end tests.

## 14.2. Test Types and Organization

-   **Unit Tests:**
    -   **Framework:** `pytest`
    -   **File Convention:** `tests/test_*.py`
    -   **Location:** `tests/` directory.
    -   **Mocking Library:** `unittest.mock`
    -   **AI Agent Requirements:** Generate tests for all public methods, cover edge cases and error conditions, and mock all external dependencies (e.g., Redis, Gemini API).

-   **Integration Tests:**
    -   **Scope:** Testing the interaction between the API and the services (OCR, AI, Cache).
    -   **Location:** `tests/integration/`
    -   **Test Infrastructure:** `Testcontainers` will be used to spin up a real Redis instance for integration tests to ensure the cache logic works as expected. External APIs like Gemini will be mocked.

-   **End-to-End (E2E) Tests:**
    -   **Framework:** `pytest` with `httpx`
    -   **Scope:** A small number of tests that call the running service via its HTTP endpoint with real example files and validate the final JSON output.
    -   **Environment:** These tests will run against a locally running Docker container.

---

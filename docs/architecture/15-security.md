# 15. Security

Security is a primary concern and will be addressed at every layer.

## 15.1. Input Validation

-   **Validation Library:** `Pydantic` will be used for all input validation at the API boundary.
-   **Validation Location:** Validation occurs automatically by FastAPI when decoding the request into Pydantic models.
-   **Required Rules:** All external inputs MUST be validated. The `file` upload will be checked for valid content types (PDF, PNG, JPG).

## 15.2. Secrets Management

-   **Development:** Secrets will be managed using a `.env` file, which is loaded by Pydantic's settings management. The `.env` file itself MUST NOT be committed to version control.
-   **Production:** Secrets will be injected as environment variables into the Docker container.
-   **Code Requirements:** NEVER hardcode secrets. Access them only via the configuration service.

## 15.3. API Security

-   **Rate Limiting:** A rate limiter will be configured in FastAPI to prevent abuse of the API endpoints.
-   **CORS Policy:** A strict CORS policy will be implemented to only allow requests from authorized origins (e.g., the n8n workflow's host).
-   **Security Headers:** Standard security headers (e.g., `X-Content-Type-Options`, `X-Frame-Options`) will be added to all responses.

## 15.4. Dependency Security

-   **Scanning Tool:** `Poetry`'s built-in audit capabilities or a tool like `pip-audit` will be used to scan for vulnerabilities in dependencies.
-   **Update Policy:** Dependencies will be reviewed and updated on a regular basis.

---

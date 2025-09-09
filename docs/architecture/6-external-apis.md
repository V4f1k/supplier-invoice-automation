# 6. External APIs

This section details the external APIs the service relies on.

## 6.1. Google Gemini API

- **Purpose:** To provide the core AI-driven data extraction. It will take the unstructured text from the OCR process and return structured JSON data based on a carefully engineered prompt.
- **Documentation:** [https://ai.google.dev/gemini-api/docs/quickstart?lang=python](https://ai.google.dev/gemini-api/docs/quickstart?lang=python)
- **Base URL(s):** Managed by the `google-generativeai` Python library.
- **Authentication:** API Key. This key MUST be provided via an environment variable and managed by the Configuration Service. It MUST NOT be hardcoded.
- **Rate Limits:** The standard free tier is 60 Requests Per Minute (RPM). This is sufficient for initial development and testing, but for production use, we must enable billing on the Google Cloud project to access higher limits and avoid service disruption.

**Key Endpoints Used:**
- The primary interaction will be via the `GenerativeModel.generate_content` method in the Python SDK.

**Integration Notes:** The AI Service component will encapsulate all interactions with this API, including error handling for rate limits (HTTP 429) and other API-related errors.

---

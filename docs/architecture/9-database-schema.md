# 9. Database Schema

Based on the current requirements, this service is stateless and does not require a traditional persistent database (like PostgreSQL or MongoDB). The primary data storage is the Redis cache, which is used for performance and cost optimization, not as a permanent system of record.

## 9.1. Redis Cache Structure

-   **Key:** A `SHA-256` hash of the input invoice file. This provides a unique, fixed-length identifier for each unique file.
-   **Value:** The complete JSON string of the `ExtractionResponse` data model. This allows us to store the entire result and return it directly on a cache hit.
-   **TTL (Time-To-Live):** Each key will be set with a 24-hour (86,400 seconds) TTL, as specified in the PRD. This ensures stale data is automatically evicted.

No other database schema is required for the initial version of this service. If future requirements involve storing historical extraction data for analytics, a persistent database could be added.

---

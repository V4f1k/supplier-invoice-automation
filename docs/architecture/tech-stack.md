# 3. Tech Stack

## 3.1. Cloud Infrastructure

Based on the PRD, the deployment target is a Hetzner server.

- **Provider:** Hetzner
- **Key Services:** Hetzner Cloud VM (e.g., CPX21 or higher) to host the Docker environment. Redis can be run as a separate container on the same VM.
- **Deployment Regions:** Falkenstein, Germany (default, can be changed based on user location).

## 3.2. Technology Stack Table

This table outlines the specific technologies and versions to be used. These choices are based on the PRD and best practices for building a robust service.

| Category | Technology | Version | Purpose | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Language** | Python | 3.11.9 | Core application language | As per PRD; modern, performant, and has excellent AI/ML library support. |
| **Web Framework** | FastAPI | 0.111.0 | Building the REST API | As per PRD; high-performance async framework ideal for I/O-bound tasks. |
| **Web Server** | Uvicorn | 0.30.1 | ASGI server for FastAPI | Standard, high-performance server for running FastAPI applications. |
| **Dependency Mgmt** | Poetry | 1.8.2 | Managing dependencies & packaging | Provides deterministic builds and is a modern standard superior to `requirements.txt`. |
| **OCR Library** | Surya-OCR | 0.3.1 | Text, line, and table detection | As per PRD; state-of-the-art performance for the required tasks. |
| **AI Client** | google-generativeai | 0.7.1 | Interfacing with Gemini API | The official and recommended Python SDK for the Google Gemini API. |
| **Cache** | Redis | 7.2 | Caching invoice results | As per PRD; industry-standard, fast in-memory key-value store. |
| **Cache Client** | redis-py | 5.0.7 | Python interface for Redis | The official, standard library for connecting to Redis from Python. |
| **Containerization**| Docker Engine | 27.0 | Containerizing the application | As per PRD; ensures a consistent environment from development to production. |

---

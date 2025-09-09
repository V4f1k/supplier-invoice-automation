# 11. Infrastructure and Deployment

This section defines a pragmatic approach to deploying and managing the service, focusing on simplicity and automation.

## 11.1. Infrastructure as Code

-   **Tool:** Docker Compose (`docker-compose.yml`)
-   **Location:** Project root
-   **Approach:** For local development, Docker Compose will manage the FastAPI application and the Redis container. For production, the `Dockerfile` will be used to build the service image, which will be run on the Hetzner VM. A simple shell script will be used on the server for deployment.

## 11.2. Deployment Strategy

-   **Strategy:** Simple Rolling Update
-   **CI/CD Platform:** GitHub Actions (or a similar platform)
-   **Pipeline Configuration:** A workflow file (e.g., `.github/workflows/deploy.yml`) will define the pipeline.

## 11.3. Environments

-   **`development`:** Run locally via `docker-compose up`. Developers will use this for coding and testing.
-   **`production`:** A single Hetzner Cloud VM running the application and Redis containers.

## 11.4. Environment Promotion Flow

```
(Local Development) -> (Git Push to `main` branch) -> (CI/CD Pipeline) -> (Production Deployment)
```

-   The flow is continuous deployment. A merge or push to the `main` branch will automatically trigger the production deployment workflow.

## 11.5. Rollback Strategy

-   **Primary Method:** Manual redeployment of a previously known stable Docker image tag.
-   **Trigger Conditions:** Critical errors or bugs discovered in the production environment after a new deployment.
-   **Recovery Time Objective:** < 15 minutes.

---

# Deployment and Operations Guide

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Production Configuration](#production-configuration)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Backup and Recovery](#backup-and-recovery)
7. [Scaling Strategies](#scaling-strategies)
8. [Security Hardening](#security-hardening)
9. [Maintenance Procedures](#maintenance-procedures)
10. [Troubleshooting](#troubleshooting)

---

## Deployment Options

### Overview

The Supplier Invoice Automation Service can be deployed in multiple ways depending on your infrastructure requirements:

- **Docker Compose** - Local development and small-scale production
- **Kubernetes** - Enterprise production with auto-scaling
- **Cloud Services** - Managed container services (ECS, GKE, AKS)
- **Bare Metal** - Direct installation on servers

### Recommended Deployment Strategy

| Environment | Recommended Option | Scalability | Complexity |
|-------------|-------------------|-------------|------------|
| **Development** | Docker Compose | Low | Low |
| **Staging** | Kubernetes/Docker | Medium | Medium |
| **Production** | Kubernetes | High | High |
| **Enterprise** | Kubernetes + Service Mesh | Very High | Very High |

---

## Docker Deployment

### Single Container Deployment

#### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- Google Gemini API Key

#### Quick Deployment

1. **Clone and Configure**
```bash
git clone <repository-url>
cd supplier-invoice-automation

# Configure environment
cp .env.example .env
# Edit .env with your Google API key
```

2. **Build and Deploy**
```bash
# Build and start services
docker-compose up --build -d

# Verify deployment
curl http://localhost:8000/health
```

3. **Production Docker Compose**
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - REDIS_HOST=redis
      - LOG_LEVEL=INFO
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'

  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.25'

volumes:
  redis_data:
```

### Multi-Node Docker Swarm

#### Initialize Swarm
```bash
# Initialize on manager node
docker swarm init --advertise-addr <manager-ip>

# Join worker nodes
docker swarm join --token <worker-token> <manager-ip>:2377
```

#### Deploy Stack
```yaml
version: '3.8'
services:
  app:
    image: supplier-invoice-automation:latest
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY_FILE=/run/secrets/google_api_key
      - REDIS_HOST=redis
    secrets:
      - google_api_key
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
      placement:
        constraints:
          - node.role == worker

  redis:
    image: redis:7.2-alpine
    deploy:
      placement:
        constraints:
          - node.role == worker

secrets:
  google_api_key:
    external: true
```

```bash
# Deploy stack
docker stack deploy -c docker-stack.yml invoice-app
```

---

## Kubernetes Deployment

### Prerequisites
- Kubernetes 1.20+
- kubectl configured
- 4GB RAM cluster minimum
- Ingress controller (NGINX, Traefik)

### Basic Kubernetes Deployment

#### 1. Namespace and ConfigMap
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: invoice-automation
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: invoice-automation
data:
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  LOG_LEVEL: "INFO"
```

#### 2. Secrets
```bash
# Create secret for API key
kubectl create secret generic api-secrets \
  --from-literal=google-api-key="your_api_key_here" \
  -n invoice-automation
```

#### 3. Redis Deployment
```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: invoice-automation
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7.2-alpine
        ports:
        - containerPort: 6379
        resources:
          limits:
            memory: "256Mi"
            cpu: "250m"
          requests:
            memory: "128Mi"
            cpu: "100m"
        volumeMounts:
        - name: redis-data
          mountPath: /data
        command: ["redis-server", "--appendonly", "yes"]
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: invoice-automation
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: invoice-automation
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

#### 4. Application Deployment
```yaml
# k8s/app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: invoice-app
  namespace: invoice-automation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: invoice-app
  template:
    metadata:
      labels:
        app: invoice-app
    spec:
      containers:
      - name: app
        image: supplier-invoice-automation:latest
        ports:
        - containerPort: 8000
        env:
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: google-api-key
        - name: REDIS_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: REDIS_HOST
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: LOG_LEVEL
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: invoice-app-service
  namespace: invoice-automation
spec:
  selector:
    app: invoice-app
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

#### 5. Ingress Configuration
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: invoice-app-ingress
  namespace: invoice-automation
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  rules:
  - host: invoice-api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: invoice-app-service
            port:
              number: 80
  tls:
  - hosts:
    - invoice-api.yourdomain.com
    secretName: tls-secret
```

#### 6. Horizontal Pod Autoscaler
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: invoice-app-hpa
  namespace: invoice-automation
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: invoice-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### Deployment Commands
```bash
# Apply all configurations
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n invoice-automation
kubectl get services -n invoice-automation

# Check logs
kubectl logs -f deployment/invoice-app -n invoice-automation
```

### Advanced Kubernetes Features

#### Network Policies
```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: invoice-app-netpol
  namespace: invoice-automation
spec:
  podSelector:
    matchLabels:
      app: invoice-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to: []  # Allow external API calls
    ports:
    - protocol: TCP
      port: 443
```

#### Pod Disruption Budget
```yaml
# k8s/pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: invoice-app-pdb
  namespace: invoice-automation
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: invoice-app
```

---

## Production Configuration

### Environment Variables

#### Required Configuration
```bash
# Core Application
GOOGLE_API_KEY=your_production_api_key
REDIS_HOST=redis.internal
REDIS_PORT=6379

# Production Settings
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760
CIRCUIT_BREAKER_TIMEOUT=60

# Performance Tuning
WORKERS=4
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=50
```

#### Optional Configuration
```bash
# Redis Configuration
REDIS_DB=0
REDIS_PASSWORD=secure_password
REDIS_SSL=true

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30

# Security
ALLOWED_HOSTS=invoice-api.yourdomain.com
CORS_ORIGINS=https://your-frontend.com

# Features
CACHE_TTL=86400
RETRY_ATTEMPTS=3
```

### Production Dockerfile

```dockerfile
# Multi-stage production build
FROM python:3.11.9-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.6.1

# Copy dependency files
WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Production stage
FROM python:3.11.9-slim as runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Redis Production Configuration

```bash
# redis.conf for production
bind 0.0.0.0
port 6379
requirepass your_secure_password

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Security
protected-mode yes
tcp-keepalive 300

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

---

## Monitoring and Logging

### Application Monitoring

#### Health Check Monitoring
```bash
#!/bin/bash
# health-monitor.sh
while true; do
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
    if [ $response -ne 200 ]; then
        echo "$(date): Health check failed - HTTP $response"
        # Send alert
    fi
    sleep 30
done
```

#### Prometheus Metrics
```python
# app/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')
CACHE_HIT_RATE = Gauge('cache_hit_rate', 'Cache hit rate percentage')
CIRCUIT_BREAKER_STATE = Gauge('circuit_breaker_state', 'Circuit breaker state', ['service'])

# Start metrics server
start_http_server(9090)
```

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Invoice Automation Service",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "cache_hit_rate",
            "legendFormat": "Hit Rate %"
          }
        ]
      }
    ]
  }
}
```

### Centralized Logging

#### ELK Stack Configuration
```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:7.15.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"

  logstash:
    image: docker.elastic.co/logstash/logstash:7.15.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5044:5044"
```

#### Logstash Configuration
```ruby
# logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "invoice-automation" {
    json {
      source => "message"
    }
    date {
      match => [ "timestamp", "ISO8601" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "invoice-automation-%{+YYYY.MM.dd}"
  }
}
```

### Log Aggregation

#### Fluentd Configuration
```yaml
# fluent.conf
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<match invoice.app.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name invoice-automation
  type_name application
  <buffer>
    @type file
    path /var/log/fluentd-buffers/invoice-app
    flush_mode interval
    flush_interval 30s
    chunk_limit_size 2M
    queue_limit_length 32
    retry_max_interval 30
    retry_forever true
  </buffer>
</match>
```

---

## Backup and Recovery

### Redis Backup Strategy

#### Automated Backup Script
```bash
#!/bin/bash
# redis-backup.sh

BACKUP_DIR="/backups/redis"
DATE=$(date +%Y%m%d_%H%M%S)
REDIS_HOST="redis"
REDIS_PORT="6379"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
redis-cli -h $REDIS_HOST -p $REDIS_PORT --rdb $BACKUP_DIR/dump_$DATE.rdb

# Compress backup
gzip $BACKUP_DIR/dump_$DATE.rdb

# Remove backups older than 7 days
find $BACKUP_DIR -name "*.rdb.gz" -mtime +7 -delete

echo "Backup completed: dump_$DATE.rdb.gz"
```

#### Cron Configuration
```bash
# Add to crontab
0 2 * * * /usr/local/bin/redis-backup.sh
```

### Application State Backup

#### Configuration Backup
```bash
#!/bin/bash
# config-backup.sh

BACKUP_DIR="/backups/config"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup Kubernetes configs
kubectl get all -n invoice-automation -o yaml > $BACKUP_DIR/$DATE/k8s-resources.yaml

# Backup ConfigMaps and Secrets
kubectl get configmaps -n invoice-automation -o yaml > $BACKUP_DIR/$DATE/configmaps.yaml
kubectl get secrets -n invoice-automation -o yaml > $BACKUP_DIR/$DATE/secrets.yaml

# Create tarball
tar -czf $BACKUP_DIR/config_$DATE.tar.gz -C $BACKUP_DIR $DATE
rm -rf $BACKUP_DIR/$DATE

echo "Configuration backup completed: config_$DATE.tar.gz"
```

### Disaster Recovery

#### Recovery Procedures
```bash
#!/bin/bash
# disaster-recovery.sh

BACKUP_DIR="/backups"
RESTORE_DATE=$1

if [ -z "$RESTORE_DATE" ]; then
    echo "Usage: $0 <YYYYMMDD_HHMMSS>"
    exit 1
fi

# Stop services
kubectl scale deployment invoice-app --replicas=0 -n invoice-automation

# Restore Redis data
gunzip -c $BACKUP_DIR/redis/dump_$RESTORE_DATE.rdb.gz > /tmp/dump.rdb
kubectl cp /tmp/dump.rdb redis-pod:/data/dump.rdb -n invoice-automation

# Restart Redis
kubectl rollout restart deployment/redis -n invoice-automation

# Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l app=redis -n invoice-automation --timeout=300s

# Restore application
kubectl scale deployment invoice-app --replicas=3 -n invoice-automation

echo "Disaster recovery completed for backup: $RESTORE_DATE"
```

---

## Scaling Strategies

### Horizontal Scaling

#### Auto-scaling Configuration
```yaml
# Kubernetes HPA with custom metrics
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: invoice-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: invoice-app
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

#### Load Balancer Configuration
```yaml
# NGINX Load Balancer
upstream invoice_backend {
    least_conn;
    server invoice-app-1:8000 max_fails=3 fail_timeout=30s;
    server invoice-app-2:8000 max_fails=3 fail_timeout=30s;
    server invoice-app-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name invoice-api.yourdomain.com;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://invoice_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 30s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    location /health {
        access_log off;
        proxy_pass http://invoice_backend;
        proxy_connect_timeout 5s;
        proxy_send_timeout 5s;
        proxy_read_timeout 5s;
    }
}
```

### Vertical Scaling

#### Resource Optimization
```yaml
# Resource limits for different workloads
resources:
  # Small workload
  small:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  
  # Medium workload  
  medium:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "1Gi"
      cpu: "1000m"
  
  # Large workload
  large:
    requests:
      memory: "1Gi"
      cpu: "1000m"
    limits:
      memory: "2Gi"
      cpu: "2000m"
```

---

## Security Hardening

### Network Security

#### Service Mesh (Istio)
```yaml
# istio-config.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: invoice-automation
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: invoice-app-policy
  namespace: invoice-automation
spec:
  selector:
    matchLabels:
      app: invoice-app
  rules:
  - from:
    - source:
        namespaces: ["istio-system"]
  - to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/health", "/extract"]
```

### Container Security

#### Security Context
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  runAsGroup: 1001
  fsGroup: 1001
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

#### Pod Security Policy
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: invoice-app-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

### Secret Management

#### Vault Integration
```yaml
# vault-config.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vault-auth
  namespace: invoice-automation
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: invoice-app
spec:
  template:
    spec:
      serviceAccountName: vault-auth
      containers:
      - name: vault-agent
        image: vault:latest
        command:
        - vault
        - agent
        - -config=/etc/vault/config.hcl
        volumeMounts:
        - name: vault-config
          mountPath: /etc/vault
      - name: app
        image: supplier-invoice-automation:latest
        env:
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: vault-secrets
              key: google-api-key
```

---

## Maintenance Procedures

### Rolling Updates

#### Zero-Downtime Deployment
```bash
#!/bin/bash
# rolling-update.sh

IMAGE_TAG=$1

if [ -z "$IMAGE_TAG" ]; then
    echo "Usage: $0 <image_tag>"
    exit 1
fi

# Update deployment
kubectl set image deployment/invoice-app \
    app=supplier-invoice-automation:$IMAGE_TAG \
    -n invoice-automation

# Wait for rollout to complete
kubectl rollout status deployment/invoice-app -n invoice-automation --timeout=600s

# Verify health
kubectl run test-pod --rm -i --tty --restart=Never --image=curlimages/curl -- \
    curl -f http://invoice-app-service/health

if [ $? -eq 0 ]; then
    echo "Deployment successful!"
else
    echo "Deployment failed, rolling back..."
    kubectl rollout undo deployment/invoice-app -n invoice-automation
    exit 1
fi
```

### Database Migration

#### Redis Migration Script
```bash
#!/bin/bash
# redis-migration.sh

OLD_REDIS="redis-old:6379"
NEW_REDIS="redis-new:6379"

# Create snapshot of old Redis
redis-cli -h $OLD_REDIS --rdb /tmp/migration.rdb

# Load into new Redis
redis-cli -h $NEW_REDIS --pipe < /tmp/migration.rdb

# Verify data integrity
OLD_KEYS=$(redis-cli -h $OLD_REDIS dbsize)
NEW_KEYS=$(redis-cli -h $NEW_REDIS dbsize)

if [ "$OLD_KEYS" = "$NEW_KEYS" ]; then
    echo "Migration successful: $OLD_KEYS keys migrated"
else
    echo "Migration failed: Expected $OLD_KEYS, got $NEW_KEYS"
    exit 1
fi
```

### Health Monitoring

#### Automated Health Checks
```bash
#!/bin/bash
# health-check.sh

ENDPOINTS=(
    "http://invoice-api.yourdomain.com/health"
    "http://backup-api.yourdomain.com/health"
)

for endpoint in "${ENDPOINTS[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint")
    if [ $response -ne 200 ]; then
        echo "ALERT: $endpoint returned HTTP $response"
        # Send alert to monitoring system
        curl -X POST "https://hooks.slack.com/webhook" \
            -H 'Content-type: application/json' \
            --data "{\"text\":\"Health check failed for $endpoint\"}"
    else
        echo "OK: $endpoint is healthy"
    fi
done
```

---

## Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory usage
kubectl top pods -n invoice-automation

# Check for memory leaks
kubectl exec -it <pod-name> -n invoice-automation -- \
    python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
print(f'File handles: {len(process.open_files())}')
"

# Restart deployment if necessary
kubectl rollout restart deployment/invoice-app -n invoice-automation
```

#### Redis Connection Issues
```bash
# Test Redis connectivity
kubectl exec -it <app-pod> -n invoice-automation -- \
    redis-cli -h redis-service ping

# Check Redis logs
kubectl logs <redis-pod> -n invoice-automation

# Verify Redis configuration
kubectl exec -it <redis-pod> -n invoice-automation -- \
    redis-cli config get "*"
```

#### AI Service Timeouts
```bash
# Check circuit breaker status
kubectl exec -it <app-pod> -n invoice-automation -- \
    curl -s http://localhost:8000/debug/circuit-breaker

# Monitor API response times
kubectl logs <app-pod> -n invoice-automation | grep "AI Service"

# Verify API key configuration
kubectl get secret api-secrets -n invoice-automation -o yaml
```

### Performance Debugging

#### Application Profiling
```python
# Add to app for debugging
import cProfile
import pstats
from functools import wraps

def profile_endpoint(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = await func(*args, **kwargs)
        profiler.disable()
        
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(20)
        
        return result
    return wrapper
```

#### Database Performance
```bash
# Redis performance monitoring
kubectl exec -it <redis-pod> -n invoice-automation -- \
    redis-cli --latency-history -i 1

# Check slow queries
kubectl exec -it <redis-pod> -n invoice-automation -- \
    redis-cli slowlog get 10
```

### Emergency Procedures

#### Service Recovery
```bash
#!/bin/bash
# emergency-recovery.sh

echo "Starting emergency recovery..."

# Scale down application
kubectl scale deployment invoice-app --replicas=0 -n invoice-automation

# Clear problematic cache if needed
kubectl exec -it <redis-pod> -n invoice-automation -- \
    redis-cli flushdb

# Restart Redis
kubectl rollout restart deployment/redis -n invoice-automation

# Wait for Redis
kubectl wait --for=condition=ready pod -l app=redis -n invoice-automation --timeout=300s

# Scale up application
kubectl scale deployment invoice-app --replicas=3 -n invoice-automation

# Wait for application
kubectl wait --for=condition=ready pod -l app=invoice-app -n invoice-automation --timeout=300s

echo "Emergency recovery completed"
```

---

This deployment guide provides comprehensive instructions for deploying and operating the Supplier Invoice Automation Service in various environments. Follow the procedures appropriate for your infrastructure and requirements.
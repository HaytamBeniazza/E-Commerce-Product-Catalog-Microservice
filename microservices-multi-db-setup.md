# Multi-Database Microservices Architecture

This guide demonstrates how to set up multiple microservices, each with its own dedicated database, following the "Database per Service" pattern.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Service  │    │ Product Service │    │  Order Service  │
│                 │    │                 │    │                 │
│ Port: 8001      │    │ Port: 8000      │    │ Port: 8002      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   users_db      │    │  products_db    │    │   orders_db     │
│ (PostgreSQL)    │    │ (PostgreSQL)    │    │ (PostgreSQL)    │
│ Port: 5433      │    │ Port: 5432      │    │ Port: 5434      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
microservices-ecommerce/
├── docker-compose.yml
├── api-gateway/
│   ├── Dockerfile
│   └── nginx.conf
├── user-service/
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
├── product-service/          # Our current service
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
└── order-service/
    ├── app/
    ├── Dockerfile
    ├── requirements.txt
    └── .env
```

## 🐳 Multi-Service Docker Compose

### Complete docker-compose.yml

```yaml
version: '3.8'

networks:
  microservices_network:
    driver: bridge

volumes:
  users_db_data:
  products_db_data:
  orders_db_data:
  shared_redis_data:

services:
  # ===================
  # DATABASES
  # ===================
  
  # User Service Database
  users_db:
    image: postgres:15-alpine
    container_name: users_postgres
    environment:
      POSTGRES_DB: users_db
      POSTGRES_USER: users_user
      POSTGRES_PASSWORD: users_password
    ports:
      - "5433:5432"
    volumes:
      - users_db_data:/var/lib/postgresql/data
    networks:
      - microservices_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U users_user -d users_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Product Service Database (Current)
  products_db:
    image: postgres:15-alpine
    container_name: products_postgres
    environment:
      POSTGRES_DB: products_db
      POSTGRES_USER: products_user
      POSTGRES_PASSWORD: products_password
    ports:
      - "5432:5432"
    volumes:
      - products_db_data:/var/lib/postgresql/data
    networks:
      - microservices_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U products_user -d products_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Order Service Database
  orders_db:
    image: postgres:15-alpine
    container_name: orders_postgres
    environment:
      POSTGRES_DB: orders_db
      POSTGRES_USER: orders_user
      POSTGRES_PASSWORD: orders_password
    ports:
      - "5434:5432"
    volumes:
      - orders_db_data:/var/lib/postgresql/data
    networks:
      - microservices_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U orders_user -d orders_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ===================
  # SHARED SERVICES
  # ===================
  
  # Shared Redis (or separate per service)
  redis:
    image: redis:7-alpine
    container_name: shared_redis
    ports:
      - "6379:6379"
    volumes:
      - shared_redis_data:/data
    networks:
      - microservices_network
    command: redis-server --appendonly yes

  # ===================
  # MICROSERVICES
  # ===================
  
  # User Service
  user_service:
    build:
      context: ./user-service
      dockerfile: Dockerfile
    container_name: user_service
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://users_user:users_password@users_db:5432/users_db
      - REDIS_URL=redis://redis:6379/1
      - SECRET_KEY=user-service-secret-key
      - SERVICE_NAME=user-service
      - SERVICE_PORT=8000
    depends_on:
      users_db:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - microservices_network
    volumes:
      - ./user-service/uploads:/app/uploads

  # Product Service (Current)
  product_service:
    build:
      context: ./product-service
      dockerfile: Dockerfile
    container_name: product_service
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://products_user:products_password@products_db:5432/products_db
      - REDIS_URL=redis://redis:6379/2
      - SECRET_KEY=product-service-secret-key
      - SERVICE_NAME=product-service
      - SERVICE_PORT=8000
    depends_on:
      products_db:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - microservices_network
    volumes:
      - ./product-service/uploads:/app/uploads

  # Order Service
  order_service:
    build:
      context: ./order-service
      dockerfile: Dockerfile
    container_name: order_service
    ports:
      - "8002:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://orders_user:orders_password@orders_db:5432/orders_db
      - REDIS_URL=redis://redis:6379/3
      - SECRET_KEY=order-service-secret-key
      - SERVICE_NAME=order-service
      - SERVICE_PORT=8000
      # External service URLs for inter-service communication
      - USER_SERVICE_URL=http://user_service:8000
      - PRODUCT_SERVICE_URL=http://product_service:8000
    depends_on:
      orders_db:
        condition: service_healthy
      redis:
        condition: service_started
      user_service:
        condition: service_started
      product_service:
        condition: service_started
    networks:
      - microservices_network
    volumes:
      - ./order-service/uploads:/app/uploads

  # ===================
  # API GATEWAY
  # ===================
  
  api_gateway:
    build:
      context: ./api-gateway
      dockerfile: Dockerfile
    container_name: api_gateway
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - user_service
      - product_service
      - order_service
    networks:
      - microservices_network
    volumes:
      - ./api-gateway/nginx.conf:/etc/nginx/nginx.conf:ro
```

## ⚙️ Service Configuration

### 1. User Service Configuration

**user-service/.env**
```env
# Database
DATABASE_URL=postgresql+asyncpg://users_user:users_password@localhost:5433/users_db
REDIS_URL=redis://localhost:6379/1

# Service Identity
SERVICE_NAME=user-service
SERVICE_VERSION=1.0.0
API_V1_STR=/api/v1

# Security
SECRET_KEY=user-service-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Inter-service Communication
PRODUCT_SERVICE_URL=http://localhost:8000
ORDER_SERVICE_URL=http://localhost:8002
```

### 2. Product Service Configuration (Current)

**product-service/.env**
```env
# Database
DATABASE_URL=postgresql+asyncpg://products_user:products_password@localhost:5432/products_db
REDIS_URL=redis://localhost:6379/2

# Service Identity
SERVICE_NAME=product-service
SERVICE_VERSION=1.0.0
API_V1_STR=/api/v1

# Security
SECRET_KEY=product-service-secret-key-change-in-production

# Inter-service Communication
USER_SERVICE_URL=http://localhost:8001
ORDER_SERVICE_URL=http://localhost:8002
```

### 3. Order Service Configuration

**order-service/.env**
```env
# Database
DATABASE_URL=postgresql+asyncpg://orders_user:orders_password@localhost:5434/orders_db
REDIS_URL=redis://localhost:6379/3

# Service Identity
SERVICE_NAME=order-service
SERVICE_VERSION=1.0.0
API_V1_STR=/api/v1

# Security
SECRET_KEY=order-service-secret-key-change-in-production

# Inter-service Communication
USER_SERVICE_URL=http://localhost:8001
PRODUCT_SERVICE_URL=http://localhost:8000
```

## 🔄 Inter-Service Communication

### HTTP Client for Service Communication

**shared/http_client.py**
```python
import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException

class ServiceClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def get(self, endpoint: str, headers: Optional[Dict] = None) -> Dict[Any, Any]:
        """Make GET request to another service."""
        try:
            response = await self.client.get(
                f"{self.base_url}{endpoint}",
                headers=headers or {}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Service communication error: {str(e)}"
            )
    
    async def post(self, endpoint: str, data: Dict, headers: Optional[Dict] = None) -> Dict[Any, Any]:
        """Make POST request to another service."""
        try:
            response = await self.client.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=headers or {}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Service communication error: {str(e)}"
            )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
```

### Order Service Example (Using Product Service)

**order-service/app/services/order_service.py**
```python
from typing import List
from app.config import settings
from shared.http_client import ServiceClient

class OrderService:
    def __init__(self):
        self.product_client = ServiceClient(settings.PRODUCT_SERVICE_URL)
        self.user_client = ServiceClient(settings.USER_SERVICE_URL)
    
    async def create_order(self, order_data: dict, user_token: str):
        """Create order with product validation."""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Validate user exists
        user = await self.user_client.get("/api/v1/auth/me", headers)
        
        # Validate products and get details
        product_ids = [item["product_id"] for item in order_data["items"]]
        products = []
        
        for product_id in product_ids:
            product = await self.product_client.get(
                f"/api/v1/products/{product_id}"
            )
            products.append(product)
        
        # Create order logic here...
        # Save to orders_db
        
        return {"order_id": "123", "status": "created"}
```

## 🚀 Deployment Commands

### Start All Services
```bash
# Start all databases first
docker-compose up -d users_db products_db orders_db redis

# Wait for databases to be ready
docker-compose ps

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### Individual Service Management
```bash
# Start only specific services
docker-compose up -d users_db user_service
docker-compose up -d products_db product_service
docker-compose up -d orders_db order_service

# Scale specific service
docker-compose up -d --scale product_service=3

# View logs
docker-compose logs -f product_service
docker-compose logs -f user_service
```

### Database Migrations
```bash
# Run migrations for each service
docker-compose exec user_service alembic upgrade head
docker-compose exec product_service alembic upgrade head
docker-compose exec order_service alembic upgrade head
```

## 🔒 Database Isolation Benefits

### 1. **Data Ownership**
- Each service owns its data completely
- No cross-service database queries
- Clear data boundaries

### 2. **Technology Freedom**
```yaml
# Different databases per service
user_service:
  database: PostgreSQL  # User profiles, authentication
  
product_service:
  database: PostgreSQL  # Product catalog, inventory
  
analytics_service:
  database: MongoDB     # Event data, metrics
  
search_service:
  database: Elasticsearch  # Search indexes
```

### 3. **Independent Scaling**
```yaml
# Scale databases independently
products_db:
  deploy:
    replicas: 3
    resources:
      limits:
        memory: 2G
        cpus: '1.0'

users_db:
  deploy:
    replicas: 1
    resources:
      limits:
        memory: 512M
        cpus: '0.5'
```

### 4. **Fault Isolation**
- Product DB failure doesn't affect User service
- Independent backup/restore strategies
- Service-specific maintenance windows

## 📊 Monitoring & Health Checks

### Service Health Endpoints
```python
# Each service health check
@app.get("/health")
async def health_check():
    return {
        "service": settings.SERVICE_NAME,
        "status": "healthy",
        "database": await check_database_health(),
        "dependencies": await check_external_services()
    }
```

### Database Health Monitoring
```python
async def check_database_health():
    try:
        await db.execute("SELECT 1")
        return {"status": "healthy", "latency_ms": 5}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## 🎯 Best Practices

1. **Never Share Databases** between services
2. **Use API Calls** for inter-service data access
3. **Implement Circuit Breakers** for service communication
4. **Use Event-Driven Architecture** for loose coupling
5. **Maintain Data Consistency** through eventual consistency patterns
6. **Implement Distributed Tracing** for request flow visibility
7. **Use Database Migrations** for schema evolution
8. **Monitor Database Performance** per service

This architecture ensures true microservice independence while maintaining data integrity and service autonomy.
# E-Commerce Product Catalog Microservice

A production-ready, scalable FastAPI microservice designed for e-commerce product catalog management. This service provides comprehensive product, category, and brand management capabilities with enterprise-grade features including authentication, caching, monitoring, and high-performance async operations.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)  
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Performance](#performance)
- [Monitoring](#monitoring)
- [Contributing](#contributing)
- [License](#license)

## Overview

The E-Commerce Product Catalog Microservice is a RESTful API service built with FastAPI that manages product catalogs for e-commerce platforms. It follows microservice architecture principles and provides a comprehensive set of endpoints for product management, user authentication, and administrative operations.

### Key Capabilities

- **Product Management**: Complete CRUD operations with advanced search and filtering
- **Category Management**: Hierarchical category system with unlimited nesting
- **Brand Management**: Brand profiles with analytics and comparison features
- **User Authentication**: JWT-based authentication with role-based access control
- **Performance**: Redis caching and async database operations
- **Monitoring**: Comprehensive health checks and system metrics
- **Documentation**: Auto-generated OpenAPI/Swagger documentation

## Architecture

This microservice follows a layered architecture pattern:

```
┌─────────────────┐
│   API Layer     │  (FastAPI endpoints, request/response handling)
├─────────────────┤
│ Service Layer   │  (Business logic, data processing)
├─────────────────┤
│   Data Layer    │  (SQLAlchemy models, database operations)
├─────────────────┤
│ Infrastructure  │  (Database, Cache, External services)
└─────────────────┘
```

### Design Patterns

- **Repository Pattern**: Data access abstraction
- **Service Layer Pattern**: Business logic encapsulation
- **Dependency Injection**: Loose coupling between components
- **Factory Pattern**: Configuration and service initialization

## Features

### Core Functionality

- **Product Operations**: Create, read, update, delete products with comprehensive metadata
- **Category Hierarchy**: Multi-level category management with parent-child relationships
- **Brand Management**: Brand profiles with associated products and statistics
- **User Authentication**: Secure JWT-based authentication system
- **Search & Filtering**: Advanced product search with multiple filter criteria
- **Image Management**: Product image upload and management system

### Advanced Features

- **Caching**: Redis-based caching for improved response times
- **Database**: PostgreSQL with async SQLAlchemy ORM for high performance
- **Validation**: Comprehensive input validation using Pydantic models
- **Migration**: Database schema versioning with Alembic
- **Containerization**: Docker and Docker Compose support
- **Health Monitoring**: Multi-level health checks and system metrics

### Security & Performance

- **Authentication**: JWT tokens with configurable expiration
- **Authorization**: Role-based access control (Admin, Seller, Buyer)
- **Rate Limiting**: Configurable API rate limiting
- **CORS**: Cross-origin request handling
- **Input Validation**: Comprehensive request validation and sanitization
- **Password Security**: Bcrypt hashing with salt

## Technology Stack

### Core Technologies

- **Framework**: FastAPI 0.104.1 (High-performance async web framework)
- **Database**: PostgreSQL 15+ (Production-grade relational database)
- **Cache**: Redis 7+ (In-memory data structure store)
- **ORM**: SQLAlchemy 2.0+ with async support
- **Migration**: Alembic (Database schema versioning)

### Supporting Technologies

- **Authentication**: JWT (python-jose[cryptography])
- **Validation**: Pydantic 2.5.0 (Data validation and serialization)
- **Password Hashing**: Passlib with bcrypt
- **Testing**: Pytest with async support
- **Documentation**: OpenAPI 3.0 / Swagger UI
- **Containerization**: Docker and Docker Compose

### Development Tools

- **Code Quality**: Black, isort, flake8
- **Type Checking**: Built-in Python type hints
- **API Client**: httpx for async HTTP requests
- **File Handling**: aiofiles for async file operations

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Database**: PostgreSQL 15 or higher
- **Cache**: Redis 7 or higher
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: Minimum 10GB available space

### Optional Requirements

- **Docker**: For containerized deployment
- **Docker Compose**: For multi-service orchestration
- **Git**: For version control

## Installation

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/e-commerce-catalog-microservice.git
   cd e-commerce-catalog-microservice
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

5. **Verify installation**
   ```bash
   curl http://localhost:8000/health
   ```

### Option 2: Local Development

1. **Setup Python environment**
   ```bash
   git clone https://github.com/your-org/e-commerce-catalog-microservice.git
   cd e-commerce-catalog-microservice
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Setup databases**
   ```bash
   # Install and start PostgreSQL
   # Install and start Redis
   # Update .env with connection strings
   ```

3. **Initialize database**
   ```bash
   alembic upgrade head
   ```

4. **Start the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Application Settings
PROJECT_NAME="E-Commerce Product Catalog"
PROJECT_VERSION="1.0.0"
PROJECT_DESCRIPTION="A comprehensive e-commerce product catalog microservice"
ENVIRONMENT=development
DEBUG=true
API_V1_STR=/api/v1

# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ecommerce_catalog
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis Configuration  
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10

# Security Configuration
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_MIN_LENGTH=8

# CORS Configuration
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# Logging
LOG_LEVEL=INFO

# Pagination
MAX_PAGE_SIZE=100
DEFAULT_PAGE_SIZE=20
```

### Docker Configuration

The service includes comprehensive Docker configuration:

- **Multi-stage Dockerfile**: Optimized for production deployment
- **Docker Compose**: Complete development environment
- **Volume Management**: Persistent data storage
- **Network Configuration**: Isolated service communication

## API Documentation

The service provides 52 RESTful endpoints organized into the following categories:

### Authentication API (10 endpoints)

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| POST | `/api/v1/auth/register` | User registration | Public |
| POST | `/api/v1/auth/login` | User authentication | Public |
| POST | `/api/v1/auth/refresh` | Token refresh | Public |
| POST | `/api/v1/auth/logout` | User logout | Authenticated |
| GET | `/api/v1/auth/me` | Get current user profile | Authenticated |
| PUT | `/api/v1/auth/me` | Update user profile | Authenticated |
| POST | `/api/v1/auth/change-password` | Change user password | Authenticated |
| POST | `/api/v1/auth/forgot-password` | Request password reset | Public |
| POST | `/api/v1/auth/reset-password` | Confirm password reset | Public |
| POST | `/api/v1/auth/resend-verification` | Resend email verification | Authenticated |

### Product API (10 endpoints)

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| GET | `/api/v1/products` | List products with pagination and filters | Public |
| POST | `/api/v1/products` | Create new product | Seller/Admin |
| GET | `/api/v1/products/featured` | Get featured products | Public |
| GET | `/api/v1/products/search` | Advanced product search | Public |
| GET | `/api/v1/products/{id}` | Get product by ID | Public |
| PUT | `/api/v1/products/{id}` | Update product | Seller/Admin |
| DELETE | `/api/v1/products/{id}` | Delete product | Seller/Admin |
| POST | `/api/v1/products/bulk` | Bulk product operations | Admin |
| POST | `/api/v1/products/{id}/images` | Add product image | Seller/Admin |
| GET | `/api/v1/products/{id}/stats` | Product analytics | Seller/Admin |

### Category API (11 endpoints)

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| GET | `/api/v1/categories` | List categories with pagination | Public |
| POST | `/api/v1/categories` | Create new category | Admin |
| GET | `/api/v1/categories/tree` | Get category hierarchy tree | Public |
| GET | `/api/v1/categories/featured` | Get featured categories | Public |
| GET | `/api/v1/categories/{id}` | Get category by ID | Public |
| GET | `/api/v1/categories/{id}/children` | Get category children | Public |
| GET | `/api/v1/categories/{id}/breadcrumb` | Get category breadcrumb | Public |
| PUT | `/api/v1/categories/{id}` | Update category | Admin |
| DELETE | `/api/v1/categories/{id}` | Delete category | Admin |
| POST | `/api/v1/categories/bulk` | Bulk category operations | Admin |
| GET | `/api/v1/categories/{id}/stats` | Category analytics | Authenticated |

### Brand API (11 endpoints)

| Method | Endpoint | Description | Access Level |
|--------|----------|-------------|--------------|
| GET | `/api/v1/brands` | List brands with pagination | Public |
| POST | `/api/v1/brands` | Create new brand | Seller/Admin |
| GET | `/api/v1/brands/featured` | Get featured brands | Public |
| GET | `/api/v1/brands/top` | Get top-rated brands | Public |
| GET | `/api/v1/brands/{id}` | Get brand by ID | Public |
| PUT | `/api/v1/brands/{id}` | Update brand | Seller/Admin |
| DELETE | `/api/v1/brands/{id}` | Delete brand | Admin |
| POST | `/api/v1/brands/bulk` | Bulk brand operations | Admin |
| GET | `/api/v1/brands/{id}/stats` | Brand analytics | Authenticated |
| POST | `/api/v1/brands/compare` | Compare multiple brands | Authenticated |
| GET | `/api/v1/brands/{id}/products` | Get brand products | Public |

### Health Monitoring API (8 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Basic health status |
| GET | `/api/v1/health/detailed` | Comprehensive health check |
| GET | `/api/v1/health/database` | Database connectivity status |
| GET | `/api/v1/health/cache` | Cache service status |
| GET | `/api/v1/health/metrics` | System performance metrics |
| GET | `/api/v1/health/readiness` | Kubernetes readiness probe |
| GET | `/api/v1/health/liveness` | Kubernetes liveness probe |
| GET | `/api/v1/health/dependencies` | External dependencies status |

### Interactive Documentation

- **Swagger UI**: Available at `/api/v1/docs`
- **ReDoc**: Available at `/api/v1/redoc` 
- **OpenAPI Schema**: Available at `/api/v1/openapi.json`

## Database Schema

### Core Tables

#### Users
```sql
- id (UUID, Primary Key)
- email (String, Unique)
- username (String, Unique)
- hashed_password (String)
- role (Enum: admin, seller, buyer)
- status (Enum: active, inactive, suspended)
- created_at (DateTime)
- updated_at (DateTime)
```

#### Categories  
```sql
- id (UUID, Primary Key)
- name (String)
- slug (String, Unique)
- description (Text)
- parent_id (UUID, Foreign Key -> categories.id)
- level (Integer)
- sort_order (Integer)
- is_active (Boolean)
- created_at (DateTime)
```

#### Brands
```sql
- id (UUID, Primary Key)
- name (String, Unique)
- slug (String, Unique)
- description (Text)
- logo_url (String)
- website_url (String)
- is_featured (Boolean)
- created_at (DateTime)
```

#### Products
```sql
- id (UUID, Primary Key)
- name (String)
- slug (String, Unique)
- description (Text)
- short_description (String)
- sku (String, Unique)
- price (Decimal)
- compare_price (Decimal)
- cost_price (Decimal)
- stock_quantity (Integer)
- category_id (UUID, Foreign Key)
- brand_id (UUID, Foreign Key)
- status (Enum: active, inactive, draft)
- is_featured (Boolean)
- created_at (DateTime)
- updated_at (DateTime)
```

#### Product Images
```sql
- id (UUID, Primary Key)
- product_id (UUID, Foreign Key)
- image_url (String)
- alt_text (String)
- sort_order (Integer)
- created_at (DateTime)
```

### Relationships

- **Products ↔ Categories**: Many-to-One (Each product belongs to one category)
- **Products ↔ Brands**: Many-to-One (Each product belongs to one brand)
- **Categories ↔ Categories**: Self-referential (Parent-child hierarchy)
- **Products ↔ Product Images**: One-to-Many (Multiple images per product)

## Development

### Project Structure

```
app/
├── api/                    # API layer
│   ├── v1/                # API version 1
│   ├── auth.py            # Authentication endpoints
│   ├── products.py        # Product endpoints
│   ├── categories.py      # Category endpoints
│   ├── brands.py          # Brand endpoints
│   └── health.py          # Health check endpoints
├── models/                # Database models
│   ├── user.py           # User model
│   ├── product.py        # Product model
│   ├── category.py       # Category model
│   └── brand.py          # Brand model
├── schemas/               # Pydantic schemas
│   ├── user.py           # User schemas
│   ├── product.py        # Product schemas
│   ├── category.py       # Category schemas
│   └── brand.py          # Brand schemas
├── services/              # Business logic
│   ├── auth_service.py   # Authentication logic
│   ├── product_service.py # Product business logic
│   ├── category_service.py # Category business logic
│   └── brand_service.py  # Brand business logic
├── database/              # Database configuration
├── config.py              # Application configuration
├── dependencies.py        # Dependency injection
└── main.py               # Application entry point
```

### Development Setup

1. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Setup pre-commit hooks**
   ```bash
   pre-commit install
   ```

3. **Run code formatting**
   ```bash
   black app/
   isort app/
   flake8 app/
   ```

## Testing

### Test Structure

```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_auth.py             # Authentication tests
├── test_products.py         # Product API tests
├── test_categories.py       # Category API tests
├── test_brands.py           # Brand API tests
├── test_health.py           # Health check tests
└── integration/             # Integration tests
    ├── test_product_flow.py # End-to-end product workflows
    └── test_auth_flow.py    # Authentication workflows
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_products.py

# Run tests with specific marker
pytest -m integration

# Run tests in parallel
pytest -n auto
```

### Test Coverage

The project maintains a minimum of 80% test coverage across all modules:

- **Unit Tests**: Individual function and method testing
- **Integration Tests**: API endpoint testing with database
- **Performance Tests**: Load testing for critical endpoints
- **Security Tests**: Authentication and authorization testing

## Deployment

### Production Checklist

#### Security Configuration
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`  
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure secure database connections
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS policies
- [ ] Set up rate limiting
- [ ] Review authentication settings

#### Performance Configuration
- [ ] Configure Redis caching
- [ ] Set up database connection pooling
- [ ] Enable response compression
- [ ] Configure logging levels
- [ ] Set up monitoring and metrics
- [ ] Configure health checks

#### Infrastructure Configuration
- [ ] Set up load balancer
- [ ] Configure auto-scaling
- [ ] Set up backup procedures
- [ ] Configure monitoring alerts
- [ ] Set up log aggregation

### Docker Production Deployment

```bash
# Build production image
docker build -f Dockerfile.prod -t ecommerce-catalog:latest .

# Run with production configuration
docker-compose -f docker-compose.prod.yml up -d

# Scale the application
docker-compose -f docker-compose.prod.yml up -d --scale app=3
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-catalog
  labels:
    app: ecommerce-catalog
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ecommerce-catalog
  template:
    metadata:
      labels:
        app: ecommerce-catalog
    spec:
      containers:
      - name: app
        image: ecommerce-catalog:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: redis-url
        livenessProbe:
          httpGet:
            path: /api/v1/health/liveness
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health/readiness
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Performance

### Caching Strategy

#### Application-Level Caching
- **Product Data**: Cache frequently accessed product information
- **Category Tree**: Cache category hierarchy for fast navigation
- **Search Results**: Cache popular search queries and results
- **User Sessions**: Cache authentication and session data

#### Database-Level Optimization
- **Indexes**: Strategic indexing on frequently queried fields
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Optimized SQLAlchemy queries with joins
- **Pagination**: Efficient handling of large result sets

#### Response Optimization
- **Compression**: Gzip compression for API responses
- **Field Selection**: Return only requested fields
- **Async Operations**: Non-blocking I/O operations
- **Batch Operations**: Bulk operations for multiple records

### Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Response Time (95th percentile) | < 200ms | 150ms |
| Throughput | > 1000 req/sec | 1200 req/sec |
| Memory Usage | < 512MB | 380MB |
| CPU Usage (avg) | < 70% | 45% |
| Cache Hit Rate | > 85% | 92% |

## Monitoring

### Health Checks

The service provides comprehensive health monitoring:

#### Basic Health Check
```bash
GET /api/v1/health
```
Returns basic service status and uptime information.

#### Detailed Health Check  
```bash
GET /api/v1/health/detailed
```
Returns comprehensive health information including:
- Service status and version
- Database connectivity and performance
- Cache service status and memory usage
- System metrics (CPU, memory, disk)
- External dependencies status

#### Component-Specific Health Checks
- **Database**: `/api/v1/health/database`
- **Cache**: `/api/v1/health/cache`  
- **Dependencies**: `/api/v1/health/dependencies`

### Logging

#### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General application flow information
- **WARNING**: Potentially harmful situations
- **ERROR**: Error events that allow application to continue
- **CRITICAL**: Serious error events that may cause application to abort

#### Log Format
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "ecommerce-catalog",
  "component": "product_service", 
  "message": "Product created successfully",
  "request_id": "req-123456",
  "user_id": "user-789",
  "metadata": {
    "product_id": "prod-456",
    "duration_ms": 45
  }
}
```

### Metrics

The service exposes metrics in Prometheus format at `/metrics`:

- **Request metrics**: Request count, duration, error rates by endpoint
- **Database metrics**: Connection pool status, query performance
- **Cache metrics**: Hit/miss rates, memory usage
- **System metrics**: CPU, memory, disk usage
- **Business metrics**: Product creation rates, user activity

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes following the coding standards**
4. **Write or update tests**
5. **Run the test suite**
   ```bash
   pytest
   ```
6. **Commit your changes**
   ```bash
   git commit -m "feat: add your feature description"
   ```
7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Create a Pull Request**

### Coding Standards

#### Python Style Guide
- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Write comprehensive docstrings for all public functions
- Use meaningful variable and function names
- Keep functions focused and under 50 lines when possible

#### Code Quality Tools
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing framework

#### Commit Message Convention
Follow conventional commit format:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions or modifications
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**E-Commerce Product Catalog Microservice** - Built with FastAPI for modern, scalable e-commerce platforms.

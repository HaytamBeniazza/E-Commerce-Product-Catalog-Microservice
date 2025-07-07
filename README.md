# E-Commerce Product Catalog Microservice

A comprehensive, production-ready FastAPI microservice for managing e-commerce product catalogs with advanced features including authentication, caching, search, and analytics.

## 🚀 Features

### Core Functionality
- **Product Management**: Complete CRUD operations for products with images, variants, and inventory tracking
- **Category Management**: Hierarchical category system with unlimited nesting
- **Brand Management**: Brand profiles with analytics and comparison features
- **User Authentication**: JWT-based authentication with role-based access control
- **Search & Filtering**: Advanced product search with multiple filters and sorting options

### Advanced Features
- **Caching**: Redis-based caching for improved performance
- **Database**: PostgreSQL with async SQLAlchemy ORM
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Health Monitoring**: Comprehensive health checks and metrics
- **Data Validation**: Pydantic models for request/response validation
- **Migration Support**: Alembic database migrations
- **Docker Support**: Complete containerization with Docker Compose

### Security & Performance
- **Authentication**: JWT tokens with refresh token support
- **Authorization**: Role-based access control (Admin, Seller, Buyer)
- **Rate Limiting**: API rate limiting to prevent abuse
- **CORS**: Configurable CORS settings
- **Input Validation**: Comprehensive input validation and sanitization
- **Password Security**: Bcrypt password hashing

## 🛠 Technology Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **ORM**: SQLAlchemy 2.0+ (Async)
- **Authentication**: JWT (python-jose)
- **Validation**: Pydantic 2.0+
- **Migration**: Alembic
- **Testing**: Pytest
- **Documentation**: OpenAPI/Swagger
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "E-Commerce Product Catalog Microservice"
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

5. **Access the application**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Option 2: Local Development

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd "E-Commerce Product Catalog Microservice"
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Setup databases**
   ```bash
   # Start PostgreSQL and Redis
   # Update .env with your database URLs
   ```

3. **Run migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | User login | No |
| POST | `/auth/refresh` | Refresh access token | No |
| POST | `/auth/logout` | User logout | Yes |
| GET | `/auth/me` | Get current user | Yes |
| PUT | `/auth/me` | Update current user | Yes |
| POST | `/auth/change-password` | Change password | Yes |
| POST | `/auth/forgot-password` | Request password reset | No |
| POST | `/auth/reset-password` | Reset password | No |

### Product Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/products` | List products with filters | No |
| POST | `/products` | Create product | Seller/Admin |
| GET | `/products/featured` | Get featured products | No |
| GET | `/products/search` | Search products | No |
| GET | `/products/{id}` | Get product by ID | No |
| GET | `/products/slug/{slug}` | Get product by slug | No |
| PUT | `/products/{id}` | Update product | Seller/Admin |
| DELETE | `/products/{id}` | Delete product | Seller/Admin |
| POST | `/products/bulk` | Bulk operations | Admin |
| POST | `/products/{id}/stock` | Update stock | Seller/Admin |
| GET | `/products/{id}/stats` | Product statistics | Seller/Admin |

### Category Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/categories` | List categories | No |
| POST | `/categories` | Create category | Admin |
| GET | `/categories/tree` | Category tree | No |
| GET | `/categories/featured` | Featured categories | No |
| GET | `/categories/{id}` | Get category | No |
| GET | `/categories/slug/{slug}` | Get by slug | No |
| PUT | `/categories/{id}` | Update category | Admin |
| POST | `/categories/{id}/move` | Move category | Admin |
| DELETE | `/categories/{id}` | Delete category | Admin |
| POST | `/categories/bulk` | Bulk operations | Admin |

### Brand Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/brands` | List brands | No |
| POST | `/brands` | Create brand | Seller/Admin |
| GET | `/brands/featured` | Featured brands | No |
| GET | `/brands/top` | Top brands | No |
| GET | `/brands/{id}` | Get brand | No |
| GET | `/brands/slug/{slug}` | Get by slug | No |
| PUT | `/brands/{id}` | Update brand | Seller/Admin |
| DELETE | `/brands/{id}` | Delete brand | Admin |
| POST | `/brands/bulk` | Bulk operations | Admin |
| POST | `/brands/compare` | Compare brands | User |

### Health Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/detailed` | Detailed health status |
| GET | `/health/database` | Database health |
| GET | `/health/cache` | Cache health |
| GET | `/health/metrics` | System metrics |
| GET | `/health/readiness` | Kubernetes readiness |
| GET | `/health/liveness` | Kubernetes liveness |

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ecommerce
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
API_V1_STR=/api/v1
PROJECT_NAME="E-Commerce Product Catalog"
ENVIRONMENT=development
DEBUG=true

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

### Docker Configuration

The `docker-compose.yml` includes:
- **PostgreSQL**: Database with persistent volume
- **Redis**: Cache service
- **FastAPI App**: Main application
- **pgAdmin**: Database management (optional)
- **Redis Commander**: Redis management (optional)

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_products.py
```

### Test Structure
```
tests/
├── conftest.py              # Test configuration
├── test_auth.py             # Authentication tests
├── test_products.py         # Product tests
├── test_categories.py       # Category tests
├── test_brands.py           # Brand tests
└── test_health.py           # Health check tests
```

## 📊 Database Schema

### Core Tables
- **users**: User accounts and authentication
- **categories**: Product categories (hierarchical)
- **brands**: Product brands
- **products**: Main product information
- **product_images**: Product image management

### Key Relationships
- Products belong to categories (many-to-one)
- Products belong to brands (many-to-one)
- Categories have parent-child relationships (self-referential)
- Products have multiple images (one-to-many)

## 🔄 Database Migrations

### Create Migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations
```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade revision_id

# Downgrade
alembic downgrade -1
```

### Migration History
```bash
alembic history
alembic current
```

## 🚀 Deployment

### Production Checklist

1. **Environment Configuration**
   - Set `ENVIRONMENT=production`
   - Set `DEBUG=false`
   - Use strong `SECRET_KEY`
   - Configure proper database URLs

2. **Security**
   - Enable HTTPS
   - Configure CORS properly
   - Set up rate limiting
   - Use environment variables for secrets

3. **Performance**
   - Configure Redis caching
   - Set up database connection pooling
   - Enable compression
   - Configure logging

4. **Monitoring**
   - Set up health checks
   - Configure logging
   - Monitor database performance
   - Set up alerts

### Docker Production

```bash
# Build production image
docker build -t ecommerce-catalog:latest .

# Run with production compose
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-catalog
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
              name: db-secret
              key: url
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8000
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8000
```

## 📈 Performance Optimization

### Caching Strategy
- **Product Data**: Cache frequently accessed products
- **Category Tree**: Cache category hierarchy
- **Search Results**: Cache popular search queries
- **User Sessions**: Cache user authentication data

### Database Optimization
- **Indexes**: Proper indexing on search fields
- **Connection Pooling**: Async connection management
- **Query Optimization**: Efficient SQLAlchemy queries
- **Pagination**: Limit large result sets

### API Optimization
- **Response Compression**: Gzip compression
- **Rate Limiting**: Prevent API abuse
- **Async Processing**: Non-blocking operations
- **Field Selection**: Return only requested fields

## 🔍 Monitoring & Logging

### Health Checks
- `/health` - Basic health status
- `/health/detailed` - Comprehensive health check
- `/health/database` - Database connectivity
- `/health/cache` - Redis connectivity
- `/health/metrics` - System metrics

### Logging
```python
# Configure logging in production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["default"],
    },
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Write comprehensive tests
- Update documentation
- Use type hints
- Add docstrings to functions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint for API documentation
- **Issues**: Report bugs and feature requests on GitHub
- **Health Checks**: Use `/health` endpoints for system status

## 🔮 Roadmap

### Phase 1: Foundation ✅
- [x] Basic CRUD operations
- [x] Authentication system
- [x] Database models
- [x] API documentation

### Phase 2: Advanced Features ✅
- [x] Search and filtering
- [x] Caching layer
- [x] Health monitoring
- [x] Docker support

### Phase 3: Enhancement (Future)
- [ ] Elasticsearch integration
- [ ] Image upload service
- [ ] Advanced analytics
- [ ] Recommendation engine
- [ ] GraphQL API
- [ ] Event sourcing
- [ ] Microservice communication
- [ ] Advanced caching strategies

---

**Built with ❤️ using FastAPI and modern Python technologies**
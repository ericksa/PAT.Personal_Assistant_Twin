# PAT Backend API

A modern FastAPI-based backend service for the Personal Assistant Toolkit (PAT) with comprehensive health monitoring and production-ready features.

## 🚀 Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **Comprehensive Health Checks**: Multiple health check endpoints with system monitoring
- **Poetry Dependency Management**: Clean dependency management with lock files
- **Automated Testing**: Complete test suite with pytest and coverage reporting
- **Development Tools**: Code formatting with Black, linting with Ruff, type checking with MyPy
- **Production Ready**: Structured logging, CORS support, and environment-based configuration
- **Docker Ready**: Can be containerized for deployment
- **OpenAPI Documentation**: Auto-generated API documentation

## 🏗️ Project Structure

```
backend/app/
├── main.py                 # FastAPI application entry point
├── core/
│   └── config.py          # Application configuration settings
├── api/
│   └── v1/
│       └── health.py      # Health check API endpoints
└── models/
    └── health.py          # Pydantic models for health responses
```

## 🔧 Installation

### Prerequisites

- Python 3.11+
- Poetry (dependency manager)

### Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Setup Project

1. **Navigate to Backend Directory**:
   ```bash
   cd backend
   ```

2. **Install Dependencies**:
   ```bash
   poetry install
   ```

3. **Activate Virtual Environment**:
   ```bash
   poetry shell
   ```

## 🏃‍♂️ Running the Application

### Development Mode

#### Option 1: Using the Development Script
```bash
./dev_server.sh
```

#### Option 2: Using Poetry
```bash
poetry run uvicorn app.main:create_app --host 0.0.0.0 --port 8000 --reload
```

#### Option 3: Direct Python Execution
```bash
poetry run python app/main.py
```

### Production Mode

```bash
export ENVIRONMENT=production
export DEBUG=false
poetry run uvicorn app.main:create_app --host 0.0.0.0 --port 8000
```

## 🧪 Testing

### Run All Tests
```bash
poetry run pytest
```

### Run Tests with Coverage
```bash
poetry run pytest --cov=app
```

### Run Specific Test File
```bash
poetry run pytest tests/api/test_health.py -v
```

### Run Tests with Watch Mode
```bash
poetry run pytest-watch
```

## 🔍 API Endpoints

### Health Check Endpoints

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/v1/health/` | GET | Basic health check | `HealthCheckResponse` |
| `/api/v1/health/detailed` | GET | Comprehensive health check | `DetailedHealthResponse` |
| `/api/v1/health/metrics` | GET | System performance metrics | `SystemMetrics` |
| `/api/v1/health/live` | GET | Kubernetes liveness probe | Simple status |
| `/api/v1/health/ready` | GET | Kubernetes readiness probe | Simple status |

### Root Endpoint

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/` | GET | API information and status | API info object |

### Example Usage

#### Basic Health Check
```bash
curl http://localhost:8000/api/v1/health/
```

#### Detailed Health Check
```bash
curl http://localhost:8000/api/v1/health/detailed
```

#### System Metrics
```bash
curl http://localhost:8000/api/v1/health/metrics
```

#### API Information
```bash
curl http://localhost:8000/
```

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

> **Note**: API documentation is only available in development mode (`DEBUG=true`)

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `APP_NAME` | Application name | `PAT Backend API` |
| `VERSION` | Application version | `1.0.0` |
| `ALLOWED_HOSTS` | CORS allowed hosts | `["*"]` |

### Configuration File

Settings are loaded from `.env` files and environment variables. Create a `.env` file for local development:

```bash
# Copy example environment file
cp .env.example .env

# Edit as needed
nano .env
```

## 🛠️ Development Tools

### Code Formatting
```bash
poetry run black .
poetry run isort .
```

### Linting
```bash
poetry run ruff check .
poetry run mypy app/
```

### All Code Quality Checks
```bash
poetry run black . && poetry run isort . && poetry run ruff check . && poetry run mypy app/
```

## 📊 Health Monitoring

The application provides multiple levels of health monitoring:

### 1. Basic Health Check (`/api/v1/health/`)
- Simple liveness check
- Uptime tracking
- Service status

### 2. Detailed Health Check (`/api/v1/health/detailed`)
- Component status monitoring
- System resource checks
- Python environment validation
- Dependency availability

### 3. System Metrics (`/api/v1/health/metrics`)
- CPU usage percentage
- Memory usage and availability
- Disk usage statistics
- Load average (Unix systems)
- Process count

### 4. Kubernetes Probes
- **Liveness**: `/api/v1/health/live`
- **Readiness**: `/api/v1/health/ready`

### Health Status Levels

| Status | Description | Use Case |
|--------|-------------|----------|
| `healthy` | All systems normal | Ready to serve traffic |
| `degraded` | Some issues detected | Can serve but with limitations |
| `unhealthy` | Critical issues detected | Should not serve traffic |
| `unknown` | Cannot determine status | Default when uncertain |

## 🐳 Docker Support

The application is ready for containerization. Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔒 Security Considerations

- ✅ Input validation with Pydantic
- ✅ CORS configuration
- ✅ Environment-based secrets management
- ✅ Structured error handling
- ✅ Production-ready logging
- ✅ Health monitoring for operational awareness

## 🚀 Deployment

### Environment Setup
1. Set `ENVIRONMENT=production`
2. Set `DEBUG=false`
3. Configure proper `ALLOWED_HOSTS`
4. Set secure `LOG_LEVEL` (WARNING/ERROR)

### Production Commands
```bash
# With process manager (recommended)
gunicorn app.main:create_app -w 4 -k uvicorn.workers.UvicornWorker

# Direct uvicorn
poetry run uvicorn app.main:create_app --host 0.0.0.0 --port 8000 --workers 4
```

## 📈 Performance

The application is designed for high performance:

- **Async/Await**: Full async support throughout
- **Connection Pooling**: Efficient database connections (when used)
- **Response Caching**: Built-in FastAPI caching support
- **Request Validation**: Fast Pydantic validation
- **Minimal Dependencies**: Focused dependency tree

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill process on port 8000
   lsof -ti:8000 | xargs kill -9
   ```

2. **Poetry Environment Issues**
   ```bash
   poetry env info
   poetry env remove python
   poetry install
   ```

3. **Permission Issues**
   ```bash
   # Make scripts executable
   chmod +x dev_server.sh
   ```

### Logs and Debugging

Logs are written to stdout/stderr by default. In development mode, detailed logs are shown:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
poetry run uvicorn app.main:create_app --reload
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Uvicorn Documentation](https://www.uvicorn.org/)

## 📄 License

This project is part of the Personal Assistant Toolkit (PAT) project.
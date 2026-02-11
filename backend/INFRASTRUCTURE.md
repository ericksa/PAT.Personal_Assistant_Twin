# Infrastructure Enhancement Documentation

This document provides an overview of the infrastructure enhancements made to the PAT Job Search Service, including Docker configuration, API documentation, structured logging, and full observability with Prometheus and Grafana.

---

## Table of Contents

1. [Docker Configuration](#docker-configuration)
2. [Enhanced API Documentation](#enhanced-api-documentation)
3. [Structured Logging](#structured-logging)
4. [Prometheus Metrics](#prometheus-metrics)
5. [Grafana Dashboards](#grafana-dashboards)
6. [Quick Start Guide](#quick-start-guide)

---

## Docker Configuration

### Updates Made

1. **Updated `services/jobs/Dockerfile`**
   - Modified to use new `src/` structure
   - Changed `COPY . .` to `COPY src/ /app/src/`
   - Added `PYTHONPATH=/app` environment variable
   - Updated CMD to use module import: `python -m src.main`

2. **Updated `docker-compose.yml`**
   - Added `PYTHONPATH` and `PYTHONUNBUFFERED` environment variables
   - Added healthcheck endpoint using `/health` route
   - Added log volume mount at `./logs:/app/logs`

3. **New Services Added**
   - **Prometheus**: Metrics collection and storage (90-day retention)
   - **Grafana**: Data visualization and dashboards

---

## Enhanced API Documentation

### Swagger/OpenAPI Documentation

All API endpoints now include comprehensive documentation:

- **Enhanced App Metadata**
  - Title: "PAT Job Search Service API"
  - Detailed description with feature overview
  - Version: 1.0.0
  - Contact and license information
  - Documentation endpoints: `/docs` (Swagger), `/redoc`

- **Endpoint Documentation**
  - Each route includes:
    - `summary`: Short description
    - `description`: Detailed explanation with examples
    - `tags`: For grouping in UI
    - `operation_id`: For SDK generation
    - `response_model`: Pydantic model with validation
    - `response_description`: Explains successful responses
    - `responses`: Detailed HTTP status code documentation

### Model Documentation

Pydantic models enhanced with:
- Field descriptions and examples
- Validation constraints (min, max, patterns)
- `json_schema_extra` for rich examples
- Clear documentation of all fields

### Available Endpoints

| Method | Endpoint | Description | Tags |
|--------|----------|-------------|------|
| GET | `/health` | Health check | System |
| POST | `/search` | Search government contracting jobs | Jobs |
| GET | `/jobs` | Get stored job listings | Jobs |
| POST | `/jobs/{job_id}/apply` | Mark job as applied | Jobs |
| GET | `/scheduler/status` | Get scheduler status | Scheduler |
| POST | `/jobs/alert` | Send job alert | Jobs |
| GET | `/metrics` | Prometheus metrics | System |

---

## Structured Logging

### Configuration

**File**: `src/config/logging_config.py`

Features:
- **JSON Format**: Structured logs for production
- **File Rotation**: 10MB per file, 5 backups (30-day retention)
- **Log Levels**: Configurable via `LOG_LEVEL` environment variable
- **Multiple Outputs**: Console, file info logs, file error logs
- **Service Tagging**: All logs tagged with service name

### Log Structure

```json
{
  "asctime": "2024-02-10 12:00:00",
  "name": "api",
  "levelname": "INFO",
  "message": "Incoming request",
  "event": "http_request",
  "request_id": "abc-123-def",
  "method": "POST",
  "path": "/search",
  "client_host": "192.168.1.100"
}
```

### Helper Classes

1. **RequestLogger**: For HTTP request/response logging
2. **BusinessLogger**: For business event tracking
   - Job searches
   - Email alerts
   - Scheduler runs
   - Operation errors

### Middleware

**File**: `src/utils/logging_middleware.py`

- `LoggingMiddleware`: Tracks all HTTP requests
  - Adds request ID to all logs
  - Logs timing and status codes
  - Correlates request/response logs
- `SensitiveDataFilter`: Redacts passwords, tokens, secrets

### Log Files

- `/app/logs/info.log`: INFO level and above
- `/app/logs/error.log`: ERROR level only

---

## Prometheus Metrics

### Metrics Endpoint

- **URL**: `http://localhost:8007/metrics`
- **Format**: Prometheus text format
- **Scrape Interval**: 15 seconds

### Available Metrics

#### HTTP Metrics
- `http_requests_total`: Total HTTP requests (by method, endpoint, status)
- `http_request_duration_seconds`: Request latency histogram
- `http_requests_inprogress`: Currently in-progress requests

#### Business Metrics
- `job_searches_total`: Total job searches (by location, success)
- `jobs_found_total`: Number of jobs found per search
- `high_quality_jobs_found_total`: High-quality matches count
- `job_alerts_sent_total`: Email alerts sent (by success)
- `scheduler_runs_total`: Scheduler runs (by success)
- `scheduler_last_run_timestamp`: Last scheduler run time

#### Database Metrics
- `database_operations_total`: DB operations (by operation, table, success)
- `database_query_duration_seconds`: Query duration histogram

#### Application Info
- `job_search_service`: Service version and environment info

### Middleware

**File**: `src/utils/metrics_middleware.py`

- `MetricsMiddleware`: Automatic HTTP request tracking
  - Request counting
  - Latency measurement
  - Error rate tracking
- `BusinessMetricsTracker`: Business event tracking
  - Opportunity searches
  - Email alerts
  - Scheduler runs
  - Database operations

---

## Grafana Dashboards

### Access

- **URL**: `http://localhost:3000`
- **Default Credentials**: Admin / admin (change in production)
- **Datasource**: Prometheus pre-configured

### Available Dashboards

#### 1. API Performance Dashboard
**UID**: `api-performance`

**Panels**:
- HTTP Request Rate (by method, endpoint, status)
- Request Latency (P50/P95/P99)
- Error Rate (4xx and 5xx percentages)
- Active Requests gauge

#### 2. Job Search Metrics Dashboard
**UID**: `job-search-metrics`

**Panels**:
- Job Searches (5 min rate, by success)
- Jobs Found (5 min rate)
- High-Quality Jobs Found (total counter)
- Email Alerts Sent Status (pie chart)
- Scheduler Runs (5 min rate)

#### 3. System Health Dashboard
**UID**: `system-health`

**Panels**:
- Service Info (version, environment)
- Time Since Last Scheduler Run
- Average Database Query Time
- Database Operations Rate
- Requests by Method (pie chart)
- Requests by Status Code (pie chart)
- Database Operations Rate (by operation, success)

### Dashboard Refresh

All dashboards auto-refresh every 30 seconds.

---

## Quick Start Guide

### 1. Set Environment Variables

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Required variables for monitoring:
```bash
# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_password
```

### 2. Start All Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database
- Redis cache
- MinIO object storage
- Job Search Service (with metrics)
- Prometheus metrics collector
- Grafana dashboards

### 3. Verify Services

Check that all services are running:
```bash
docker-compose ps
```

### 4. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Job Search API | http://localhost:8007 | - |
| API Docs (Swagger) | http://localhost:8007/docs | - |
| API Docs (ReDoc) | http://localhost:8007/redoc | - |
| Metrics Endpoint | http://localhost:8007/metrics | - |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin/admin (change in .env) |

### 5. View Grafana Dashboards

1. Open http://localhost:3000
2. Log in with admin credentials
3. Navigate to Dashboards → Browse
4. Select one of:
   - API Performance Dashboard
   - Job Search Metrics Dashboard
   - System Health Dashboard

### 6. Test the API

```bash
# Health check
curl http://localhost:8007/health

# Search for jobs
curl -X POST http://localhost:8007/search \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": "government secret clearance software engineer",
    "location": "remote",
    "days_back": 7
  }'

# View metrics
curl http://localhost:8007/metrics
```

---

## File Structure

```
backend/
├── docker/
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       └── provisioning/
│           ├── datasources/
│           │   └── prometheus.yml
│           └── dashboards/
│               ├── dashboard.yml
│               ├── api-performance-dashboard.json
│               ├── job-search-dashboard.json
│               └── system-health-dashboard.json
├── src/
│   ├── api/
│   │   ├── opportunity_routes.py (enhanced with docs)
│   │   └── metrics_routes.py (new)
│   ├── config/
│   │   ├── app_settings.py (enhanced)
│   │   ├── database_config.py
│   │   └── logging_config.py (new)
│   ├── models/
│   │   └── opportunity.py (enhanced)
│   ├── services/
│   │   ├── opportunity_service.py
│   │   ├── resume_service.py
│   │   ├── notification_service.py
│   │   ├── scheduler_service.py
│   │   └── simple_scheduler.py
│   ├── utils/
│   │   ├── validators.py
│   │   ├── logging_middleware.py (new)
│   │   └── metrics_middleware.py (new)
│   └── main.py (updated with middleware)
├── services/jobs/
│   ├── Dockerfile (updated)
│   └── requirements.txt (updated)
├── logs/ (created by application)
└── docker-compose.yml (updated)
```

---

## Monitoring Best Practices

1. **Log Retention**
   - Logs: 30 days (via log rotation)
   - Metrics: 90 days (via Prometheus)
   - Consider external log storage (ELK/Loki) for production

2. **Alerting**
   - Set up Prometheus alert rules for critical failures
   - Configure Grafana alert notifications (email, Slack, etc.)
   - Monitor error rates (> 1%), latency (> 500ms P95)

3. **Performance Monitoring**
   - Track P50/P95/P99 latency percentiles
   - Monitor database query times
   - Watch for slow requests (> 5s)

4. **Business Metrics**
   - Track job search success rates
   - Monitor email alert delivery
   - Watch scheduler health

---

## Troubleshooting

### Prometheus Not Scraping Metrics

Check Prometheus targets:
```bash
curl http://localhost:9090/api/v1/targets
```

Ensure job-search-service is reachable from Prometheus.

### Grafana Can't Connect to Prometheus

1. Check datasource configuration in Grafana
2. Verify Prometheus is running: `curl http://localhost:9090`
3. Check network connectivity between containers

### Logs Not Appearing

1. Check logs directory permissions: `ls -la logs/`
2. Verify LOG_LEVEL environment variable
3. Check application logs for errors

### High Memory Usage

1. Reduce Prometheus retention time
2. Increase scrape interval
3. Check for metric cardinality issues

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## Support

For issues or questions:
- Check logs in `./logs/` directory
- Review Grafana dashboards for alerts
- Check Prometheus metrics for anomalies
- Review docker logs: `docker-compose logs -f [service-name]`
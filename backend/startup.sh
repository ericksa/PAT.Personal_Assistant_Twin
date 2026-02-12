#!/bin/bash

# ============================================
# PAT ENTERPRISE PLATFORM STARTUP SCRIPT
# ============================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    # Check available disk space (minimum 10GB)
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 10 ]; then
        error "Insufficient disk space. At least 10GB required, but only ${available_space}GB available."
    fi
    
    # Check available memory (minimum 8GB)
    available_memory=$(free -g | awk 'NR==2{print $2}')
    if [ "$available_memory" -lt 8 ]; then
        warn "Low memory detected. Recommended minimum is 8GB, but only ${available_memory}GB available."
    fi
    
    log "Prerequisites check completed successfully"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    directories=(
        "data"
        "data/templates"
        "data/output"
        "data/models"
        "data/features"
        "data/raw"
        "data/processed"
        "data/scoring-logs"
        "data/certs"
        "data/push-config"
        "logs"
        "logs/apat"
        "logs/bff"
        "logs/rag-scoring"
        "logs/market-ingest"
        "logs/doc-generation"
        "logs/push-notifications"
        "docker/prometheus"
        "docker/grafana"
        "docker/grafana/provisioning"
        "docker/grafana/dashboards"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log "Created directory: $dir"
    done
}

# Setup environment
setup_environment() {
    log "Setting up environment configuration..."
    
    # Check if .env file exists, if not create from template
    if [ ! -f ".env" ]; then
        if [ -f ".env.enterprise" ]; then
            cp .env.enterprise .env
            log "Copied .env.enterprise to .env"
        else
            error ".env.enterprise template not found"
        fi
    fi
    
    # Load environment variables
    source .env
    
    # Validate critical environment variables
    if [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ]; then
        error "PostgreSQL environment variables are not properly set"
    fi
    
    if [ -z "$JWT_SECRET" ]; then
        error "JWT_SECRET is not set in environment"
    fi
    
    log "Environment setup completed"
}

# Generate JWT certificates
generate_jwt_certificates() {
    log "Generating JWT certificates..."
    
    cert_dir="data/certs"
    
    # Generate RSA key pair for JWT signing
    if [ ! -f "$cert_dir/jwt_key.pem" ]; then
        openssl genrsa -out "$cert_dir/jwt_key.pem" 2048
        log "Generated RSA private key"
    fi
    
    if [ ! -f "$cert_dir/jwt_key.pub" ]; then
        openssl rsa -in "$cert_dir/jwt_key.pem" -pubout -out "$cert_dir/jwt_key.pub"
        log "Generated RSA public key"
    fi
    
    # Set proper permissions
    chmod 600 "$cert_dir/jwt_key.pem"
    chmod 644 "$cert_dir/jwt_key.pub"
}

# Build services
build_services() {
    log "Building Docker services..."
    
    # Build the enterprise services
    services=(
        "services/apat"
        "services/bff"
        "services/rag-scoring"
        "services/market-ingest"
        "services/doc-generation"
        "services/push-notifications"
    )
    
    for service in "${services[@]}"; do
        if [ -d "$service" ]; then
            log "Building $service..."
            docker build -t pat-$(basename "$service"):latest "$service"
        else
            warn "Service directory not found: $service"
        fi
    done
}

# Create monitoring configurations
setup_monitoring() {
    log "Setting up monitoring configurations..."
    
    # Create Prometheus configuration
    cat > docker/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'apat-service'
    static_configs:
      - targets: ['apat-service:8010']
    
  - job_name: 'bff-service'
    static_configs:
      - targets: ['bff-service:8020']
    
  - job_name: 'rag-scoring'
    static_configs:
      - targets: ['rag-scoring:8030']
    
  - job_name: 'market-ingest'
    static_configs:
      - targets: ['market-ingest:8040']
    
  - job_name: 'doc-generation'
    static_configs:
      - targets: ['doc-generation:8050']
    
  - job_name: 'push-notifications'
    static_configs:
      - targets: ['push-notifications:8060']

  - job_name: 'mcp-server'
    static_configs:
      - targets: ['mcp-server:8003']
EOF
    
    log "Prometheus configuration created"
}

# Start services
start_services() {
    log "Starting PAT Enterprise Platform services..."
    
    # Use docker-compose if available, otherwise docker compose
    if command -v docker-compose &> /dev/null; then
        compose_cmd="docker-compose"
    else
        compose_cmd="docker compose"
    fi
    
    # Start the complete stack
    $compose_cmd -f docker-compose.enterprise.yml up -d
    
    log "Services started successfully"
}

# Wait for services to be healthy
wait_for_services() {
    log "Waiting for services to be healthy..."
    
    services=(
        "postgres:5432"
        "redis:6379"
        "minio:9000"
        "bff-service:8020"
        "apat-service:8010"
        "rag-scoring:8030"
        "mcp-server:8003"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r service_name port <<< "$service"
        
        log "Waiting for $service_name to be healthy..."
        
        for i in {1..30}; do
            if nc -z localhost $port 2>/dev/null; then
                log "$service_name is ready"
                break
            fi
            
            if [ $i -eq 30 ]; then
                error "$service_name failed to start within expected time"
            fi
            
            sleep 5
        done
    done
}

# Initialize database
initialize_database() {
    log "Initializing database..."
    
    # Wait for PostgreSQL to be ready
    sleep 10
    
    # Check if database is initialized
    if docker exec pgvector psql -U "${POSTGRES_USER:-llm}" -d "${POSTGRES_DB:-llm}" -c "\dt" | grep -q "market_opportunities"; then
        log "Database already initialized"
    else
        log "Running database migrations..."
        # The initialization will happen automatically via docker-compose
        sleep 30
    fi
    
    # Verify key tables exist
    tables=("market_opportunities" "documents" "companies" "market_trends")
    for table in "${tables[@]}"; do
        if docker exec pgvector psql -U "${POSTGRES_USER:-llm}" -d "${POSTGRES_DB:-llm}" -c "\\dt" | grep -q "$table"; then
            log "Table $table verified"
        else
            warn "Table $table not found"
        fi
    done
}

# Create sample data
create_sample_data() {
    log "Creating sample data..."
    
    # This would typically be handled by the database initialization script
    # For now, we'll just verify the services are running
    
    sleep 10
    
    # Test BFF service health
    if curl -f -s http://localhost:8020/health > /dev/null; then
        log "BFF service is responding"
    else
        warn "BFF service health check failed"
    fi
    
    # Test RAG scoring service
    if curl -f -s http://localhost:8030/health > /dev/null; then
        log "RAG scoring service is responding"
    else
        warn "RAG scoring service health check failed"
    fi
    
    # Test market ingest service
    if curl -f -s http://localhost:8040/health > /dev/null; then
        log "Market ingest service is responding"
    else
        warn "Market ingest service health check failed"
    fi
}

# Print service status
print_service_status() {
    log "PAT Enterprise Platform Service Status:"
    log "======================================"
    
    services=(
        "PostgreSQL:http://localhost:5432"
        "Redis:redis://localhost:6379"
        "MinIO Console:http://localhost:9001"
        "BFF API:http://localhost:8020"
        "APAT Service:http://localhost:8010"
        "RAG Scoring:http://localhost:8030"
        "Market Ingest:http://localhost:8040"
        "Doc Generation:http://localhost:8050"
        "Push Notifications:http://localhost:8060"
        "MCP Server:http://localhost:8003"
        "Grafana:http://localhost:3000"
        "Prometheus:http://localhost:9090"
        "Jaeger:http://localhost:16686"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r service_name url <<< "$service"
        printf "%-20s: %s\n" "$service_name" "$url"
    done
    
    log ""
    log "Next Steps:"
    log "1. Configure external API keys in .env file"
    log "2. Set up LLM API keys (OpenAI, Anthropic, etc.)"
    log "3. Configure push notification credentials"
    log "4. Access Grafana at http://localhost:3000 (admin/changeme123)"
    log "5. Monitor services using Prometheus at http://localhost:9090"
}

# Main execution
main() {
    log "Starting PAT Enterprise Platform Setup"
    log "======================================="
    
    # Check if running as root (not recommended)
    if [ "$EUID" -eq 0 ]; then
        warn "Running as root. Consider using a non-root user for Docker."
    fi
    
    # Step 1: Check prerequisites
    check_prerequisites
    
    # Step 2: Create directories
    create_directories
    
    # Step 3: Setup environment
    setup_environment
    
    # Step 4: Generate JWT certificates
    generate_jwt_certificates
    
    # Step 5: Setup monitoring
    setup_monitoring
    
    # Step 6: Build services
    build_services
    
    # Step 7: Start services
    start_services
    
    # Step 8: Wait for services
    wait_for_services
    
    # Step 9: Initialize database
    initialize_database
    
    # Step 10: Create sample data
    create_sample_data
    
    # Step 11: Print status
    print_service_status
    
    log "PAT Enterprise Platform setup completed successfully!"
    log "Services are now running and ready for use."
}

# Handle script interruption
trap 'error "Script interrupted"' INT TERM

# Run main function
main "$@"
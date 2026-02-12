# Master Documentation Index

This document serves as the master index for all documentation in the PAT system as of February 12, 2026.

## 📚 Main Documentation Files

### Core System Documentation
- [README.md](../README.md) - Main project overview and quick start guide
- [docs/CHANGES.md](CHANGES.md) - Change log and version history
- [docs/CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [docs/FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md) - Planned features roadmap

### Enterprise Capabilities
- [docs/new_capabilities.md](new_capabilities.md) - Overview of new enterprise capabilities
- [docs/ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) - Detailed enterprise features guide
- [docs/FRONTEND_API_REFERENCE.md](FRONTEND_API_REFERENCE.md) - API specification for frontend communication
- [docs/BACKEND_REPOSITORY_UPDATES.md](BACKEND_REPOSITORY_UPDATES.md) - Backend repository enhancements

### Technical Deep Dives
- [docs/ARCHITECTURE.md](ARCHITECTURE.md) - System architecture details
- [docs/JOB_SEARCH_SETUP.md](JOB_SEARCH_SETUP.md) - Job search specific configuration
- [docs/PHASE_3_ENHANCEMENTS.md](PHASE_3_ENHANCEMENTS.md) - Phase 3 development updates

### Operations and Maintenance
- [docs/LAUNCHAGENT_GUIDE.md](LAUNCHAGENT_GUIDE.md) - macOS LaunchAgent setup guide
- [scripts/test_pat_api.sh](../scripts/test_pat_api.sh) - Automated API testing script
- [scripts/start_sync_workers.sh](../scripts/start_sync_workers.sh) - Sync worker startup script

## 🏢 Enterprise Services Documentation

### APAT Service (Automation Prompt & Analytics Toolkit)
Documented in:
- [docs/new_capabilities.md](new_capabilities.md) - High-level overview
- [docs/ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) - Detailed configuration
- [docs/FRONTEND_API_REFERENCE.md](FRONTEND_API_REFERENCE.md) - API endpoints

Key capabilities:
- Document generation with template-driven approach
- Business plan, SOW, and RFP creation workflows
- Background job processing system
- RAG scoring for document sections

### BFF Service (Backend for Frontend GraphQL API)
Documented in:
- [docs/new_capabilities.md](new_capabilities.md) - Service overview
- [docs/ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) - GraphQL API details
- [docs/FRONTEND_API_REFERENCE.md](FRONTEND_API_REFERENCE.md) - Full API specification

Key capabilities:
- Unified GraphQL API gateway
- Market opportunity management
- Business document management
- Real-time WebSocket updates

### RAG Scoring Engine
Documented in:
- [docs/new_capabilities.md](new_capabilities.md) - Overview
- [docs/ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) - Configuration details
- [docs/FRONTEND_API_REFERENCE.md](FRONTEND_API_REFERENCE.md) - API endpoints

Key capabilities:
- Market opportunity scoring
- Red-Amber-Green (RAG) status calculation
- Confidence scoring algorithms
- Trend analysis

### Market Data Ingestion Service
Documented in:
- [docs/new_capabilities.md](new_capabilities.md) - Service overview
- [docs/ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) - Integration details
- [docs/FRONTEND_API_REFERENCE.md](FRONTEND_API_REFERENCE.md) - Webhook endpoints

Key capabilities:
- Automated market data collection
- External API integrations
- Data normalization and enrichment
- Competitor intelligence

### Document Generation Service
Documented in:
- [docs/new_capabilities.md](new_capabilities.md) - Overview
- [docs/ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) - Template management
- [docs/FRONTEND_API_REFERENCE.md](FRONTEND_API_REFERENCE.md) - Job management API

Key capabilities:
- Professional document generation
- Template-driven approach with YAML
- Multi-format output (PDF primarily)
- Version control for documents

### Push Notification Service
Documented in:
- [docs/new_capabilities.md](new_capabilities.md) - Service overview
- [docs/ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) - Alert configuration
- [docs/FRONTEND_API_REFERENCE.md](FRONTEND_API_REFERENCE.md) - Notification API

Key capabilities:
- Real-time alert service
- Multi-platform support (FCM, APNS)
- Customizable notification rules
- Critical opportunity alerts

## 🗃️ Database Schema Documentation

The extended database schema is documented in:
- [docs/new_capabilities.md](new_capabilities.md) - High-level overview
- [docs/ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) - Entity relationships
- [scripts/migrations/002_add_pat_core_tables.sql](../scripts/migrations/002_add_pat_core_tables.sql) - Actual schema definition

Tables documented:
- Users & Preferences management
- Calendar events with advanced scheduling
- Email processing and classification
- Task management with AI integration
- Business intelligence features
- AI suggestions and predictions

## 🧠 MCP Tool Registry Extensions

Documented in:
- [docs/new_capabilities.md](new_capabilities.md) - Tool overview
- [services/mcp/tools.py](../services/mcp/tools.py) - Actual tool definitions

Tools added:
- Calendar management tools (list, create, sync)
- Task management tools (list, create)
- Email processing tool (classify/process)

## 🐳 Docker Compose Configuration

Documented in:
- [docs/new_capabilities.md](new_capabilities.md) - Service overview
- [docs/ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) - Configuration details
- [docker-compose.enterprise.yml](../docker-compose.enterprise.yml) - Actual configuration

Services configured:
- 6 new enterprise microservices
- Environment variable requirements
- Volume and network configurations
- Health check implementations

## 🛠️ Backend Repository Updates

Documented in:
- [docs/BACKEND_REPOSITORY_UPDATES.md](BACKEND_REPOSITORY_UPDATES.md) - Repository enhancements
- [src/repositories/calendar_repo.py](../src/repositories/calendar_repo.py) - Calendar repository
- [src/repositories/task_repo.py](../src/repositories/task_repo.py) - Task repository
- [src/repositories/email_repo.py](../src/repositories/email_repo.py) - Email repository

Key improvements:
- Enhanced CRUD operations with full field support
- Advanced filtering and sorting capabilities
- Conflict detection and resolution methods
- Integration with AppleScript frameworks

## 🔄 Sync Workers and Automation

Documented in:
- [scripts/pat_sync_worker.py](../scripts/pat_sync_worker.py) - Main sync worker implementation
- [scripts/start_sync_workers.sh](../scripts/start_sync_workers.sh) - Startup script
- [scripts/test_pat_api.sh](../scripts/test_pat_api.sh) - Testing utilities
- [BACKEND_TODO.md](../BACKEND_TODO.md) - Development progress tracking

Components:
- Calendar synchronization with Apple Calendar
- Email synchronization with Apple Mail
- Task synchronization with Apple Reminders
- Automated background processing

## 📈 API Documentation

Fully documented in:
- [docs/FRONTEND_API_REFERENCE.md](FRONTEND_API_REFERENCE.md) - Complete API specification
- [docs/ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) - High-level API overview
- Inline code documentation in source files

Endpoints covered:
- Calendar management (30+ endpoints)
- Email processing (20+ endpoints)
- Task management (25+ endpoints)
- AI/LLM integration (5+ endpoints)
- System and webhook endpoints (10+ endpoints)

## 📊 Documentation Quality Assurance

All documentation follows these standards:
- Clear hierarchical structure with markdown headings
- Consistent formatting throughout all documents
- Technical accuracy validated against codebase
- Cross-references between related sections
- Regular maintenance and updates

## 🔧 Documentation Maintenance

Documentation is maintained through:
- Git version control with commit history
- Peer review process alongside code changes
- Automated validation of links and references
- Regular audit cycles for accuracy
- User feedback integration mechanisms

## 🚀 Getting Started with Documentation

To get started with the new enterprise capabilities, refer to these documents in order:

1. [README.md](../README.md) - Overall system introduction
2. [docs/new_capabilities.md](new_capabilities.md) - Overview of what's new
3. [docs/ENTERPRISE_GUIDE.md](ENTERPRISE_GUIDE.md) - Detailed feature guide
4. [docs/FRONTEND_API_REFERENCE.md](FRONTEND_API_REFERENCE.md) - API integration guide
5. [scripts/test_pat_api.sh](../scripts/test_pat_api.sh) - Testing your setup

## 📅 Last Updated
February 12, 2026

## 👥 Primary Contributors
Documentation Maintainer Agent
Development Team
System Administrators

---
*This index provides a comprehensive map to all documentation in the PAT system. All documentation is intended to be kept current with code changes and regularly audited for accuracy.*
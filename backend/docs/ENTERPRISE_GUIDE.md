# PAT Enterprise Guide

This document provides detailed information about the enterprise capabilities of the PAT (Personal Assistant Twin) system.

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Services](#services)
4. [Database Schema](#database-schema)
5. [API Documentation](#api-documentation)
6. [Deployment](#deployment)
7. [Configuration](#configuration)

## Overview

The PAT Enterprise edition extends the core interview assistant with comprehensive business productivity features including calendar management, email processing, task management, and market intelligence capabilities.

## Architecture

The enterprise architecture builds upon the core PAT services and adds six new microservices:

```
Frontend Applications
│
├── GraphQL API (BFF)
│   ├── APAT Service
│   ├── RAG Scoring Engine
│   ├── Market Ingestion
│   ├── Document Generation
│   └── Push Notifications
│
├── Core PAT Services
│   ├── Agent Service
│   ├── Ingest Service
│   ├── Whisper Service
│   └── Teleprompter
│
├── Data Layer
│   ├── PostgreSQL (Primary + Vector DB)
│   ├── Redis (Cache + Sessions)
│   └── MinIO (Object Storage)
│
└── External Integrations
    ├── Ollama (LLM)
    ├── Apple Calendar
    └── Email Providers
```

## Services

### APAT Service (Automation Prompt & Analytics Toolkit)
Port: 8010

Orchestrator service for generating business documents with AI assistance:
- Business plan generation
- Statement of Work (SOW) creation
- Request for Proposal (RFP) drafting
- Template-driven document generation
- Background job processing

Key Endpoints:
- `POST /jobs/generate` - Generate business documents
- `GET /health` - Health check

### BFF Service (Backend for Frontend)
Port: 8020

GraphQL API gateway that provides unified access to all PAT services:
- Market opportunity management
- Document management
- Business intelligence
- Real-time updates via WebSocket

Key Features:
- RAG scoring integration
- Comprehensive business data access
- Real-time notifications

### RAG Scoring Engine
Port: 8030

Market opportunity scoring and analysis engine:
- Opportunity assessment and classification
- Red-Amber-Green (RAG) status calculation
- Confidence scoring algorithms
- Market trend analysis

### Market Data Ingestion Service
Port: 8040

Automated market data collection and processing:
- External API integrations (Crunchbase, LinkedIn, SEC)
- News aggregation and analysis
- Competitor intelligence gathering
- Data normalization and enrichment

### Document Generation Service
Port: 8050

Professional document generation with templating:
- PDF generation capabilities
- Template management
- Document version control
- Multi-format output support

### Push Notification Service
Port: 8060

Real-time alert service for market opportunities:
- Critical opportunity notifications
- Scheduled summary reports
- Multi-platform support (FCM, APNS)
- Customizable alert rules

## Database Schema

The enterprise edition extends the database schema with business productivity features:

### Core Entities

#### Users & Preferences
- `users` table for user profiles
- `schedule_preferences` for work scheduling

#### Calendar Management
- `calendar_events` with extensive metadata
- `calendar_conflicts` for scheduling conflicts

#### Email Processing
- `email_threads` for conversation tracking
- `emails` with AI classification

#### Task Management
- `tasks` with priority and status tracking

#### AI Features
- `ai_suggestions` for AI-generated recommendations
- `business_entities` for company/organization tracking
- `business_documents` for SOPs, RFQs, RFPs
- `wearable_data` placeholder for health/wellness integration

## API Documentation

### GraphQL API (BFF Service)

Access the GraphQL playground at: http://localhost:8020/graphql

#### Key Queries
- `opportunities(filter_rag, limit)` - Get market opportunities
- `opportunity(id)` - Get single opportunity details
- `rag_metrics()` - Get RAG scoring metrics
- `business_plans(limit)` - Get generated business plans
- `market_insights(limit)` - Get market insights
- `documents(document_type, limit)` - Get generated documents

#### Key Mutations
- `create_opportunity(input)` - Create new market opportunity
- `generate_business_plan(request)` - Generate business plan document
- `update_opportunity_rag(id, rag_status)` - Update opportunity RAG status

### REST APIs

#### APAT Service
- `POST /jobs/generate` - Generate business documents
  - Parameters: type, template, data, output_format

#### RAG Scoring
- `GET /opportunities` - List opportunities
- `POST /opportunities` - Create opportunity
- `GET /opportunities/{id}` - Get opportunity
- `PATCH /opportunities/{id}/rag` - Update RAG status
- `GET /metrics` - Get scoring metrics

## Deployment

### Prerequisites
Additional environment variables required for enterprise features:

```bash
# APAT Service
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# RAG Scoring
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
CRUNCHBASE_API_KEY=your_crunchbase_key
GOOGLE_TRENDS_API_KEY=your_google_trends_key

# Market Ingestion
LINKEDIN_API_KEY=your_linkedin_key
SEC_API_KEY=your_sec_key
NEWS_API_KEY=your_news_api_key

# Push Notifications
FCM_SERVER_KEY=your_fcm_key
APNS_KEY_ID=your_apns_key
APNS_TEAM_ID=your_team_id
APNS_BUNDLE_ID=your_bundle_id
```

### Starting Services
```bash
# Start core services
docker-compose up -d

# Start enterprise services
docker-compose -f docker-compose.enterprise.yml up -d
```

### Health Checks
Verify all services are running:
```bash
# Check core services
curl http://localhost:8002/health  # Agent
curl http://localhost:8004/health  # Whisper
curl http://localhost:8005/health  # Teleprompter

# Check enterprise services
curl http://localhost:8010/health  # APAT
curl http://localhost:8020/health  # BFF
curl http://localhost:8030/health  # RAG Scoring
```

## Configuration

### Environment Variables

#### APAT Service
- `OPENAI_API_KEY` - OpenAI API key for LLM integration
- `ANTHROPIC_API_KEY` - Anthropic API key for alternative LLMs
- `LLM_PROVIDER` - Which LLM provider to use (openai, anthropic)
- `TEMPLATES_PATH` - Path to document templates
- `OUTPUT_PATH` - Path for generated documents

#### BFF Service
- `JWT_SECRET` - JWT token secret for authentication
- `CORS_ORIGINS` - Allowed CORS origins
- `NEXT_ERP_URL` - Integration with ERP systems

#### RAG Scoring
- `ALPHA_VANTAGE_API_KEY` - Financial data API key
- `CRUNCHBASE_API_KEY` - Startup/company data API key
- `RED_THRESHOLD` - Score threshold for RED status
- `AMBER_THRESHOLD` - Score threshold for AMBER status

#### Market Ingestion
- `CRUNCHBASE_API_KEY` - Company data API key
- `LINKEDIN_API_KEY` - Professional network data API key
- `SEC_API_KEY` - Financial filing data API key
- `NEWS_API_KEY` - News aggregation API key

#### Push Notifications
- `FCM_SERVER_KEY` - Firebase Cloud Messaging key
- `APNS_KEY_ID` - Apple Push Notification Service key ID
- `APNS_TEAM_ID` - Apple Developer Team ID
- `APNS_BUNDLE_ID` - iOS App Bundle ID

### Customization

#### Templates
Custom document templates can be placed in the `data/templates` directory and referenced by name in API calls.

#### Scoring Algorithms
RAG scoring thresholds and algorithms can be customized in the configuration files for each service.

#### Notification Rules
Push notification triggers and delivery methods can be configured via the push notification service configuration.
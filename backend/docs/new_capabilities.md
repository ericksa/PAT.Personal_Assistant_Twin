# New Capabilities Documentation

This document outlines the new capabilities and services that have been added to the PAT (Personal Assistant Twin) project.

## Table of Contents
1. [APAT Service](#apat-service)
2. [BFF Service](#bff-service)
3. [PAT Core Database Schema](#pat-core-database-schema)
4. [MCP Tool Extensions](#mcp-tool-extensions)
5. [Enterprise Docker Compose](#enterprise-docker-compose)

## APAT Service (Automation Prompt & Analytics Toolkit)

The APAT service is a new microservice designed for automated document generation with AI assistance.

### Key Features
- Document generation for business plans, Statements of Work (SOW), and RFPs
- Template-driven approach with YAML configuration
- Background job processing system
- Integration with MCP for storage and retrieval
- RAG (Red-Amber-Green) status calculation for document sections

### API Endpoints
- `GET /health` - Health check endpoint
- `POST /jobs/generate` - Queue document generation jobs

### Environment Variables
- `INGEST_SERVICE_URL` - URL for the ingest service
- `MCP_SERVICE_URL` - URL for the MCP service
- Path configurations for templates, output, and logs

## BFF Service (Backend for Frontend GraphQL API)

The BFF service provides a unified GraphQL API gateway for frontend applications.

### Key Features
- GraphQL API for consolidated backend access
- Market opportunity management with RAG scoring
- Document management for business artifacts
- Real-time updates via WebSocket

### GraphQL Schema

#### Types
- `Opportunity` - Market opportunities with RAG scoring
- `Document` - Generated business documents
- `RAGMetrics` - Metrics and overview
- `BusinessPlan` - Complete business plans
- `MarketInsight` - Market insights and trends

#### Queries
- `opportunities(filter_rag, limit)` - Get market opportunities
- `opportunity(id)` - Get single opportunity
- `rag_metrics()` - Get scoring metrics
- `business_plans(limit)` - Get business plans
- `market_insights(limit)` - Get market insights
- `documents(document_type, limit)` - Get generated documents

#### Mutations
- `create_opportunity(input)` - Create new opportunity
- `generate_business_plan(request)` - Generate business plan
- `update_opportunity_rag(id, rag_status)` - Update RAG status

## PAT Core Database Schema

New database tables support core personal assistant functionality.

### New Tables

#### Users & Preferences
- `users` - User profiles and preferences
- `schedule_preferences` - Work scheduling preferences

#### Calendar Management
- `calendar_events` - Events with metadata
- `calendar_conflicts` - Scheduling conflicts

#### Email Processing
- `email_threads` - Conversation threads
- `emails` - Individual messages with classification

#### Task Management
- `tasks` - Task management with priority/status

#### AI Features
- `ai_suggestions` - AI-generated suggestions
- `business_entities` - Companies/organizations
- `business_documents` - Business documents (SOPs, RFQs, RFPs)
- `wearable_data` - Wearable device data (placeholder)

## MCP Tool Extensions

Extended tool registry with new PAT Core integration tools.

### New Tools

#### Calendar Tools
- `pat_calendar_list` - List calendar events
- `pat_calendar_create` - Create calendar event
- `pat_calendar_sync` - Sync with Apple Calendar

#### Task Tools
- `pat_task_list` - List tasks
- `pat_task_create` - Create task

#### Email Tool
- `pat_email_process` - Process/classify email

## Enterprise Docker Compose

Comprehensive service orchestration for enterprise deployment.

### Services
1. `apat-service` - Automation Prompt & Analytics Toolkit
2. `bff-service` - Backend for Frontend GraphQL API
3. `rag-scoring` - RAG Scoring Engine
4. `market-ingest` - Market Data Ingestion Service
5. `doc-generation` - Document Generation Service
6. `push-notifications` - Push Notification Service

Each service configured with environment variables, dependencies, volumes, and health checks.
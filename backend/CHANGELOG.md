# PAT Backend Changelog

All notable changes to the backend services will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- PAT Core service - Personal Assistant Twin API (port 8010)
- Database schema for Calendar, Email, Task, AI, Business entities
- Llama 3.2 3B integration via Ollama
- AppleScript integration framework for macOS apps
- Calendar events sync from PAT-cal calendar
- Task sync from Apple Reminders
- Email classification, summarization, reply drafting
- AI-powered scheduling and conflict detection
- Backend TODO documentation (`backend/BACKEND_TODO.md`)
- Changelog documentation (this file)
- Frontend API reference documentation (`backend/FRONTEND_API_REFERENCE.md`)
- LaunchAgent reference guide (`docs/LAUNCHAGENT_GUIDE.md`)

### Changed
- Updated asyncpg dependency from 0.29.0 to ~=0.30.0
- Renamed default calendar from "Adam" to "PAT-cal"

### Fixed
- Fixed calendar repository import references

### Removed
- None yet

### Security
- Running PAT Core locally only (not in Docker) for security
- No cloud LLM API calls - all local Ollama

---

## [0.0.1] - 2026-02-11

### Added
- Initial PAT backend infrastructure
- Database tables: users, calendar_events, calendar_conflicts, tasks, email_threads (subset)
- Core Llama 3.2 3B integration
- Basic API endpoints for calendar and email (placeholder)
- AppleScript base manager for macOS integration

### Technical
- Created base repository pattern (`base.py`)
- Created SQL helper for asyncpg operations
- Created Pydantic models for data validation
- Created service layer for business logic
- Created API routes with FastAPI
- Implemented logging configuration with rotation

### Testing
- Tested AppleScript integration - successfully lists calendars
- Tested Ollama connection - successful
- Tested PAT Core API startup - successful
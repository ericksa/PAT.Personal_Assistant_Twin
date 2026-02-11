# PAT Backend TODO

## Priority Legend
- 🔴 HIGH - Critical for current iteration
- 🟡 MEDIUM - Important, can be deferred slightly
- 🟢 LOW - Nice to have, future work
- 📌 FUTURE - Future project, no timeline

---

## 🔴 HIGH PRIORITY

### Database Migration Fix
- [ ] Fix `emails` table schema error in `scripts/migrations/002_add_pat_core_tables.sql`
- [ ] Re-run migration to create `emails` table
- [ ] Verify all 11 PAT Core tables created successfully

### Sync Workers Implementation
- [ ] Create `scripts/pat_sync_worker.py` with calendar/email/reminders workers
- [ ] Implement AppleScript integration (graceful error handling)
- [ ] Add logging to stdout + log file
- [ ] Configure error notifications (log + 1-time email until fixed)

### API Testing
- [ ] Create `scripts/test_pat_api.sh` automated test suite
- [ ] Test all 30+ PAT Core endpoints
- [ ] Verify database persistence
- [ ] Test LLM integration

### Sync Worker Startup Script
- [ ] Create `scripts/start_sync_workers.sh` to start all workers
- [ ] Add logging configuration
- [ ] Test permission prompts (macOS)

---

## 🟡 MEDIUM PRIORITY

### PAT Core Service Stability
- [ ] Update `README.md` with PAT Core service startup instructions
- [ ] Test PAT Core server start on boot
- [ ] Monitor performance and memory usage

### Error Handling & Monitoring
- [ ] Add comprehensive error handling in all endpoints
- [ ] Implement retry logic for database operations
- [ ] Add monitoring/metrics for PAT Core service

### Documentation
- [ ] Create `backend/FRONTEND_API_REFERENCE.md` - API spec for future frontend communication
- [ ] Update `README.md` with complete PAT system overview

---

## 🟢 LOW PRIORITY

### System Integration
- [ ] Document macOS permission requirements for AppleScript
- [ ] Create startup script for PAT Core service

### CI/CD
- [ ] Set up automated testing for PAT Core
- [ ] Add linting/type checking to CI pipeline

---

## 📌 FUTURE PROJECTS (No Timeline)

### macOS LaunchAgent Setup
**Status:** Reference guide created, implementation deferred

**Tasks (for future implementation):**
- [ ] Create LaunchAgent plist files for calendar/email/reminders workers
- [ ] Test auto-startup on user login
- [ ] Configure log file paths
- [ ] Document troubleshooting steps

**Reference:** See `docs/LAUNCHAGENT_GUIDE.md` for implementation guide.

### WebSocket Support for Real-time Updates
- [ ] Implement WebSocket for PAT Core API
- [ ] Add real-time push notifications for calendar events
- [ ] Add real-time email notifications

---

## Completed (2026-02-11)

### Database & Infrastructure
- [x] Create PAT Core database migration script (`scripts/migrations/002_add_pat_core_tables.sql`)
- [x] Apply database migration (10/11 tables created successfully)
- [x] Create user table with single-user setup
- [x] Create calendar events table with AI fields
- [x] Create tasks table with Apple Reminders integration
- [x] Create business entities and documents tables

### Core Services
- [x] Create calendar service with conflict detection
- [x] Create service layer abstraction
- [x] Implement AppleScript integration framework
- [x] Test AppleScript calendar access (successfully lists calendars)

### Dependencies & Configuration
- [x] Update asyncpg dependency from 0.29.0 to ~=0.30.0
- [x] Rename default calendar from "Adam" to "PAT-cal"
- [x] Create logging configuration with structured output
- [x] Set up PAT Core API with 30+ endpoints

### API Implementation
- [x] Calendar CRUD endpoints
- [x] Email AI features (classify, summarize, draft reply, extract tasks/meetings)
- [x] Task management endpoints (CRUD, prioritization)
- [x] Chat/LLM endpoints (Llama 3.2 3B integration)
- [x] Health and system info endpoints

### Testing & Verification
- [x] Test PAT Core API startup (successful)
- [x] Test LLM connection to Ollama (successful)
- [x] Test AppleScript calendar integration (successful)
- [x] Verify PostgreSQL connectivity

---

## Known Issues

### Database Migration
- **Issue:** `emails` table failed to create due to schema error in migration script
- **Status:** Migration script needs fix
- **Impact:** Email CRUD operations will fail until table created

### Sync Workers
- **Issue:** Workers not yet implemented
- **Status:** Implementation in progress
- **Impact:** Manual sync required until workers deployed

---

## Dependencies

### External Services
- **Ollama:** `http://localhost:11434` - Llama 3.2 3B model service
- **PostgreSQL:** `localhost:5432` - Database for PAT Core
- **Apple Calendar:** "PAT-cal" - Default calendar for sync
- **Apple Mail:** INBOX - Email source
- **Apple Reminders:** Task source

### Python Packages (key)
- `asyncpg~=0.30.0` - PostgreSQL async driver
- `fastapi~=0.128.0` - API framework
- `pydantic~=2.11.7` - Data validation
- `httpx~=0.28.1` - Async HTTP client
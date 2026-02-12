# PAT Backend TODO

## Priority Legend
- 🔴 HIGH - Critical for current iteration
- 🟡 MEDIUM - Important, can be deferred slightly
- 🟢 LOW - Nice to have, future work
- 📌 FUTURE - Future project, no timeline

---

## 🔴 HIGH PRIORITY

### Database Migration Fix
- [x] Fix `emails` table schema error in `scripts/migrations/002_add_pat_core_tables.sql`
- [x] Re-run migration to create `emails` table
- [x] Verify all 11 PAT Core tables created successfully

### Sync Workers Implementation
- [x] Create `scripts/pat_sync_worker.py` with calendar/email/reminders workers
- [x] Implement AppleScript integration (graceful error handling)
- [x] Add logging to stdout + log file
- [ ] Configure error notifications (log + 1-time email until fixed)

### API Testing
- [x] Create `scripts/test_pat_api.sh` automated test suite
- [x] Test all 30+ PAT Core endpoints
- [x] Verify database persistence
- [x] Test LLM integration

### Sync Worker Startup Script
- [x] Create `scripts/start_sync_workers.sh` to start all workers
- [x] Add logging configuration
- [x] Test permission prompts (macOS)

---

## 🟡 MEDIUM PRIORITY

### PAT Core Service Stability
- [x] Update `README.md` with PAT Core service startup instructions
- [ ] Test PAT Core server start on boot
- [ ] Monitor performance and memory usage

### Error Handling & Monitoring
- [ ] Add comprehensive error handling in all endpoints
- [ ] Implement retry logic for database operations
- [ ] Add monitoring/metrics for PAT Core service

### Documentation
- [x] Create `backend/FRONTEND_API_REFERENCE.md` - API spec for future frontend communication
- [x] Update `README.md` with complete PAT system overview

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

## Completed (2026-02-12)

### Database & Infrastructure
- [x] Fix `emails` table schema error in migration script
- [x] Re-run migration and verify all 11 PAT Core tables
- [x] Rename legacy `tasks` table to avoid conflict with PAT Core

### Core Services & Repositories
- [x] Restore `BaseRepository` (asyncpg version)
- [x] Implement `EmailRepository` and `TaskRepository`
- [x] Implement `EmailService` and `TaskService`
- [x] Update `AppleScriptManager` with generic execution class

### API Implementation
- [x] Restore 30+ endpoints in `src/api/pat_routes.py` (CRUD + AI)
- [x] Merge WebSocket endpoints with REST endpoints

### Sync & Automation
- [x] Create `scripts/pat_sync_worker.py` for automated background sync
- [x] Create `scripts/start_sync_workers.sh` for easy startup
- [x] Create `scripts/test_pat_api.sh` for automated testing

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
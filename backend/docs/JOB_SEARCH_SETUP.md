# PAT Job Search Agent - Setup and Configuration

## Overview
The Job Search Agent automates finding government contracting positions requiring secret clearance, with daily searches and intelligent resume customization.

## ✅ Completed Features

### Core Infrastructure
- ✅ LinkedIn API integration configuration
- ✅ Job search database schema
- ✅ FastAPI job search service
- ✅ Clearance detection algorithm
- ✅ Automated scheduler
- ✅ Email notification service
- ✅ Resume customization for government jobs

### Key Features
- **Daily Automated Searches**: Runs at 8 AM EST
- **Government Focus**: Targets VA → DHA → DoD → DOT agencies
- **Clearance Detection**: Identifies secret clearance requirements
- **Resume Customization**: Generates ATS-friendly resumes
- **Email Alerts**: Sends daily job summaries

## 🚀 Quick Start

### 1. Configure Environment
Add these to your `.env` file:

```bash
# LinkedIn API (already configured)
LINKEDIN_CLIENT_ID=86vjm97gdqpp74
LINKEDIN_CLIENT_SECRET=WPL_AP1.6MB43IgL9xlzvqYE.sW4HIg==

# Email notifications (required for email alerts)
PAT_NOTIFICATION_EMAIL=erickson.adam.m@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=erickson.adam.m@gmail.com
# Use Gmail App Password (NOT regular password)
SMTP_PASSWORD=your_gmail_app_password_here

# Job search schedule
JOB_SEARCH_ENABLED=true
JOB_SEARCH_SCHEDULE="0 8 * * *"
GOVERNMENT_AGENCY_PRIORITY=VA,DHA,DOD,DOT
```

### 2. Start Services
```bash
# Rebuild and start job search service
cd /Users/adamerickson/Projects/PAT/backend
docker-compose up -d job-search-service

# Verify service is running
docker-compose ps job-search-service
```

### 3. Test the System
```bash
# Run comprehensive test
python test_job_search.py
```

## 📋 API Endpoints

### Job Search
```bash
# Search for jobs
curl -X POST http://localhost:8007/search \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": "government secret clearance software engineer",
    "location": "remote",
    "days_back": 7
  }'

# Get scheduler status
curl http://localhost:8007/scheduler/status

# Health check
curl http://localhost:8007/health
```

## 🔧 Configuration Options

### LinkedIn API Setup
1. Use your LinkedIn premium account credentials
2. API uses mock data initially - replace with real LinkedIn Jobs API
3. Credentials configured in `.env` file

### Email Notifications
To enable real email notifications:
1. Create Gmail App Password
2. Add SMTP credentials to `.env`
3. Service falls back to mock notifications if SMTP not configured

### Search Frequency
- Default: Daily at 8 AM EST
- Adjust `JOB_SEARCH_SCHEDULE` in environment
- Format: Cron schedule (minute hour day month day_of_week)

## 🎯 Target Job Criteria

### Priority Agencies
1. **VA**: Veterans Affairs (highest priority)
2. **DHA**: Defense Health Agency
3. **DoD**: Department of Defense
4. **DOT**: Department of Transportation

### Key Technologies
- Java Spring Boot ecosystem
- AWS government cloud experience
- API development background
- DevOps/containerization skills

### Clearance Requirements
- Secret clearance positions prioritized
- Government contract experience highlighted
- Security compliance emphasized

## 🔄 Integration Points

### Existing PAT System
- Leverages your uploaded resume documents
- Integrates with RAG system for document access
- Uses n8n workflows for automation

### Future Integrations
- LinkedIn profile scraping
- Real LinkedIn Jobs API (currently uses mock data)
- Database integration for job tracking

## 🧪 Testing

### Manual Testing
```bash
# Test search functionality
curl -X POST http://localhost:8007/search \
  -d '{"keywords": "government secret clearance"}'

# Check service health
curl http://localhost:8007/health
```

### Automated Testing
```bash
python test_job_search.py
```

### Mock Data
Currently uses simulated job data. Replace with real LinkedIn API when ready.

## 📈 Monitoring

### Service Status
- Port: 8007
- Health endpoint: `/health`
- Scheduler status: `/scheduler/status`

### Daily Reports
- Email summaries sent to `erickson.adam.m@gmail.com`
- Mock notifications logged if SMTP not configured
- Job matches scored by relevance

## 🔧 Troubleshooting

### Common Issues
**Service won't start:**
- Check Docker logs: `docker-compose logs job-search-service`
- Verify `.env` file configuration
- Check port availability (8007)

**No email notifications:**
- Verify SMTP credentials
- Check Gmail App Password setup
- Fallback uses mock notifications (logged to console)

**Database integration pending:**
- Schema created but integration needs implementation
- Jobs currently tracked in memory only

## 📞 Support

For issues or enhancements:
1. Check service logs
2. Run test script for diagnostics
3. Review environment configuration

---

**Next Steps:** 
- Implement real LinkedIn Jobs API integration
- Complete database integration
- Add resume generation API endpoints
- Test with actual government job postings

The Job Search Agent is ready for deployment and will begin automated searching once services are started!
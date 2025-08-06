# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL WARNING ⚠️

**NEVER START THE WEBSITE SERVER!** 
- Do NOT run `python start_website.py`
- Do NOT run `flask run` 
- Do NOT run any commands that start the web server
- Once the server is started, it cannot be easily stopped and will block the terminal
- The server is for production use only, not for development testing

## Specialized Claude Agents

This project includes specialized agents in `.claude/agents/` for different tasks:

### Available Agents:
- **code-reviewer** - Use immediately after writing or modifying code for quality, security, and maintainability review
- **debugger** - Use proactively when encountering errors, test failures, or unexpected behavior  
- **frontend-developer** - Use for React components, responsive layouts, and frontend performance optimization
- **deployment-engineer** - Use for CI/CD pipelines, deployment issues, infrastructure configuration, and production readiness
- **general-purpose** - Use for complex multi-step tasks requiring research and file operations

### When to Use Agents:
- After significant code changes → `code-reviewer`
- When tests fail or errors occur → `debugger`
- For UI/frontend work → `frontend-developer`
- For deployment/infrastructure issues → `deployment-engineer`
- For complex multi-step tasks → `general-purpose`

Example usage:
```bash
# After modifying database code
claude --agent code-reviewer "Review the recent database changes"

# When debugging appointment conflicts
claude --agent debugger "Appointment creation is failing with status conflicts"

# For frontend calendar improvements
claude --agent frontend-developer "Optimize calendar page performance and add accessibility"

# For deployment issues and CI/CD setup
claude --agent deployment-engineer "Fix Railway deployment failures and set up proper CI/CD pipeline"
```

## Project Overview

This is an AI-powered appointment tracking system for Air Force customer service section. The system processes emails and manages appointments/contacts for military personnel using a SQLite database for data persistence.

## Development Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

Set up environment variables:
```bash
# Create .env file with:
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Run the main application:
```bash
# Run continuously (checks every 5 minutes)
python main.py

# Run once and exit
python main.py --once

# Run with custom interval (in seconds)
python main.py --interval 60

# Run with verbose output
python main.py --verbose

# Show current status
python main.py status

# View appointment calendar
python main.py appointments
python main.py calendar
```

## System Architecture & Data Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────┐
│   React App     │───▶│  Vite Dev Server │───▶│ Flask Backend   │───▶│ SQLite DB    │
│  (Frontend)     │    │   (Port 5173)    │    │ (Port 5000)     │    │vera_system.db│
│                 │    │                  │    │                 │    │              │
│ SectionLeadsPage│    │ Proxy: /api/*    │    │start_website.py │    │ 14 Personnel │
│ CalendarPage    │    │ → localhost:5000 │    │                 │    │ Records      │
│ HomePage        │    │                  │    │ DatabaseManager │    │              │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └──────────────┘
```

### **Critical System Components:**

**Frontend (React + TypeScript)**
- `frontend/src/pages/SectionLeadsPage.tsx` - Personnel status dashboard
- `frontend/src/pages/CalendarPage.tsx` - Appointment calendar view  
- `frontend/src/services/api.ts` - API service layer (axios)
- `frontend/vite.config.ts` - **PROXY CONFIG**: `/api/*` → `http://localhost:5000`

**Backend (Flask + SQLite)**
- `start_website.py` - **PRIMARY FLASK APP** (Port 5000) - **THIS IS WHAT FRONTEND CALLS**
- `database_manager.py` - SQLite database operations and transactions
- `vera_system.db` - SQLite database with personnel, appointments, general_events tables

**Legacy/Duplicate Files (NOT USED BY FRONTEND)**
- `website/app.py` - Duplicate Flask app (different port)
- `calendar_manager.py` - Old JSON-based system
- `gpt_parser.py` - Email processing (not used for web interface)

### **Data Flow Architecture:**
1. **React Frontend** (localhost:5173) makes API calls to `/api/personnel-status`
2. **Vite Proxy** forwards `/api/*` requests to `localhost:5000`
3. **Flask App** (`start_website.py`) receives request at `/api/personnel-status`
4. **DatabaseManager** executes SQLite queries on `vera_system.db`
5. **Response** flows back through Flask → Vite → React

### **Key API Endpoints:**
- `GET /api/personnel-status` - Personnel assignments and status counts
- `GET /api/appointments` - Calendar appointments and events
- `GET /api/personnel` - All personnel records
- `POST /api/ai-agent/message` - Vera chat interface

## Database System

The system now uses SQLite database (`vera_system.db`) instead of JSON files:

### Tables:
- `personnel` - Personnel records with status tracking
- `appointments` - Appointment scheduling with conflict detection  
- `general_events` - Section-wide events and activities

### Key Features:
- Automatic status management with transactions
- Conflict detection for appointments
- Foreign key constraints for data integrity
- Atomic operations for consistent updates

## Data Migration

The system can migrate from legacy JSON files to SQLite:
```python
from database_manager import DatabaseManager
db = DatabaseManager()
db.migrate_from_json()  # Migrates appointments.json, personnel_assignments.json, etc.
```

## Workflow

1. **Message Retrieval**: `EmailParser` connects to Gmail API and searches for Google Voice forwarded text messages
2. **Message Processing**: `GPTParser` analyzes each message using Anthropic Claude API to extract:
   - Appointment requests
   - Service type (ID cards, records, travel, etc.)
   - Urgency level
   - Contact information
3. **Data Storage**: Processed messages are stored in SQLite database with automatic status updates
4. **Continuous Monitoring**: Main loop checks for new messages at configurable intervals
5. **Web Interface**: React frontend communicates with Flask backend for calendar and personnel management

## Web Interface (Production Only)

- **Frontend**: React application in `frontend/` directory
- **Backend**: Flask API in `website/app.py`
- **Database Integration**: All API endpoints pull from SQLite database
- **AI Chat**: Vera agent provides intelligent responses via `/api/ai-agent/message`

**Important**: Web server is for production deployment only. Do not start during development.

## Legacy JSON Files

These JSON files are now deprecated and can be safely removed after database migration:
- `appointments.json` - Migrated to `appointments` table
- `personnel_assignments.json` - Migrated to `personnel` table  
- `contacts.json` - Contact data integrated into `personnel` table
- `processed_messages.json` - Message tracking (still used by email parser)

Keep these files:
- `processed_messages.json` - Still used for email message tracking
- `personnel.json` - May contain additional contact data
- `railway.json` - Deployment configuration
- `package.json` - Frontend dependencies

## Key Dependencies

- Google API client libraries for Gmail integration
- Anthropic for Claude AI functionality
- SQLite3 for database operations
- Flask for web API backend
- React for frontend interface
- Pandas for data manipulation

## Setup Requirements

1. **Google API Setup**:
   - Create a Google Cloud project and enable Gmail API
   - Download `credentials.json` from Google Cloud Console
   - First run will open browser for OAuth authentication

2. **Anthropic Claude API Setup**:
   - Get Anthropic API key from console.anthropic.com
   - Set `ANTHROPIC_API_KEY` environment variable or add to `.env` file

3. **Google Voice Setup**:
   - Configure Google Voice to forward text messages to your Gmail
   - Go to Google Voice settings > Messages > Forward messages to email

4. **Database Setup**:
   - Database is automatically created on first run
   - Run migration to import existing JSON data: `python -c "from database_manager import DatabaseManager; DatabaseManager().migrate_from_json()"`

## Testing and Verification

**All test files should be placed in the `tests/` directory going forward.**

Test database operations:
```bash
python database_manager.py     # Run built-in tests
python tests/test_database.py  # Test API response structure  
python populate_database.py    # Repopulate database if needed
```

Test specific functionality:
```bash
python tests/test_simon_calendar.py    # Test calendar API endpoints
python tests/check_simon_appointment.py # Debug appointment data
```

View current data:
```bash
python -c "from database_manager import DatabaseManager; db = DatabaseManager(); print(db.get_personnel_status_summary())"
```

**Test Organization:**
- `tests/test_*.py` - Unit and integration tests
- `tests/check_*.py` - Debug and diagnostic scripts
- Root directory - Only production code and utilities

## Troubleshooting Section Leads Page

If the section leads page shows zeros:

### **Step 1: Verify Backend is Working**
```bash
# Test API endpoint directly
curl http://localhost:5000/api/personnel-status

# Should return 14 personnel with proper counts
```

### **Step 2: Check Frontend Development Server**
```bash
cd frontend
npm run dev  # Should start on port 5173
```

### **Step 3: Debug Data Flow**
1. **Browser Console**: Check for JavaScript errors
2. **Network Tab**: Verify API calls reach `/api/personnel-status`
3. **Response Data**: Ensure API returns correct structure

### **Step 4: Common Issues**
- **Multiple Flask Instances**: Kill all Python processes, restart only `start_website.py`
- **Port Conflicts**: Ensure Flask runs on port 5000, React on 5173
- **Database Empty**: Run `python populate_database.py` to repopulate
- **Proxy Issues**: Verify `vite.config.ts` proxy points to `localhost:5000`

### **Expected API Response Structure**
```json
{
  "success": true,
  "stats": {
    "total_personnel": 14,
    "military_count": 12,
    "civilian_count": 2,
    "working_count": 13,
    "out_of_office_count": 1
  },
  "assignments": {
    "floor": {"count": 1, "personnel": [...]},
    "admin_room": {"count": 2, "personnel": [...]},
    "terminal": {"count": 7, "personnel": [...]},
    "float": {"count": 3, "personnel": [...]}
  },
  "unavailable_personnel": [...]
}
```

## Progress Tracking - Vera Database Integration

```
MIGRATION TASKS:
├── [✅] Dependency analysis completed
├── [✅] Impact matrix created  
├── [✅] DatabaseManager method mapping completed
├── [✅] Breaking changes identified
├── [✅] Risk mitigation strategies documented
├── [✅] Migration plan approved by user
├── [ ] Tests updated for database fixtures
├── [✅] Migration executed
├── [✅] Integration testing completed
└── [ ] Rollback plan validated
```

### Discovered Dependencies
- `start_website.py:252`: reads from `personnel_assignments.json` directly for API endpoint
- `tests/test_vera_appointments.py`: creates JSON fixtures for testing Vera functionality
- `gpt_parser.py`: shares same JSON files with Vera, coordination needed
- `calendar_manager.py`: legacy system using same JSON structure as Vera
- `processed_messages.json`: still used by email parser (keep unchanged)

### Breaking Changes Identified
1. `vera_agent.py` personnel lookup: List iteration → Database query (requires personnel_id)
2. Status updates: In-memory dict modification → Database transaction
3. Error handling: JSON exceptions → SQLite exceptions  
4. Data loading: Full file load → On-demand queries
5. Transaction scope: File write atomicity → Explicit DB transactions

## Document Version History
- v1.0: Initial project setup and architecture documentation
- v1.1: Added comprehensive dependency analysis for JSON operations
- v1.2: Detailed Vera database integration requirements
- v1.3: Added progress tracking and lessons learned sections

## Lessons Learned / Integration Gotchas

**Discovered During Analysis:**
- Multiple systems write to same JSON files simultaneously
- Tests expect specific JSON file structure and locations
- start_website.py has hybrid approach (some DB, some JSON)
- AppointmentManager already database-integrated but Vera bypasses it
- Error handling inconsistent between JSON and database operations
- No file locking mechanism for JSON writes (potential corruption)

**Gotchas to Watch For:**
- Personnel lookup requires exact name matching vs fuzzy JSON search
- Database queries are case-sensitive vs JSON lowercase comparisons
- Transaction rollback needed for multi-step operations  
- Schema constraints may reject data that JSON files accepted
- Performance implications: Memory vs disk I/O trade-offs

## ⚠️ CRITICAL CODE DEPENDENCY ANALYSIS ⚠️

**Before modifying ANY code, understand these dependencies to prevent breaking changes:**

### **JSON File Dependencies (CRITICAL BREAKING POINTS)**

**Files Reading/Writing Same JSON Files (HIGHEST RISK):**
```
appointments.json:
├── vera_agent.py:32,139 (WRITES via add_appointment)
├── gpt_parser.py:33 (READ/WRITE via _load_json_file)
├── calendar_manager.py:10 (READ/WRITE)
├── database_manager.py:149 (READ for migration)
└── tests/test_vera_appointments.py:77 (READ/WRITE fixtures)

personnel_assignments.json:
├── vera_agent.py:35,93 (READ/WRITE via update_personnel_status) 
├── gpt_parser.py:36 (READ/WRITE)
├── calendar_manager.py:11 (READ/WRITE)
├── start_website.py:252 (READ ONLY - for API endpoint)
├── database_manager.py:126 (READ for migration)
└── tests/test_vera_appointments.py:72 (READ/WRITE fixtures)

contacts.json:
├── vera_agent.py:33 (READ via _load_json_file)
├── gpt_parser.py:34 (READ/WRITE)
└── Database already migrated this data

personnel.json:
├── vera_agent.py:34 (READ via _load_json_file)
├── gpt_parser.py:35 (READ/WRITE)
└── May contain additional contact data not in database
```

### **Direct Import Dependencies**
```
VeraAgent imported by:
├── start_website.py:15,319 (Web API /api/ai-agent/message)
├── website/app.py:15 (Duplicate Flask app - legacy)
└── tests/test_vera_appointments.py:18 (Unit tests)

Files using _load_json_file/_save_json_file:
├── vera_agent.py:46,54 (MAIN TARGET FOR MODIFICATION)
├── gpt_parser.py:49,56 (WILL BREAK if JSON structure changes)
├── calendar_manager.py:23,30 (WILL BREAK if JSON structure changes)
└── Tests expect JSON file operations
```

### **DatabaseManager to JSON Operation Mapping**
```
VERA JSON → DATABASE EQUIVALENT:
├── vera_agent._load_json_file(personnel_assignments.json) → db.get_all_personnel()
├── vera_agent.update_personnel_status() → db.update_personnel_status()
├── vera_agent.add_appointment() → db.create_appointment() (via AppointmentManager)
├── vera_agent.get_personnel_roster() → db.get_all_personnel()
└── vera_agent._save_json_file() → Automatic DB transactions

JSON DATA FORMAT → DATABASE SCHEMA:
├── JSON: {name, rank, status, last_updated} → DB: personnel table
├── JSON: {id, personnel_name, appointment_date} → DB: appointments table
└── JSON nested structures → DB normalized relations
```

### **CRITICAL DATA FORMAT MISMATCHES**
```
⚠️ BREAKING CHANGES REQUIRED:

1. Personnel Status Updates:
   JSON: person_found['status'] = new_status (in-memory dict)
   DB: db.update_personnel_status(personnel_id, new_status) (needs personnel_id)

2. Personnel Lookup:
   JSON: linear search through self.personnel_assignments list
   DB: db.find_personnel(name) returns single record or None

3. Data Loading:
   JSON: Load entire file into memory once
   DB: Query on demand (performance implications)

4. Transaction Boundaries:
   JSON: File write is atomic
   DB: Explicit transaction management required

5. Error Handling:
   JSON: FileNotFoundError, json.JSONDecodeError
   DB: sqlite3.Error, transaction rollback needed
```

### **CHANGE IMPACT MATRIX**

**If vera_agent.py changes to database:**
```
IMMEDIATE BREAKS:
├── Tests expecting JSON fixtures (test_vera_appointments.py)
├── Any external systems reading JSON files directly
└── Backup/restore processes expecting JSON format

POTENTIAL BREAKS:
├── start_website.py:252 (still reads personnel_assignments.json)
├── Performance assumptions (full file load vs DB queries)
├── Error handling expecting JSON-specific exceptions
└── Race conditions between file-based and DB-based operations

SYSTEMS THAT CONTINUE WORKING:
├── Web API endpoints (already use DatabaseManager)
├── AppointmentManager (already database-integrated)
└── Frontend React app (uses API, not direct file access)
```

### **INTEGRATION RISKS & MITIGATION**
```
HIGHEST RISK AREAS:
1. Personnel Status Updates - Two systems could conflict
2. Appointment Creation - JSON vs DB conflict detection
3. Data Synchronization - Stale JSON data vs fresh DB data
4. Test Suite - Expects JSON file operations

REQUIRED BEFORE MODIFYING VERA:
├── Backup vera_agent.py (✅ vera_agent_backup.py exists)
├── Ensure database has current data (run populate_database.py)
├── Update tests to use database fixtures
├── Stop any processes writing to JSON files
└── Plan rollback strategy if integration fails

EXTERNAL SYSTEMS CHECK:
├── No cron jobs found reading JSON files
├── No deployment scripts depend on JSON structure  
├── Railway.json deployment config doesn't reference JSON files
└── Frontend only uses API endpoints (safe)
```

### **PERFORMANCE & BEHAVIOR CHANGES**
```
JSON → DATABASE CHANGES:
├── Memory: Full file load → On-demand queries
├── Concurrency: File locking → DB transactions  
├── Persistence: Manual save calls → Automatic commits
├── Error Recovery: File restore → Transaction rollback
└── Data Validation: Runtime checks → Schema constraints
```

## Important Notes

- System processes Google Voice messages forwarded to Gmail (not direct Google Voice API)
- Data is now stored in SQLite database for reliability and performance
- Security consideration: `credentials.json` and API keys contain sensitive information
- The system avoids processing duplicate messages by tracking message IDs
- Message extraction filters out Google Voice email footer text
- **NEVER START THE WEB SERVER DURING DEVELOPMENT** - Use only for production deployment
- Database operations are atomic and handle concurrent access safely
- Personnel status is automatically updated based on appointment scheduling
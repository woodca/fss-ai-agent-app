# Test Suite

This directory contains all test files for the Air Force CS Section appointment tracking system.

## Test Categories

### Database Tests
- `test_simon_stability.py` - Tests SQLite database stability for Simon's status persistence

### Calendar System Tests
- `test_calendar_system.py` - Calendar functionality tests
- `test_date_parsing.py` - Date parsing and validation tests

### Appointment System Tests
- `test_appointment_commands.py` - Appointment command processing
- `test_vera_appointments.py` - Vera AI appointment handling

### Personnel Status Tests
- `test_status_commands.py` - Personnel status update commands
- `test_manning.py` - Personnel manning and assignment tests
- `test_ssgtwoodley.py` - Specific personnel status tests
- `test_smith_leave.py` - Leave processing tests

### Message Processing Tests
- `test_parsing.py` - General message parsing
- `test_footer_filtering.py` - Google Voice footer filtering
- `test_real_message.py` - Real message processing tests
- `test_latest_message.py` - Latest message handling

### API Tests
- `test_web_api.py` - Web API endpoint tests
- `test_website_api.py` - Website API integration tests

## Running Tests

To run individual tests from the project root directory:
```bash
python tests/test_simon_stability.py
```

Or run from the tests directory with:
```bash
cd tests
python test_simon_stability.py
```

To run all tests (if you have a test runner):
```bash
python -m pytest tests/
```

## Important Notes

- `test_simon_stability.py` is the critical test that validates the SQLite database fix for the persistent status reversion issue
- Tests may require the main application database and configuration files to be present
- Some tests may interact with actual data files, so run with caution in production environments
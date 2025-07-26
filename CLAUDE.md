# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered appointment tracking system for Air Force customer service section. The system appears to be designed to process emails and manage appointments/contacts for military personnel.

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

Run the dashboard:
```bash
streamlit run dashboard/dashboard.py
```

Run the web interface:
```bash
python start_website.py
```
Then visit: http://localhost:5000

## Architecture

The codebase follows a modular Python structure:

- `main.py` - Main application orchestrator with CLI interface
- `email_parser.py` - Gmail API integration to retrieve Google Voice forwarded messages  
- `gpt_parser.py` - Anthropic Claude integration for message analysis and appointment extraction
- `dashboard/dashboard.py` - Streamlit dashboard interface (not yet implemented)
- `templates/gpt_prompt.txt` - GPT prompt template for Air Force customer service context

## Workflow

1. **Message Retrieval**: `EmailParser` connects to Gmail API and searches for Google Voice forwarded text messages
2. **Message Processing**: `GPTParser` analyzes each message using Anthropic Claude API to extract:
   - Appointment requests
   - Service type (ID cards, records, travel, etc.)
   - Urgency level
   - Contact information
3. **Data Storage**: Processed messages are stored in JSON files:
   - `appointments.json` - Appointment requests
   - `contacts.json` - Contact history
   - `processed_messages.json` - Tracking processed message IDs
4. **Continuous Monitoring**: Main loop checks for new messages at configurable intervals

## Data Files

The system uses JSON files for data persistence:
- `appointments.json` - Stores appointment data
- `contacts.json` - Manages contact information
- `processed_messages.json` - Tracks processed email messages
- `credentials.json` - Contains API credentials (ensure this stays in .gitignore)

## Key Dependencies

- Google API client libraries for Gmail integration
- Anthropic for Claude AI functionality
- Streamlit for web dashboard
- Pandas for data manipulation
- Plotly for data visualization

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

## Important Notes

- System processes Google Voice messages forwarded to Gmail (not direct Google Voice API)
- Data is stored locally in JSON files for simplicity
- Security consideration: `credentials.json` and API keys contain sensitive information
- The system avoids processing duplicate messages by tracking message IDs
- Message extraction filters out Google Voice email footer text to ensure only actual text message content is processed
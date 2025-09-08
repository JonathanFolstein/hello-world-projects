# Gmail Old Email Cleaner - Hello World Project

## Overview
This project demonstrates how to build a Python application that connects to Gmail API and deletes old emails based on specified criteria.

## Language/Framework Used
- **Python 3.13** - Main programming language
- **Gmail API** - For accessing and managing Gmail emails
- **Google Auth Libraries** - For OAuth2 authentication

## What This Program Demonstrates
- OAuth2 authentication with Google APIs
- Gmail API integration for email management
- Date-based email filtering
- Batch operations for email deletion
- Error handling for API operations
- Secure credential management

## How to Run the Program
(Setup instructions will be added as development progresses)

1. Install dependencies: `pip install -r requirements.txt`
2. Set up Google API credentials
3. Run the application: `python main.py`

## Project Structure
```
gmail-cleaner-hello/
├── README.md           # This file
├── PRD.md             # Product Requirements Document  
├── main.py            # Main application entry point
├── gmail_client.py    # Gmail API client wrapper
├── email_cleaner.py   # Core email deletion logic
├── config.py          # Configuration management
├── requirements.txt   # Python dependencies
├── .gitignore        # Git ignore rules
└── credentials/       # API credentials (gitignored)
    └── .gitkeep
```

## Example Output
(Will be updated once the application is functional)

## Security Notes
- All API credentials are stored locally and gitignored
- OAuth2 flow ensures secure authentication
- Email deletion operations include confirmation prompts
- Dry-run mode available for testing

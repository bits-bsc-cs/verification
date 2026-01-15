# Local Development

## Prerequisites
- Python 3.10+
- Discord Bot Token
- Resend API Key

## Setup
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Fill in the required keys in `.env`.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application
The system requires two separate processes.

1. Start the Discord Bot:
   ```bash
   python -m app.bot
   ```

2. Start the FastAPI Server:
   ```bash
   fastapi dev app/main.py
   ```

The bot handles Discord interactions and the IPC server (port 5001), while the FastAPI server handles web requests (port 8000).

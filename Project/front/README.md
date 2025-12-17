# SOLO Taxonomy Quiz Generator - Web Application

## Quick Start

**Terminal 1 - Backend:**
```powershell
cd backend
.\venv\Scripts\activate
python app.py
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm start
```

## Database
This project uses **SQLite** - no additional installation required! The database file (`quiz_database.db`) is created automatically when you first run the backend.

## API Key Management
- **Primary**: OpenRouter API (9 keys for daily limits)
- **Fallback**: GitHub Models (gpt-4o)
- **Alert**: Frontend displays warning when keys are exhausted for the day
- Check status: The app checks API status every 30 seconds and shows a notification if all keys are rate-limited
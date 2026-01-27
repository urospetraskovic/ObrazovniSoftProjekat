# Quick Start Guide

## Starting the Application

You need to run three terminals simultaneously:

**Terminal 1 - Ollama (AI Model):**
```powershell
.\ollama.ps1 serve
```

**Terminal 2 - Backend (Flask API):**
```powershell
cd backend
.\venv\Scripts\python.exe app.py
```

**Terminal 3 - Frontend (React App):**
```powershell
cd frontend
npm start
```

The application will be available at `http://localhost:3000`

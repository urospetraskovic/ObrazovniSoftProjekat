# SOLO Taxonomy Quiz Generator - Setup Guide

## Quick Start

This guide will help you set up and run the SOLO Taxonomy Quiz Generator web application.

## System Requirements

- **Node.js**: v14.0.0 or higher (https://nodejs.org/)
- **Python**: v3.8 or higher (https://python.org/)
- **npm**: v6.0.0 or higher (comes with Node.js)
- **pip**: Python package manager (comes with Python)

## Step-by-Step Setup

### Step 1: Backend Setup

1. Open PowerShell or Command Prompt
2. Navigate to the backend folder:
   ```bash
   cd backend
   ```

3. Create a Python virtual environment:
   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

5. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

6. Verify `.env` file exists with your API keys:
   ```bash
   cat .env  # or type .env on Windows
   ```

### Step 2: Frontend Setup

1. Open a new PowerShell/Command Prompt terminal
2. Navigate to the frontend folder:
   ```bash
   cd frontend
   ```

3. Install npm dependencies:
   ```bash
   npm install
   ```

## Running the Application

### Method 1: Using Start Script (Windows)

1. Double-click `start.bat` in the project root

This will automatically start both the backend and frontend in separate windows.

### Method 2: Using Start Script (macOS/Linux)

1. Open terminal in project root
2. Run:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

### Method 3: Manual Start (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # Activate virtual environment
python app.py
```

You should see:
```
 * Running on http://localhost:5000
 * Debug mode: on
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

The browser will open automatically at `http://localhost:3000`

## Verification

### Backend Health Check

Open browser and navigate to:
```
http://localhost:5000/api/health
```

You should see:
```json
{"status": "ok", "message": "API is running"}
```

### Frontend Load

Visit:
```
http://localhost:3000
```

You should see the SOLO Quiz Generator interface.

## Using the Application

1. **Upload a Text File**: Click the upload area and select a `.txt` file with educational content
2. **Generate Quiz**: Click "Generate Quiz" button
3. **View Results**: Browse through generated questions
4. **Download**: Click "Download Quiz (JSON)" to export

## Troubleshooting

### Issue: "npm: command not found"
**Solution**: Node.js/npm is not installed or not in PATH
- Install from https://nodejs.org/
- Restart terminal after installation

### Issue: "python: command not found"
**Solution**: Python is not installed or not in PATH
- Install from https://python.org/
- During installation, check "Add Python to PATH"

### Issue: "ModuleNotFoundError" when running backend
**Solution**: Dependencies not installed
```bash
cd backend
pip install -r requirements.txt
```

### Issue: "Cannot find module" when running frontend
**Solution**: npm dependencies not installed
```bash
cd frontend
npm install
```

### Issue: Port 5000 or 3000 already in use
**Solution 1**: Kill the process using the port
```bash
# Windows - Kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux - Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

**Solution 2**: Change the port in code
- Backend: Edit `app.py` line at the bottom
- Frontend: Create `.env` file in frontend folder with `REACT_APP_API_URL=http://localhost:YOUR_PORT`

### Issue: CORS Error when uploading file
**Solution**: Ensure backend is running on `http://localhost:5000`

### Issue: API returns "No API keys"
**Solution**: 
1. Verify `.env` file exists in backend folder
2. Check it has valid OpenRouter API keys
3. Restart the backend server

## Development Tips

### Real-time Code Updates
- **Backend**: Restart `app.py` when you make code changes
- **Frontend**: Changes are automatically reflected (hot reload)

### Testing the Backend API

Use curl or Postman to test:

```bash
# Health check
curl http://localhost:5000/api/health

# Generate quiz (requires file)
curl -X POST http://localhost:5000/api/generate-quiz \
  -F "file=@yourfile.txt"
```

### Debugging

**Backend Debug Mode**: Already enabled in `.env`
- Look for error messages in the terminal running `python app.py`

**Frontend Debug Mode**: Open DevTools in browser
- Press `F12` or right-click > Inspect
- Check Console tab for JavaScript errors

### Making Changes

**To modify the quiz generation logic**:
1. Edit `backend/quiz_generator.py`
2. Restart the backend server

**To modify the UI**:
1. Edit files in `frontend/src/`
2. Changes appear automatically in browser

**To change SOLO levels or questions**:
1. Edit `_build_prompt()` in `backend/quiz_generator.py`
2. Restart backend

## File Upload Limits

- **Maximum file size**: 10 MB
- **Supported format**: `.txt` (plain text)
- **Recommended size**: 500 - 5000 words per file

## API Documentation

### POST /api/generate-quiz

**Request:**
```
Content-Type: multipart/form-data
Body: file (text file)
```

**Response:**
```json
{
  "metadata": {
    "filename": "string",
    "generated_at": "ISO-8601 datetime",
    "total_chapters": number,
    "total_questions": number
  },
  "chapters": [
    {
      "chapter_number": number,
      "title": "string",
      "content_preview": "string",
      "questions": [
        {
          "solo_level": "prestructural|multistructural|relational|extended_abstract",
          "question_data": {
            "question": "string",
            "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
            "correct_answer": "A) ...",
            "explanation": "string"
          }
        }
      ]
    }
  ]
}
```

## Performance Notes

- Quiz generation time depends on file size and API response time
- Typically 30-120 seconds for a 2000-word document
- Progress indicators show generation status

## Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are installed
3. Check terminal output for error messages
4. Ensure backend and frontend are both running
5. Try restarting both services

## Next Steps

After setup, you can:
1. Upload educational content to generate quizzes
2. Customize question generation in `quiz_generator.py`
3. Modify the UI in `frontend/src/`
4. Add more SOLO taxonomy levels
5. Integrate with a database to save quizzes

---

Happy learning! 🎓

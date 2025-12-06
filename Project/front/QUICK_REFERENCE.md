# SOLO Quiz Generator - Quick Reference

## 🚀 Start Application

### Windows
```bash
cd D:\GitHub\ObrazovniSoftProjekat\Project\front
start.bat
```

### macOS/Linux
```bash
cd D:\GitHub\ObrazovniSoftProjekat\Project\front
./start.sh
```

### Manual
```bash
# Terminal 1: Backend
cd backend && python app.py

# Terminal 2: Frontend  
cd frontend && npm start
```

## 🌐 URLs
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:5000
- **API Health**: http://localhost:5000/api/health

## 📁 Project Structure
```
front/
├── frontend/          # React UI (npm start on port 3000)
├── backend/           # Flask API (python app.py on port 5000)
├── README.md          # Full documentation
├── SETUP_GUIDE.md     # Detailed setup steps
└── start.bat/sh       # Auto-start scripts
```

## 🔧 Setup (First Time Only)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

## 📤 Using the App

1. Open http://localhost:3000
2. Upload .txt file (max 10MB)
3. Click "Generate Quiz"
4. Wait 30-120 seconds
5. View/expand questions
6. Download as JSON

## 🎯 SOLO Levels

| Level | Description | Example |
|-------|-------------|---------|
| **1️⃣ Prestructural** | Basic recognition | "What is X?" |
| **3️⃣ Multistructural** | List multiple aspects | "What are the parts of X?" |
| **4️⃣ Relational** | Explain relationships | "How does X affect Y?" |
| **5️⃣ Extended Abstract** | Apply in new situations | "What if X happened?" |

## 🔑 API Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Generate quiz
curl -X POST http://localhost:5000/api/generate-quiz \
  -F "file=@document.txt"
```

## ⚙️ Configuration

**Backend** (`.env`):
- API keys for OpenRouter
- Debug mode settings
- Server host/port

**Frontend** (`.js`):
- API URL: `http://localhost:5000/api`
- Change in `src/App.js` if needed

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port in use | Kill process: `taskkill /PID xxx /F` |
| Dependencies missing | `pip install -r requirements.txt` or `npm install` |
| CORS error | Ensure backend running on port 5000 |
| No API output | Check `.env` has valid keys or fallback to mock |
| npm not found | Install Node.js from nodejs.org |
| python not found | Install Python from python.org |

## 📊 File Limits
- **Format**: .txt only
- **Max Size**: 10 MB
- **Recommended**: 500-5000 words

## 🎨 UI Customization

**Colors** (in `frontend/src/App.css`):
- Primary: `#667eea` to `#764ba2` (gradient)
- Success: `#3c3`
- Error: `#c33`

**SOLO Level Colors**:
- Prestructural: `#667eea` (blue)
- Multistructural: `#f093fb` (pink)
- Relational: `#4facfe` (cyan)
- Extended Abstract: `#00f2fe` (bright cyan)

## 🔄 Development Workflow

```
Edit Code
    ↓
Backend: Restart python app.py
Frontend: Auto-refresh (hot reload)
    ↓
Test in Browser
    ↓
Upload file & Generate Quiz
```

## 📚 File Locations

| File | Purpose |
|------|---------|
| `backend/app.py` | Flask API server |
| `backend/quiz_generator.py` | Quiz generation logic |
| `frontend/src/App.js` | Main React component |
| `frontend/src/components/FileUpload.js` | Upload component |
| `frontend/src/components/QuizDisplay.js` | Quiz display |
| `backend/.env` | API keys & config |

## 🔗 Key Endpoints Response

```json
{
  "metadata": {
    "filename": "education.txt",
    "generated_at": "2025-12-06T...",
    "total_chapters": 5,
    "total_questions": 20
  },
  "chapters": [
    {
      "chapter_number": 1,
      "title": "Chapter Name",
      "questions": [
        {
          "solo_level": "prestructural",
          "question_data": {
            "question": "What is...?",
            "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
            "correct_answer": "A) ...",
            "explanation": "..."
          }
        }
      ]
    }
  ]
}
```

## 💾 Export Format

Quiz is downloaded as `quiz.json` containing complete question data suitable for:
- Learning management systems
- Educational apps
- Research databases
- Custom integrations

## 🎓 Tips & Tricks

1. **Large Files**: Split into chapters with headings (=== CHAPTER ===)
2. **Better Results**: Clear, structured educational content works best
3. **Mock Mode**: Backend uses templates if API unavailable
4. **Debugging**: Check console (F12) for error details
5. **Performance**: 2000-word file typically takes 60-90 seconds

## 📞 Support

For issues:
1. Check SETUP_GUIDE.md for detailed help
2. See README.md for full documentation  
3. Review PROJECT_SUMMARY.md for overview
4. Check terminal output for errors

---

**Version**: 1.0  
**Last Updated**: December 2025  
**Status**: Production Ready ✅

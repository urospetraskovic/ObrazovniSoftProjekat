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

Then open **http://localhost:3001** in your browser.

---

## 🔌 API Providers - Easy Switching Guide

You have **two AI providers** available. Switch between them based on your needs!

### Option 1: OpenRouter API (Current Default)
Your primary API provider for quiz generation and content parsing.

**Status:** 12 API keys configured with daily rotation  
**Used for:** Content parsing, question generation, lesson analysis  
**Free tier:** Limited requests per day (rotates across keys automatically)

#### How it works:
- Already configured in `.env` file
- Simply run `python app.py` - it uses OpenRouter by default
- When one key is exhausted, automatically switches to the next
- Fallback to GitHub Models when all keys are rate-limited

---

### Option 2: Google Gemini API (⚡ Fast Alternative)
High-speed alternative for when you need dedicated endpoints.

**Status:** ✅ Fully configured and ready  
**API Key:** `AIzaSyDiBmhk7mk3if_mzAeURWWXoZ-uf5C4H_U`  
**Free tier quota:** Resets every 24 hours  
**Used for:** Quiz generation, summaries, learning objectives, answer explanations

#### Available Gemini Endpoints:

**1️⃣ Check if Gemini API is available:**
```bash
curl http://localhost:5000/api/gemini/health
```

**2️⃣ Generate quiz questions:**
```bash
curl -X POST http://localhost:5000/api/gemini/generate-quiz \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your lesson content here",
    "num_questions": 10,
    "question_type": "multiple_choice"
  }'
```

**3️⃣ Generate learning summary:**
```bash
curl -X POST http://localhost:5000/api/gemini/generate-summary \
  -H "Content-Type: application/json" \
  -d '{"content": "Your content to summarize"}'
```

**4️⃣ Generate learning objectives:**
```bash
curl -X POST http://localhost:5000/api/gemini/generate-objectives \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_title": "Your Lesson Title",
    "content": "Your lesson content"
  }'
```

**5️⃣ Get detailed answer explanations:**
```bash
curl -X POST http://localhost:5000/api/gemini/explain-answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is photosynthesis?",
    "correct_answer": "The process by which plants convert sunlight into chemical energy"
  }'
```

---

## 🔄 When to Use Each Provider

| Situation | Provider | Reason |
|-----------|----------|--------|
| Normal operation | OpenRouter | Default, automatic fallbacks |
| OpenRouter exhausted | Gemini | Keep app running |
| Need instant response | Gemini | Faster processing |
| PDF content parsing | OpenRouter | Better for document analysis |
| Batch operations | OpenRouter | More cost-effective |
| Testing/Development | Gemini | Simple, dedicated endpoints |

---

## 📊 Current Setup

- **Backend API:** http://localhost:5000
- **Frontend:** http://localhost:3001
- **Database:** SQLite (auto-created: `quiz_database.db`)
- **OpenRouter Keys:** 12 keys loaded (9 active for API calls)
- **Gemini:** Ready with free tier daily quota

---

## 🚀 Features

### 📚 Course & Lesson Management
- Create courses to organize your content
- Upload PDF lessons to courses
- AI automatically extracts sections and learning objects

### ❓ Intelligent Question Generation
- Generate SOLO taxonomy-leveled questions
- Support for multiple question types (multiple choice, true/false, short answer)
- Questions organized by SOLO levels (Unistructural → Extended Abstract)
- View and manage question bank

### 📝 Quiz Building & Taking
- **Build Quiz**: Create custom quizzes by selecting questions
- **Take Quiz**: Solve quizzes with instant feedback
- See your score with pass/fail status
- Review correct answers and explanations
- Practice unlimited retakes

### 🎨 Modern Professional Interface
- Beautiful sidebar navigation
- Responsive design (desktop, tablet, mobile)
- Professional color scheme and typography
- Smooth animations and transitions
- Real-time form validation

## Database
This project uses **SQLite** - no additional installation required! The database file (`quiz_database.db`) is created automatically when you first run the backend.

Stored data:
- Courses and lessons
- Parsed sections and learning objects
- Generated questions
- Created quizzes

## API Key Management
- **Primary**: OpenRouter API (9 keys for daily limits)
- **Fallback**: GitHub Models (gpt-4o) + Gemini API
- **Alert**: Frontend displays warning when keys are exhausted for the day
- Check status: The app checks API status every 30 seconds and shows a notification if all keys are rate-limited

## Where Are My Quizzes?
See [QUIZ_FEATURE_GUIDE.md](./QUIZ_FEATURE_GUIDE.md) for complete documentation on:
- Where quizzes are stored
- How to use the Take Quiz feature
- Quiz database structure
- Creating and solving quizzes

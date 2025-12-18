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

## Features

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
- **Fallback**: GitHub Models (gpt-4o)
- **Alert**: Frontend displays warning when keys are exhausted for the day
- Check status: The app checks API status every 30 seconds and shows a notification if all keys are rate-limited

## Where Are My Quizzes?
See [QUIZ_FEATURE_GUIDE.md](./QUIZ_FEATURE_GUIDE.md) for complete documentation on:
- Where quizzes are stored
- How to use the Take Quiz feature
- Quiz database structure
- Creating and solving quizzes
# SOLO Quiz Generator - Major Refactoring Guide

## Overview

This is a major architectural change to support the new workflow:
**Course → Lesson → Section → Learning Objects → Questions → Quiz**

## New Files Created

### Backend (Python)
- `backend/database.py` - SQLAlchemy database models and operations
- `backend/content_parser.py` - AI-powered PDF content extraction
- `backend/app_new.py` - Refactored API with new endpoints

### Frontend (React)
- `frontend/src/App_new.js` - New main application component
- `frontend/src/components/CourseManager.js` - Course CRUD operations
- `frontend/src/components/LessonManager.js` - Lesson upload and management
- `frontend/src/components/ContentViewer.js` - View parsed sections/learning objects
- `frontend/src/components/QuestionGenerator.js` - SOLO-based question generation
- `frontend/src/components/QuestionBank.js` - View/manage generated questions
- `frontend/src/components/QuizBuilder.js` - Build quizzes from question bank
- `frontend/src/App.new.css` - New UI styles

## How to Activate the New System

### Step 1: Install new dependencies

```bash
cd backend
pip install SQLAlchemy==2.0.23
```

### Step 2: Replace the old files with new ones

```bash
# Backend
mv backend/app.py backend/app_old.py
mv backend/app_new.py backend/app.py

# Frontend  
mv frontend/src/App.js frontend/src/App_old.js
mv frontend/src/App_new.js frontend/src/App.js

# CSS - append new styles
cat frontend/src/App.new.css >> frontend/src/App.css
```

### Step 3: Remove old components (optional)
You can delete these old components that are no longer needed:
- `frontend/src/components/TextInput.js` (removed - no more direct text input)
- `frontend/src/components/FileUpload.js` (replaced by LessonManager)
- `frontend/src/components/QuizLoader.js` (replaced by QuizBuilder)

## New Workflow

### 1. Create a Course
- Go to "Courses" tab
- Click "New Course"
- Enter name (e.g., "Operating Systems"), code (e.g., "OS"), description

### 2. Upload Lessons
- Select your course
- Go to "Lessons" tab
- Upload PDF files (e.g., "08 - Virtuelna memorija.pdf")
- Each PDF becomes a "Lesson"

### 3. Parse Lessons
- Click "Parse" on each lesson
- AI extracts:
  - **Sections**: Major topic divisions
  - **Learning Objects**: Specific concepts, definitions, procedures

### 4. Generate Questions
- Go to "Generate Questions" tab
- Select one or more lessons
- Choose SOLO levels:
  - **Unistructural**: Single fact (uses lesson content)
  - **Multistructural**: Multiple facts (uses sections)
  - **Relational**: Analyze relationships (uses learning objects)
  - **Extended Abstract**: Combine 2 lessons (requires selecting 2 lessons)
- Set questions per level
- Click "Generate"

### 5. Manage Questions
- Go to "Question Bank" tab
- View all generated questions
- Filter by SOLO level
- Delete unwanted questions

### 6. Build Quizzes
- Go to "Build Quiz" tab
- Set quiz title and settings
- Select questions manually or use "Quick Select"
- Create and export quiz

## API Endpoints

### Courses
- `GET /api/courses` - List all courses
- `POST /api/courses` - Create course
- `GET /api/courses/:id` - Get course with lessons
- `DELETE /api/courses/:id` - Delete course

### Lessons
- `GET /api/courses/:id/lessons` - List lessons
- `POST /api/courses/:id/lessons` - Upload PDF lesson
- `GET /api/lessons/:id` - Get lesson with sections
- `POST /api/lessons/:id/parse` - Parse lesson (AI extraction)
- `DELETE /api/lessons/:id` - Delete lesson

### Sections & Learning Objects
- `GET /api/lessons/:id/sections` - List sections
- `GET /api/sections/:id` - Get section with learning objects
- `GET /api/sections/:id/learning-objects` - List learning objects

### Questions
- `POST /api/generate-questions` - Generate questions from lessons
- `GET /api/questions` - List questions (filter by course_id, lesson_id, solo_level)
- `DELETE /api/questions/:id` - Delete question

### Quizzes
- `POST /api/quizzes` - Create quiz
- `GET /api/quizzes/:id` - Get quiz with questions
- `POST /api/quizzes/:id/add-questions` - Add questions to quiz
- `GET /api/quizzes/:id/export` - Export quiz to JSON

## Database Schema

The SQLite database (`backend/quiz_database.db`) contains:

- **courses**: id, name, code, description
- **lessons**: id, course_id, title, filename, file_path, raw_content, summary
- **sections**: id, lesson_id, title, content, summary, start_page, end_page
- **learning_objects**: id, section_id, title, content, object_type, keywords
- **questions**: id, primary_lesson_id, secondary_lesson_id, section_id, learning_object_id, solo_level, question_text, options, correct_answer, explanation
- **quizzes**: id, course_id, title, description, time_limit_minutes
- **quiz_questions**: id, quiz_id, question_id, order_index, points

## SOLO Taxonomy Implementation

| Level | Source | Description |
|-------|--------|-------------|
| Unistructural | Single Lesson | Identify single facts, terms, definitions |
| Multistructural | Sections | List, describe, enumerate multiple related facts |
| Relational | Learning Objects | Compare, explain relationships, analyze |
| Extended Abstract | 2 Lessons Combined | Generalize, create, apply to new contexts |

## Notes

- Old quiz files in `downloaded_quizzes/` remain compatible
- The text input feature has been removed (professor's requirement)
- Only PDF files are now accepted for lessons
- Questions are stored in database and can be reused across quizzes

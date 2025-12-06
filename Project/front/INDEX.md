# 📚 SOLO Quiz Generator - Complete Documentation Index

## 🎯 Project Overview

**SOLO Taxonomy Quiz Generator** is a full-stack web application that automatically generates educational quizzes from uploaded text content using the SOLO (Structure of Observed Learning Outcomes) taxonomy framework.

**Location**: `D:\GitHub\ObrazovniSoftProjekat\Project\front\`

---

## 📖 Documentation Guide

### Start Here 👇

1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** ⚡
   - Quick start commands
   - URL references
   - Common commands
   - Troubleshooting quick fixes
   - **Best for**: Quick lookups and fast setup

2. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** 🔧
   - Detailed step-by-step instructions
   - System requirements
   - Installation procedures
   - Verification steps
   - Comprehensive troubleshooting
   - **Best for**: First-time users, detailed setup help

3. **[README.md](README.md)** 📚
   - Complete project documentation
   - Features overview
   - Project structure
   - API documentation
   - SOLO taxonomy explanation
   - Configuration guide
   - **Best for**: Reference, API details, configuration

4. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** 📊
   - High-level overview
   - Architecture description
   - Features implemented
   - File structure explanation
   - Development tips
   - Future enhancements
   - **Best for**: Understanding the big picture, development

5. **[CHECKLIST.md](CHECKLIST.md)** ✅
   - Implementation checklist
   - Features status
   - Next steps
   - Quality assurance details
   - **Best for**: Tracking progress, verification

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt

cd ../frontend
npm install
```

### Step 2: Start Application
**Windows:**
```bash
start.bat
```

**macOS/Linux:**
```bash
./start.sh
```

**Manual:**
```bash
# Terminal 1
cd backend && python app.py

# Terminal 2
cd frontend && npm start
```

### Step 3: Use Application
1. Open http://localhost:3000
2. Upload a .txt file
3. Click "Generate Quiz"
4. Download results

---

## 📁 Project Structure

```
front/
├── frontend/                      React application
│   ├── public/
│   │   └── index.html            HTML entry point
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.js     Upload component
│   │   │   └── QuizDisplay.js    Quiz display
│   │   ├── App.js                Main component
│   │   ├── App.css               Styles
│   │   └── index.js              React entry
│   └── package.json              npm config
│
├── backend/                       Flask API
│   ├── app.py                    Flask server
│   ├── quiz_generator.py         Quiz logic
│   ├── requirements.txt          Python deps
│   ├── .env                      Configuration
│   └── uploads/                  Temp uploads
│
├── Documentation
│   ├── README.md                 Full docs
│   ├── SETUP_GUIDE.md            Setup steps
│   ├── PROJECT_SUMMARY.md        Overview
│   ├── QUICK_REFERENCE.md        Quick lookup
│   ├── CHECKLIST.md              Progress
│   └── INDEX.md                  This file
│
├── Startup Scripts
│   ├── start.bat                 Windows
│   └── start.sh                  Unix
│
└── Configuration
    └── backend/.env              API keys
```

---

## 🎯 Feature Overview

### What It Does
- ✅ Accepts .txt file uploads
- ✅ Analyzes educational content
- ✅ Generates questions at 5 SOLO levels
- ✅ Creates multiple-choice format
- ✅ Provides explanations
- ✅ Exports as JSON

### What You Need
- Node.js 14+ (for frontend)
- Python 3.8+ (for backend)
- npm (for dependencies)
- OpenRouter API keys (for generation)

### What You Get
- Modern web UI
- REST API
- JSON quiz exports
- Beautiful question display
- Error handling
- File validation

---

## 🌐 URLs & Ports

| Service | URL | Port |
|---------|-----|------|
| Frontend | http://localhost:3000 | 3000 |
| Backend | http://localhost:5000 | 5000 |
| API Health | http://localhost:5000/api/health | 5000 |
| Quiz Gen | http://localhost:5000/api/generate-quiz | 5000 |

---

## 📚 SOLO Taxonomy Levels

### 1. Prestructural (Basic)
- Simple recall
- Term recognition
- Basic facts
- Example: "What is ecology?"

### 2. Unistructural
- Single aspect
- Definition focus
- One characteristic
- Example: "Define biodiversity"

### 3. Multistructural
- Multiple aspects
- Listing components
- Independent elements
- Example: "List the components of..."

### 4. Relational
- Relationships
- Cause-effect
- Comparisons
- Example: "How does X affect Y?"

### 5. Extended Abstract
- Real-world application
- Hypothetical scenarios
- Transfer of knowledge
- Example: "What would happen if...?"

---

## 🔑 Configuration

### Backend (.env)
```env
# API Keys (from OpenRouter)
OPENROUTER_API_KEY=your_key
OPENROUTER_API_KEY_2=your_key
...

# Server settings
FLASK_ENV=development
DEBUG=True
```

### Frontend
Edit `src/App.js` to change API URL:
```javascript
const API_URL = 'http://localhost:5000/api';
```

### File Upload
- Max size: 10 MB
- Format: .txt only
- Recommended: 500-5000 words

---

## 🛠️ Common Commands

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python app.py

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### Frontend
```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm build
```

### Testing
```bash
# Backend health check
curl http://localhost:5000/api/health

# Upload file and generate quiz
curl -X POST http://localhost:5000/api/generate-quiz \
  -F "file=@yourfile.txt"
```

---

## 📊 API Reference

### Health Check
```
GET /api/health
Returns: {"status": "ok", "message": "API is running"}
```

### Generate Quiz
```
POST /api/generate-quiz
Content-Type: multipart/form-data
Body: file (text file)

Returns: Quiz JSON with chapters and questions
```

### Response Format
```json
{
  "metadata": {
    "filename": "string",
    "generated_at": "ISO-8601",
    "total_chapters": number,
    "total_questions": number
  },
  "chapters": [...]
}
```

---

## 🐛 Troubleshooting Matrix

| Problem | Cause | Solution |
|---------|-------|----------|
| Port 3000/5000 in use | Another app using port | Kill process or change port |
| "Module not found" | Dependencies missing | `npm install` or `pip install -r requirements.txt` |
| CORS error | Backend not running | Start backend on port 5000 |
| File upload fails | File too large | Max 10MB, use smaller file |
| No API output | Missing API keys | Add keys to `.env` file |
| "node: command not found" | Node not installed | Install Node.js from nodejs.org |
| "python: command not found" | Python not installed | Install Python from python.org |

For more help: See [SETUP_GUIDE.md](SETUP_GUIDE.md) troubleshooting section

---

## 💡 Usage Workflow

```
1. Open Application
   ↓ http://localhost:3000
   ↓
2. Upload Text File
   ↓ Select .txt file with content
   ↓
3. Generate Quiz
   ↓ Click "Generate Quiz" button
   ↓
4. Wait for Processing
   ↓ 30-120 seconds depending on file size
   ↓
5. View Results
   ↓ See questions organized by SOLO levels
   ↓
6. Expand Questions
   ↓ Click to see full details, options, explanations
   ↓
7. Download
   ↓ Export quiz as JSON file
   ↓
8. Use Quiz
   ↓ Integrate with LMS, assessment tools, etc.
```

---

## 🎨 UI Features

### Frontend Components
- **FileUpload**: Drag-drop file upload with validation
- **QuizDisplay**: Expandable question cards with explanations
- **Responsive Design**: Works on desktop and tablet
- **Color-Coded Levels**: Each SOLO level has distinct colors
- **Loading States**: Progress indicators
- **Error Handling**: User-friendly error messages
- **Export**: Download quiz as JSON

### Design Elements
- Modern gradient background
- Smooth transitions and animations
- Intuitive user interface
- Clear visual hierarchy
- Accessible color contrast

---

## 📈 Development & Customization

### To Modify Quiz Generation
1. Edit `backend/quiz_generator.py`
2. Update `_build_prompt()` method
3. Restart backend server

### To Customize UI
1. Edit `frontend/src/App.css` for styles
2. Edit `frontend/src/App.js` for layout
3. Changes appear automatically (hot reload)

### To Add Features
1. See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for suggestions
2. Implement in appropriate file
3. Test thoroughly
4. Document changes

---

## 📚 File Reference Guide

### Main Application Files
| File | Purpose | Language |
|------|---------|----------|
| `backend/app.py` | Flask API server | Python |
| `backend/quiz_generator.py` | Quiz generation logic | Python |
| `frontend/src/App.js` | Main React component | JavaScript |
| `frontend/src/components/FileUpload.js` | Upload component | JavaScript |
| `frontend/src/components/QuizDisplay.js` | Quiz display | JavaScript |

### Configuration Files
| File | Purpose |
|------|---------|
| `backend/.env` | API keys and settings |
| `frontend/package.json` | npm dependencies |
| `backend/requirements.txt` | Python dependencies |

### Documentation Files
| File | Content |
|------|---------|
| `README.md` | Complete documentation |
| `SETUP_GUIDE.md` | Setup instructions |
| `PROJECT_SUMMARY.md` | Project overview |
| `QUICK_REFERENCE.md` | Quick lookup |
| `CHECKLIST.md` | Implementation status |
| `INDEX.md` | This file |

### Script Files
| File | Purpose |
|------|---------|
| `start.bat` | Windows auto-start |
| `start.sh` | Unix auto-start |

---

## 🎓 Learning Resources

### Understanding SOLO Taxonomy
- [Biggs & Collis Original Work](https://en.wikipedia.org/wiki/Structure_of_observed_learning_outcomes)
- 5 distinct cognitive levels from basic to abstract
- Useful for curriculum design and assessment

### Understanding the Stack
- **Frontend**: React - UI library for building interfaces
- **Backend**: Flask - Python web framework for APIs
- **API**: REST principles for client-server communication
- **Database**: JSON for quiz data storage/export

### Educational Benefits
- Assess understanding at multiple cognitive levels
- Automatically generate appropriate questions
- Ensure comprehensive curriculum coverage
- Track student progression through levels

---

## 📞 Support & Help

### Quick Help
- See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for fast answers
- Check troubleshooting sections in [SETUP_GUIDE.md](SETUP_GUIDE.md)

### Detailed Help
- Read [README.md](README.md) for comprehensive reference
- Review [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for architecture

### Common Questions
1. **Where are files?** → See folder structure above
2. **How to start?** → Quick Start section or SETUP_GUIDE.md
3. **How to customize?** → PROJECT_SUMMARY.md development tips
4. **API endpoints?** → README.md API Reference section
5. **Having issues?** → SETUP_GUIDE.md Troubleshooting

---

## 🚀 Next Steps

### For New Users
1. Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (5 min)
2. Follow [SETUP_GUIDE.md](SETUP_GUIDE.md) (15 min)
3. Run the application (5 min)
4. Test with a sample file (10 min)

### For Developers
1. Read [README.md](README.md) for API docs
2. Review [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for architecture
3. Explore code in `backend/` and `frontend/`
4. Make customizations as needed

### For Integration
1. Understand JSON response format (see README.md)
2. Build consumer application for quiz data
3. Integrate with LMS or educational platform
4. Customize question generation as needed

---

## ✅ Verification Checklist

After setup, verify:
- [ ] Backend running on http://localhost:5000
- [ ] Frontend accessible at http://localhost:3000
- [ ] Health check returns success
- [ ] Can upload a .txt file
- [ ] Quiz generates without errors
- [ ] Questions display correctly
- [ ] Can download JSON
- [ ] All SOLO levels present

---

## 📝 Version Information

| Component | Version | Status |
|-----------|---------|--------|
| Project | 1.0 | ✅ Production Ready |
| React | 18.2.0 | ✅ Stable |
| Flask | 2.3.0 | ✅ Stable |
| Node.js | 14+ | ✅ Required |
| Python | 3.8+ | ✅ Required |

---

## 🎉 You're Ready!

The SOLO Taxonomy Quiz Generator is fully implemented, documented, and ready to use!

### Summary
- ✅ Full-stack application implemented
- ✅ All features working
- ✅ Comprehensive documentation
- ✅ Easy to setup and use
- ✅ Ready for customization

### Start Using It Today!
```bash
# Navigate to project
cd D:\GitHub\ObrazovniSoftProjekat\Project\front

# Run application
start.bat  # Windows
# or
./start.sh  # macOS/Linux

# Open in browser
http://localhost:3000
```

---

**Created**: December 2025  
**Status**: ✅ Complete and Ready  
**Last Updated**: December 6, 2025

For questions or issues, refer to the appropriate documentation file above.

Enjoy generating educational quizzes! 🚀📚

# 🎯 Getting Started - Visual Guide

## 📍 You Are Here

```
D:\GitHub\ObrazovniSoftProjekat\
├── Project/                    ← Your original project
│   ├── main.py
│   ├── prompts.py
│   ├── generated_quizzes/      ← Has ecology_questions_and_answers.txt
│   └── raw_material/           ← Has ecology_lesson.txt
│
└── Project/front/              ← NEW WEB APPLICATION (THIS IS WHAT WE BUILT!)
    ├── frontend/               ← React UI
    ├── backend/                ← Flask API
    ├── README.md               ← Start here for docs
    └── start.bat              ← Click to run on Windows
```

---

## 🚀 Step 1: Install Dependencies (One-Time)

### Windows PowerShell

```powershell
# Navigate to project
cd D:\GitHub\ObrazovniSoftProjekat\Project\front

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### macOS/Linux Terminal

```bash
cd D:\GitHub\ObrazovniSoftProjekat\Project\front
cd backend
pip install -r requirements.txt
cd ../frontend
npm install
```

---

## 🎬 Step 2: Start the Application

### Option A: Windows Users (Easiest)
```
1. Open file explorer
2. Navigate to: D:\GitHub\ObrazovniSoftProjekat\Project\front\
3. Double-click: start.bat
4. Wait 10 seconds
5. Browser opens automatically
```

### Option B: macOS/Linux Users
```bash
cd D:\GitHub\ObrazovniSoftProjekat\Project\front
chmod +x start.sh
./start.sh
```

### Option C: Manual Start (All Platforms)

**Terminal 1 (Backend):**
```bash
cd D:\GitHub\ObrazovniSoftProjekat\Project\front\backend
python app.py
# Should show: Running on http://localhost:5000
```

**Terminal 2 (Frontend):**
```bash
cd D:\GitHub\ObrazovniSoftProjekat\Project\front\frontend
npm start
# Browser opens at http://localhost:3000
```

---

## 🌐 Step 3: Access the Application

Once both services are running:

```
Open your browser and go to:
http://localhost:3000
```

You should see:
- Title: "🎓 SOLO Taxonomy Quiz Generator"
- Subtitle: "Upload educational content and generate adaptive quizzes using SOLO taxonomy"
- Left panel: "📤 Upload Content"
- Right panel: "ℹ️ How it works"

---

## 📤 Step 4: Upload a File

### Using Existing Files

You can use the ecology lesson you created earlier:

```
Location: D:\GitHub\ObrazovniSoftProjekat\Project\raw_material\ecology_lesson.txt
```

### Steps:
1. Click the blue upload box
   - It says: "📁 Click to select .txt file or drag & drop"
2. Select a .txt file
3. File info appears showing name, size, type
4. Click "🚀 Generate Quiz" button

---

## ⏳ Step 5: Wait for Processing

The application will:
1. Upload your file
2. Send it to backend
3. Backend analyzes content
4. Generates questions for each SOLO level
5. Returns quiz data

**Typical time: 30-120 seconds** (depending on file size)

You'll see: "⏳ Generating..." with a spinner

---

## 📋 Step 6: View Quiz Results

After generation completes:

```
Quiz Display Shows:
├── Chapter Information
│   ├── Chapter number
│   ├── Title
│   └── Content preview
│
├── Questions by SOLO Level
│   ├── 1️⃣ Prestructural - Blue questions
│   ├── 3️⃣ Multistructural - Pink questions
│   ├── 4️⃣ Relational - Cyan questions
│   └── 5️⃣ Extended Abstract - Bright cyan questions
│
└── For Each Question
    ├── Question text
    ├── 4 multiple choice options
    ├── Correct answer highlighted
    └── Explanation text
```

### To View Details:
1. Click on any question card
2. Card expands to show full content
3. Click again to collapse

---

## 💾 Step 7: Download Quiz

```
Click: "💾 Download Quiz (JSON)"

This saves: quiz.json
Contains: All questions, answers, explanations in JSON format
```

---

## 🔄 Step 8: Generate Another Quiz

```
Click: "↺ Generate New Quiz"

This will:
1. Clear current results
2. Return to upload screen
3. Ready for new file
```

---

## 🛑 Troubleshooting Quick Links

### Issue: "Port already in use"
```powershell
# Find and kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Issue: Dependencies not installed
```bash
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

### Issue: "Cannot find module" when running
```bash
# Make sure you're in correct directory
# And dependencies are installed
npm install   # for frontend
pip install -r requirements.txt  # for backend
```

### Issue: CORS error when uploading
Make sure backend is running on http://localhost:5000

### Issue: File won't upload
- Max 10MB
- Must be .txt format
- Check file isn't corrupted

---

## 📊 SOLO Levels Explained

### 1️⃣ Prestructural (Blue)
**What it tests:** Basic recall
**Example:** "What is ecology?"
**Student level:** Just started learning

### 3️⃣ Multistructural (Pink)
**What it tests:** Multiple facts without connections
**Example:** "List the 5 SOLO levels"
**Student level:** Can remember facts

### 4️⃣ Relational (Cyan)
**What it tests:** Understanding connections
**Example:** "How do predators affect prey populations?"
**Student level:** Understands relationships

### 5️⃣ Extended Abstract (Bright Cyan)
**What it tests:** Real-world application
**Example:** "How would you manage an invasive species?"
**Student level:** Can apply knowledge

---

## 🎨 UI Features Explained

### Color-Coded Questions
- Each SOLO level has a unique color
- Easy to identify question difficulty
- Helps track learning progression

### Expandable Cards
- Click to expand and see details
- Reduces screen clutter
- Easy to focus on one question

### File Upload Area
- Drag and drop support
- Displays selected file info
- Shows file name, size, type

### Loading Indicator
- Spinner appears during processing
- Shows "Generating..." text
- Prevents duplicate submissions

### Download Button
- Exports quiz as JSON
- Preserves all metadata
- Ready for integration elsewhere

---

## 💡 Usage Tips

1. **Best Results**: Use well-structured educational content
2. **File Size**: 500-5000 words works best
3. **Formatting**: Clear chapter headings help
4. **Content**: More specific content = better questions
5. **Multiple Files**: Can generate multiple quizzes
6. **Export Format**: JSON works with any platform

---

## 🔧 Customization (Optional)

### Change UI Colors
Edit: `frontend/src/App.css`
Look for color values like `#667eea`, `#764ba2`, etc.

### Modify Quiz Generation
Edit: `backend/quiz_generator.py`
Look for `_build_prompt()` method

### Change Ports
- **Frontend**: Edit `frontend/src/App.js` line with `API_URL`
- **Backend**: Edit `backend/app.py` last line `port=5000`

---

## ✅ Verification Checklist

After setup, verify:
- [ ] Backend running (see "Running on http://localhost:5000")
- [ ] Frontend loaded (see "http://localhost:3000" in browser)
- [ ] Can select file (file appears in upload area)
- [ ] Can generate quiz (button becomes enabled)
- [ ] Quiz displays properly (all questions visible)
- [ ] Can download (JSON file saved)

---

## 📚 Documentation Map

```
Quick Answer? 
→ QUICK_REFERENCE.md

Need to Setup?
→ SETUP_GUIDE.md

Want Full Details?
→ README.md

Need Architecture Info?
→ PROJECT_SUMMARY.md

Checking Status?
→ CHECKLIST.md

Lost in Documentation?
→ INDEX.md (this file)
```

---

## 🎯 Common Tasks

### Generate Quiz from Ecology Lesson
1. Upload: `raw_material/ecology_lesson.txt`
2. Click "Generate Quiz"
3. Wait ~60 seconds
4. Download JSON

### Use Quiz in Learning Platform
1. Download JSON
2. Parse JSON in your application
3. Display questions as needed
4. Track student answers

### Modify Question Generation
1. Edit `backend/quiz_generator.py`
2. Change prompts in `_build_prompt()` method
3. Restart backend: `python app.py`
4. Test with new file

### Change UI Theme
1. Edit `frontend/src/App.css`
2. Change color hex values
3. Auto-reloads in browser
4. Test appearance

---

## 🎓 Educational Use Cases

### For Teachers
- Generate quiz questions from lesson notes
- Create assessments at multiple cognitive levels
- Test student understanding progression
- Export for use in LMS

### For Students
- Self-test at different cognitive levels
- Track learning from basic to advanced
- Practice with auto-generated questions
- Prepare for exams

### For Curriculum Design
- Ensure content covers all SOLO levels
- Assess learning outcomes
- Design progressive assessments
- Validate teaching material

---

## 🚀 Next Steps After Setup

1. **Explore**: Upload different files and see results
2. **Experiment**: Try various content types
3. **Customize**: Modify colors or generation logic
4. **Integrate**: Use JSON in your systems
5. **Deploy**: Run in production environment

---

## 📞 Getting Help

### Quick Questions
→ See QUICK_REFERENCE.md

### Setup Issues
→ See SETUP_GUIDE.md troubleshooting

### Technical Details
→ See README.md

### Project Architecture
→ See PROJECT_SUMMARY.md

### Implementation Status
→ See CHECKLIST.md

---

## ✨ Ready to Start?

### Quick Checklist
1. ✅ Navigate to: `D:\GitHub\ObrazovniSoftProjekat\Project\front\`
2. ✅ Install dependencies (if first time)
3. ✅ Run `start.bat` or manual commands
4. ✅ Open http://localhost:3000
5. ✅ Upload a .txt file
6. ✅ Generate quiz
7. ✅ Download results
8. ✅ Enjoy!

---

## 🎉 You're All Set!

Everything is installed, configured, and ready to use.

**Go ahead and start generating quizzes!** 🚀

---

**Questions?** Check the documentation files  
**Issues?** See SETUP_GUIDE.md troubleshooting  
**Want details?** Read README.md  
**Need quick answer?** Check QUICK_REFERENCE.md

**Happy learning!** 📚✨

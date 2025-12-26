# 🎯 Complete Setup Guide for New PC
## SOLO Quiz Generator Project with Local AI Models

**Date:** December 26, 2025  
**Purpose:** Full setup instructions for running this project on a fresh Windows PC with local AI models

---

## 🎯 Key Point: Zero Project Code Changes Required

This guide is about **installing dependencies and models on your new PC**. Your project code stays exactly the same:
- ✅ Same folder structure
- ✅ Same files and logic
- ✅ Same workflows
- ✅ Just use local models instead of cloud APIs when ready

---

## ⚡ IMPORTANT: No Code Changes Required!

**Your project code does NOT need to be modified.** This guide is only about:
- Installing dependencies on your new PC
- Setting up local Ollama models
- Pointing your existing code to use local models instead of cloud APIs

✅ Your current project structure remains exactly the same  
✅ Your existing workflows continue to work  
✅ Just swap API keys/endpoints for local model configuration  

---

## 📋 Table of Contents
1. [System Requirements](#system-requirements)
2. [Step-by-Step Installation](#step-by-step-installation)
3. [Local AI Model Setup](#local-ai-model-setup)
4. [Switching to Local Models](#switching-to-local-models)
5. [Optional: Recommended Architecture](#optional-recommended-architecture)
6. [Verification & Testing](#verification--testing)
7. [Troubleshooting](#troubleshooting)

---

## 🖥️ System Requirements

### Minimum Hardware
- **CPU:** Multi-core processor (Intel i5/Ryzen 5 or better)
- **RAM:** 16 GB (32 GB recommended for smooth operation)
- **GPU:** NVIDIA GPU with CUDA support (recommended for faster inference)
- **Storage:** 50 GB free space (for models + dependencies + project files)
- **OS:** Windows 10/11

### Network
- Stable internet connection (for initial downloads)
- No need for cloud API access (everything runs locally)

---

## 🚀 Step-by-Step Installation

### Step 1: Install Python
1. Download Python 3.11 from [python.org](https://www.python.org/downloads/)
   - **Important:** Check "Add Python to PATH" during installation
   - Choose "Install Now" or customize as needed
2. Verify installation:
   ```powershell
   python --version
   pip --version
   ```

### Step 2: Install Node.js (for Frontend)
1. Download Node.js LTS from [nodejs.org](https://nodejs.org/)
2. Run installer and follow prompts
3. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

### Step 3: Install Git
1. Download from [git-scm.com](https://git-scm.com/)
2. Use default installation settings
3. Verify:
   ```powershell
   git --version
   ```

### Step 4: Clone/Verify Project Repository
```powershell
# Navigate to your project directory
cd "path\to\ObrazovniSoftProjekat\Project\front"

# Verify project structure
dir
```

### Step 5: Set Up Python Virtual Environment

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 6: Install Python Dependencies

```powershell
# Make sure virtual environment is activated
# Install backend dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Backend Dependencies to be installed:**
- Flask 2.3.0 - Web framework
- python-dotenv 1.0.0 - Environment variables
- requests 2.31.0 - HTTP library
- Werkzeug 2.3.0 - WSGI utilities
- flask-cors 4.0.0 - CORS support
- PyPDF2 3.0.1 - PDF parsing
- SQLAlchemy 2.0.36 - Database ORM
- google-generativeai 0.7.2 - Gemini API (for reference, we'll use local models)

### Step 7: Install Additional AI/ML Libraries

```powershell
# Install Ollama and related libraries (for running local models)
pip install ollama
pip install torch torchvision torchaudio
pip install transformers
pip install accelerate  # For GPU optimization

# Install PDF processing libraries
pip install pdfplumber
pip install PyMuPDF  # fitz

# Install additional utilities
pip install python-multipart
pip install python-dateutil
```

**Complete list of additional packages:**
```
ollama - Local AI model runner
torch - Deep learning framework
transformers - HuggingFace model library
accelerate - Distributed training and optimization
pdfplumber - Advanced PDF parsing
PyMuPDF - PDF text extraction
python-multipart - File upload handling
python-dateutil - Date utilities
```

### Step 8: Set Up Frontend Dependencies

```powershell
# Navigate to frontend directory
cd ..\frontend

# Install Node.js dependencies
npm install
```

**Frontend Dependencies:**
- react 18.2.0 - UI library
- react-dom 18.2.0 - DOM rendering
- axios 1.6.0 - HTTP client
- react-scripts 5.0.1 - Build tools

---

## 🤖 Local AI Model Setup

### Install Ollama (Model Manager)

1. **Download Ollama:**
   - Go to [ollama.ai](https://ollama.ai)
   - Download Windows version
   - Run installer

2. **Verify Ollama installation:**
   ```powershell
   ollama --version
   ```

### Pull Required Models

**🥇 PRIMARY MODEL: Qwen2.5-14B-Instruct (for high-quality tasks)**

```powershell
ollama pull qwen2.5:14b-instruct-q4_K_M
```

**Size:** ~8-9 GB  
**Speed:** 1-3 tokens/sec  
**Best for:** Ontology synthesis, SOLO question generation, complex reasoning

**🥈 SECONDARY MODEL: Qwen2.5-7B-Instruct (for fast preprocessing)**

```powershell
ollama pull qwen2.5:7b-instruct-q4_K_M
```

**Size:** ~4-5 GB  
**Speed:** 5-15 tokens/sec  
**Best for:** PDF parsing, section detection, initial LO extraction

### Verify Models

```powershell
ollama list
```

You should see both models listed with their sizes.

---

## 🔄 Switching to Local Models

Your project currently uses cloud APIs (Gemini, OpenAI, etc.). To use local models instead:

### Option 1: Minimal Change (Recommended)
Just replace your API calls with Ollama calls. The process is identical:

**Before (Cloud API):**
```python
from google.generativeai import GenerativeAI
response = client.generate_content(prompt)
```

**After (Local Ollama):**
```python
import ollama
response = ollama.generate(model="qwen2.5:7b-instruct-q4_K_M", prompt=prompt)
```

### Option 2: Keep Everything As-Is
Your project continues working exactly as it does now. When you're ready to switch, just update the model/API configuration in your `.env` file and code will point to local models.

**No structural changes needed.**  
**No workflow changes needed.**  
**Just point to different model endpoints.**

---

## 🏗️ Optional: Recommended Architecture

This section describes the **ideal architecture for future optimization**, but it's **completely optional**. Your project works fine as-is.

**Use this section only if you want to:**
- Improve quality by using the 2-model pipeline approach
- Refactor the pipeline for better performance
- Implement the 5-step processing workflow

**If you're happy with your current setup, skip this entire section and go directly to [Verification & Testing](#verification--testing).**

---

### Why This Architecture is Optional

Your existing project is already working. This architecture is just a suggestion for how to leverage the two models efficiently if you decide to refactor later. Not necessary to implement.

### Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ Input: PDF File                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 1: PDF → Text Extraction (NO LLM)                     │
│ Tools: pdfplumber, PyMuPDF                                 │
│ Output: Clean text with layout info                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Section Segmentation (Qwen2.5-7B)                 │
│ Input: Clean text                                           │
│ Output: JSON with section IDs and headings                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Learning Object Extraction (Qwen2.5-7B)           │
│ Input: Section-tagged text                                  │
│ Output: JSON with LOs, definitions, prerequisites          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Ontology Synthesis (Qwen2.5-14B)                  │
│ Input: Structured LOs                                       │
│ Output: JSON-LD/RDF ontology with relationships            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: SOLO Question Generation (Qwen2.5-14B)            │
│ Input: Ontology + SOLO level constraints                   │
│ Output: Multi-level quiz questions                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Output: Formatted Quiz JSON                                │
└─────────────────────────────────────────────────────────────┘
```

### Model Selection by Task

| Task | Model | Rationale |
|------|-------|-----------|
| PDF parsing | No LLM | Too slow, specialized tools exist |
| Section detection | Qwen2.5-7B | Fast, good accuracy |
| Learning object extraction | Qwen2.5-7B | Efficient for structured data |
| Ontology building | Qwen2.5-14B | Requires deep reasoning |
| SOLO question generation | Qwen2.5-14B | Best at respecting constraints |

### Why This Architecture Works

✅ **7B model** processes fast → GPU stays responsive  
✅ **14B model** handles complex tasks → highest quality  
✅ **CPU+RAM** handle model offloading → no bottlenecks  
✅ **Few hours is fine** → acceptable for offline generation  
✅ **Reduced API costs** → everything runs locally  

---

## 🧪 Verification & Testing

### Test Python Backend

```powershell
# From backend directory with venv activated
python app.py
```

Should output something like:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Test Local AI Models

```powershell
# Test Ollama connection
ollama run qwen2.5:7b-instruct-q4_K_M "What is the capital of France?"

# Test with 14B model
ollama run qwen2.5:14b-instruct-q4_K_M "Explain machine learning in 2 sentences"
```

### Test Frontend

```powershell
# From frontend directory
npm start
```

Should open the React app at `http://localhost:3000`

### Test Full Integration

1. Start backend:
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   python app.py
   ```

2. Start frontend (new terminal):
   ```powershell
   cd frontend
   npm start
   ```

3. Upload a PDF and generate quiz through the UI

---

## 🔧 Configuration Files

### .env File (Backend)

Create `.env` in the `backend` directory:

```env
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here

# Local Ollama Configuration (if using local models)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL_FAST=qwen2.5:7b-instruct-q4_K_M
OLLAMA_MODEL_QUALITY=qwen2.5:14b-instruct-q4_K_M

# Keep your existing API keys (for backward compatibility)
GEMINI_API_KEY=your-key-here
GROQ_API_KEY=your-key-here

# Database
DATABASE_URL=sqlite:///quiz_database.db

# API Settings
MAX_UPLOAD_SIZE=50  # MB
PROCESSING_TIMEOUT=3600  # seconds
```

**Your project code doesn't change** - it continues to work as before. Add the Ollama configuration as needed.

### Simple Model Switching

When you're ready to switch from cloud API to local models, just update your Python code where API calls are made:

```python
# Existing code (cloud)
# response = client.generate_with_gemini(prompt)

# New code (local)
response = ollama.generate(model="qwen2.5:7b-instruct-q4_K_M", prompt=prompt)
```

### Environment Setup Script

Create `setup_env.ps1`:

```powershell
# Activate Python venv
cd backend
.\venv\Scripts\Activate.ps1

# Start Ollama service (if not already running)
# ollama serve

# Start backend
python app.py &

cd ..\frontend
npm start
```

---

## ⚠️ Troubleshooting

### Python Not Found
**Solution:**
- Reinstall Python and ensure "Add to PATH" is checked
- Restart PowerShell after installation

### GPU Not Detected
**Solution:**
```powershell
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# If False, install CUDA-enabled PyTorch:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Ollama Models Not Loading
**Solution:**
```powershell
# Check Ollama service is running
ollama serve

# If port 11434 is in use:
# Find and kill the process, or configure different port
```

### React App Not Starting
**Solution:**
```powershell
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -r node_modules package-lock.json
npm install

# Start again
npm start
```

### Out of Memory During Model Loading
**Solution:**
- Use quantized models (4-bit: `q4_K_M` suffix)
- Increase virtual memory/pagefile
- Close other applications
- Use smaller model (7B instead of 14B) for initial testing

### Slow Performance
**Possible causes and solutions:**
- **HDD vs SSD:** Moving project to SSD significantly improves speed
- **Insufficient RAM:** Reduce other applications
- **GPU VRAM:** Check with `nvidia-smi`
- **Model quantization:** Current setup uses 4-bit quantization (recommended)

### Port Already in Use
```powershell
# Backend (default 5000)
python app.py --port 5001

# Frontend (default 3000)
PORT=3001 npm start
```

---

## 📊 Performance Expectations

### Expected Speeds (on typical gaming PC with RTX 3070+)

| Model | Task | Speed | Time for 10 questions |
|-------|------|-------|----------------------|
| Qwen2.5-7B | Section detection | 8-12 tok/s | ~30 seconds |
| Qwen2.5-14B | Ontology synthesis | 2-4 tok/s | ~3-5 minutes |
| Qwen2.5-14B | Question generation | 2-4 tok/s | ~5-10 minutes |

**Total time for full pipeline:** 10-20 minutes per document

---

## 🎯 Next Steps After Setup

1. **Verify all services running:**
   - Backend API: `http://localhost:5000`
   - Frontend UI: `http://localhost:3000`
   - Ollama: `http://localhost:11434`

2. **Test with sample PDF:**
   - Place sample PDF in `backend/uploads/`
   - Generate quiz through UI
   - Check output in `downloaded_quizzes/`

3. **Monitor performance:**
   - Watch GPU usage during model inference
   - Adjust quantization if needed
   - Profile slow sections

4. **Fine-tune pipeline:**
   - Adjust prompt engineering for better LOs
   - Customize SOLO question constraints
   - Optimize section detection for your document types

---

## 📚 Useful Resources

- **Ollama Documentation:** https://github.com/ollama/ollama
- **Qwen Model Card:** https://huggingface.co/Qwen/Qwen2.5-14B-Instruct
- **PyTorch Setup:** https://pytorch.org/get-started/locally/
- **pdfplumber Documentation:** https://github.com/jsvine/pdfplumber

---

## ✅ Checklist Before Going Live

- [ ] Python 3.11+ installed and in PATH
- [ ] Node.js LTS installed
- [ ] Git installed
- [ ] Virtual environment created and activated
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Ollama installed and running
- [ ] Qwen2.5-7B model pulled
- [ ] Qwen2.5-14B model pulled
- [ ] `.env` file configured
- [ ] Backend starts successfully
- [ ] Frontend starts successfully
- [ ] Sample PDF processes without errors
- [ ] Quiz generated and downloaded successfully

---

**Last Updated:** December 26, 2025  
**Status:** Ready for deployment on new PC

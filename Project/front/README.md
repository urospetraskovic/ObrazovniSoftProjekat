# SOLO Quiz Generator

An intelligent educational software system that automatically generates quiz questions based on the SOLO (Structure of Observed Learning Outcomes) taxonomy. The application uses local AI through Ollama to create pedagogically-structured questions from uploaded course materials.

## Overview

This project is designed to help educators automatically create assessment questions at different cognitive levels. It parses PDF course materials, builds a semantic knowledge graph (ontology), and generates multiple-choice questions categorized by SOLO taxonomy levels:

- **Unistructural** - Simple recall of single facts
- **Multistructural** - Identification of multiple related facts  
- **Relational** - Understanding connections between concepts
- **Extended Abstract** - Higher-order thinking and application

## Key Features

### Question Generation
- Upload PDF course materials
- Automatic parsing into lessons, sections, and learning objects
- AI-powered question generation at all SOLO levels
- Manual question creation and editing
- Question bank management

### Ontology System
- Automatic knowledge graph generation from content
- SPARQL query interface for exploring relationships
- Export to OWL format for use in Protégé
- Export to Turtle format for RDF tools
- Visual relationship mapping

### AI Chatbot
- Context-aware answers based on course content
- Uses RAG (Retrieval-Augmented Generation) architecture
- Explains quiz answers when students need help
- Offline fallback mode when AI is unavailable

### Quiz Management
- Build quizzes from question bank
- Filter questions by topic, SOLO level, or lesson
- Export quizzes to JSON format
- Interactive quiz solving interface
- Translation support for multiple languages

### Translation System
- Translate questions to multiple languages
- Translate entire lessons, sections, or learning objects
- Batch translation support
- Preserves SOLO level metadata

## Tech Stack

**Backend:**
- Python 3.10+
- Flask 2.3.0 (REST API)
- SQLAlchemy 2.0.36 (ORM)
- SQLite (Database)
- RDFLib 7.0.0 (Ontology/SPARQL)
- PyPDF2 (PDF parsing)

**Frontend:**
- React 18
- Axios (HTTP client)
- CSS3 styling

**AI Layer:**
- Ollama (local LLM runner)
- Qwen 2.5 14B model (recommended)

## Prerequisites

Before running the application, make sure you have:

1. **Python 3.10 or higher** - [Download](https://www.python.org/downloads/)
2. **Node.js 18 or higher** - [Download](https://nodejs.org/)
3. **Ollama** - [Download](https://ollama.com/)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd front
```

### 2. Set Up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Up Frontend

```bash
cd frontend
npm install
```

### 4. Set Up Ollama

Download and install Ollama, then pull the recommended model:

```bash
ollama pull qwen2.5:14b
```

## Running the Application

You need to run 3 terminals simultaneously. See [START_GUIDE.md](START_GUIDE.md) for quick start instructions.

**Terminal 1 - Ollama AI Server:**
```bash
.\ollama.ps1 serve
```

**Terminal 2 - Backend API:**
```bash
cd backend
.\venv\Scripts\python.exe app.py
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm start
```

The application will be available at `http://localhost:3000`

## Project Structure

```
front/
├── backend/
│   ├── app.py              # Flask API with 60+ endpoints
│   ├── repository.py       # Database configuration
│   ├── requirements.txt    # Python dependencies
│   ├── core/
│   │   ├── content_parser.py    # PDF parsing logic
│   │   └── quiz_generator.py    # SOLO question generation
│   ├── models/
│   │   └── models.py       # SQLAlchemy models
│   ├── ontology/
│   │   └── seed_ontology.ttl    # Base ontology template
│   ├── services/
│   │   ├── chatbot_service.py   # RAG chatbot
│   │   ├── sparql_service.py    # SPARQL queries
│   │   ├── ontology_service.py  # OWL/Turtle export
│   │   ├── translation_service.py
│   │   └── quiz_service.py
│   ├── uploads/            # Temporary PDF uploads
│   └── lessons/            # Stored lesson PDFs
├── frontend/
│   ├── src/
│   │   ├── App.js          # Main application
│   │   ├── api.js          # API client
│   │   └── components/
│   │       ├── ChatBot.js
│   │       ├── QuizBuilder.js
│   │       ├── QuizSolver.js
│   │       ├── QuestionGenerator.js
│   │       ├── SPARQLQueryTool.js
│   │       └── ...
│   └── public/
│       └── index.html
├── raw_materials/          # Sample lesson files
├── downloaded_quizzes/     # Exported quiz files
├── ollama.ps1             # Ollama startup script
└── START_GUIDE.md         # Quick start guide
```

## API Endpoints

The backend provides 60+ REST API endpoints grouped by functionality:

### Core Endpoints
- `GET /api/health` - Health check
- `POST /api/sparql` - Execute SPARQL queries
- `GET /api/sparql/examples` - Get example SPARQL queries

### Course Management
- `GET/POST /api/courses` - List/create courses
- `GET/DELETE /api/courses/:id` - Get/delete course
- `GET/POST /api/courses/:id/lessons` - Course lessons

### Lesson Management  
- `GET/DELETE /api/lessons/:id` - Get/delete lesson
- `POST /api/lessons/:id/parse` - Parse lesson content
- `GET /api/lessons/:id/sections` - Get lesson sections

### Ontology
- `GET /api/lessons/:id/ontology` - Get ontology
- `POST /api/lessons/:id/ontology/generate` - Generate ontology
- `GET /api/lessons/:id/ontology/export/owl` - Export to OWL
- `GET /api/lessons/:id/ontology/export/turtle` - Export to Turtle

### Questions
- `POST /api/generate-questions` - Generate questions with AI
- `GET/POST /api/questions` - List/create questions
- `PUT/DELETE /api/questions/:id` - Update/delete question

### Quizzes
- `GET/POST /api/quizzes` - List/create quizzes
- `GET /api/quizzes/:id/export` - Export quiz

### Translation
- `GET /api/translate/languages` - Available languages
- `POST /api/translate/question` - Translate question
- `POST /api/translate/quiz/:id` - Translate entire quiz

### Chatbot
- `POST /api/chat` - Send message to chatbot
- `POST /api/chat/explain-answer` - Explain quiz answer

## Database Schema

The application uses SQLite with these main entities:

- **Course** - Top-level container for lessons
- **Lesson** - Individual lessons with PDF content
- **Section** - Lesson subsections
- **LearningObject** - Atomic content units for questions
- **Question** - Quiz questions with SOLO level
- **QuestionTranslation** - Translated question content
- **Quiz** - Collection of questions
- **OntologyRelationship** - Knowledge graph edges

## Usage Tips

### Generating Good Questions

1. Upload well-structured PDF materials
2. Parse the content to extract learning objects
3. Generate the ontology to build knowledge relationships
4. Generate questions - the AI uses both content and ontology
5. Review and edit generated questions as needed

### Using SPARQL Queries

The SPARQL tool lets you explore the knowledge graph:

```sparql
# Find all concepts in a lesson
SELECT ?concept WHERE {
  ?concept a :Concept .
}

# Find relationships between concepts
SELECT ?subject ?predicate ?object WHERE {
  ?subject ?predicate ?object .
}
```

### Exporting for Protégé

1. Navigate to the ontology view
2. Click "Export to OWL"
3. Open the downloaded .owl file in Protégé
4. Visualize with OntoGraf or OWLViz plugins

## Contributing

This project was developed as part of an educational software research project focused on applying SOLO taxonomy to automated question generation.

## License

This project is for educational purposes.

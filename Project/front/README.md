# SOLO Taxonomy Quiz Generator - Web Application

cd D:\GitHub\ObrazovniSoftProjekat\Project\front\backend
..\\.venv\\Scripts\\python.exe app.py

cd D:\GitHub\ObrazovniSoftProjekat\Project\front\frontend
npm start

A full-stack web application that generates educational quizzes using SOLO Taxonomy from uploaded text files. Built with React frontend and Flask backend.

## Features

- 📤 **File Upload**: Upload .txt files with educational content
- 🧠 **Smart Content Analysis**: Automatically extracts chapters and key concepts
- 📝 **SOLO Taxonomy Levels**: Generates questions at 5 different cognitive levels
  - **Prestructural**: Basic recognition
  - **Unistructural**: Single aspect focus
  - **Multistructural**: Multiple aspects listing
  - **Relational**: Integrated understanding
  - **Extended Abstract**: Real-world application
- ✅ **Multiple Choice Format**: Automatically generates options with explanations
- 💾 **Export**: Download quizzes as JSON
- 🎨 **Modern UI**: Beautiful, responsive interface

## Project Structure

```
.
├── frontend/                 # React application
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.js
│   │   │   └── QuizDisplay.js
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   └── package.json
├── backend/                  # Flask API server
│   ├── app.py
│   ├── quiz_generator.py
│   ├── requirements.txt
│   ├── uploads/             # Temporary upload folder
│   └── .env.example
└── README.md
```

## Installation

### Prerequisites

- Node.js 14+ and npm
- Python 3.8+
- OpenRouter API key (for quiz generation)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Add your OpenRouter API keys to `.env`:
```
OPENROUTER_API_KEY=your_key_here
OPENROUTER_API_KEY_2=your_key_here
...
```

6. Run the backend:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The app will open at `http://localhost:3000`

## Usage

1. **Upload Content**: Click the file upload area and select a `.txt` file
2. **Generate Quiz**: Click "Generate Quiz" button
3. **View Questions**: Browse through generated questions organized by SOLO level
4. **Download**: Export the quiz as JSON for use elsewhere

## API Endpoints

### Health Check
```
GET /api/health
```

### Generate Quiz
```
POST /api/generate-quiz
Content-Type: multipart/form-data

Body:
- file: (text file)
```

Response:
```json
{
  "metadata": {
    "filename": "string",
    "generated_at": "ISO datetime",
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
          "solo_level": "string",
          "question_data": {
            "question": "string",
            "options": ["string"],
            "correct_answer": "string",
            "explanation": "string"
          }
        }
      ]
    }
  ]
}
```

## SOLO Taxonomy Levels

### 1. Prestructural
Students demonstrate a lack of understanding or incomplete understanding. Questions test basic recognition of terms with minimal comprehension.

**Example**: "What is X?" (basic recall)

### 2. Unistructural
Students focus on one relevant aspect. Questions ask for definition or single characteristic recognition.

**Example**: "Define X" or "What does Y mean?"

### 3. Multistructural
Students address multiple independent aspects without explaining connections. Questions ask to list components or characteristics.

**Example**: "List the components of X" or "What are the characteristics of Y?"

### 4. Relational
Students integrate aspects into a coherent whole. Questions ask about relationships, comparisons, and cause-effect.

**Example**: "How does X affect Y?" or "Compare A and B"

### 5. Extended Abstract
Students generalize understanding to new situations. Questions ask for application in novel scenarios.

**Example**: "What would happen if..." or "How would you apply X in situation Y?"

## Configuration

### Backend Configuration (`.env`)

```env
# API Keys
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_API_KEY_2=sk-or-v1-...

# Server
FLASK_ENV=development
DEBUG=True
HOST=localhost
PORT=5000

# File Upload
MAX_FILE_SIZE=10485760  # 10MB in bytes
```

### Frontend Configuration

Edit `src/App.js` to change API URL:
```javascript
const API_URL = 'http://localhost:5000/api';
```

## Development

### Adding New SOLO Levels

Edit `quiz_generator.py` and update `_build_prompt()` method:
```python
prompts = {
    'your_new_level': f"""Your prompt here..."""
}
```

### Customizing Question Generation

Modify `_generate_mock_question()` in `quiz_generator.py` to change default templates.

## Troubleshooting

### API Connection Failed
- Ensure backend is running on `http://localhost:5000`
- Check CORS configuration in `app.py`

### File Upload Fails
- Maximum file size is 10MB
- Only `.txt` files are supported
- Ensure file is not corrupted

### No Questions Generated
- Check if content is long enough (minimum 50 characters per section)
- Verify API keys are valid in `.env`
- Check backend console for error messages

## Future Enhancements

- [ ] Support for PDF and Word documents
- [ ] Multi-language support
- [ ] Question difficulty customization
- [ ] Quiz templates and themes
- [ ] Student performance tracking
- [ ] Integration with learning management systems
- [ ] Database storage for quizzes
- [ ] Real-time collaboration

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

Built with ❤️ for educators and learners

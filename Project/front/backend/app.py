import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from quiz_generator import SoloQuizGenerator
from datetime import datetime
from PyPDF2 import PdfReader

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'downloaded_quizzes')
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
MAX_FILE_SIZE = 30 * 1024 * 1024  # 30MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_pdf_text(filepath):
    """Extract text from PDF file"""
    try:
        reader = PdfReader(filepath)
        text = ""
        for page_num, page in enumerate(reader.pages):
            text += f"\n--- Page {page_num + 1} ---\n"
            text += page.extract_text()
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def read_file_content(filepath, filename):
    """Read content from uploaded file (txt or pdf)"""
    try:
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        if file_extension == 'pdf':
            content = extract_pdf_text(filepath)
        else:  # txt
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        
        return content
    except Exception as e:
        raise Exception(f"Failed to read file: {str(e)}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'API is running'}), 200

@app.route('/api/generate-quiz', methods=['POST'])
def generate_quiz():
    """Generate quiz from uploaded text or PDF file"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only .txt and .pdf files are allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read file content
        try:
            content = read_file_content(filepath, filename)
        except Exception as e:
            os.remove(filepath)
            return jsonify({'error': str(e)}), 500
        
        if not content.strip():
            os.remove(filepath)
            return jsonify({'error': 'File is empty or contains no readable text'}), 400
        
        # Get config from request (if provided)
        config = request.form.get('config')
        if config:
            try:
                config = json.loads(config)
            except:
                config = None
        
        # Generate quiz
        try:
            generator = SoloQuizGenerator()
            quiz_data = generator.generate_quiz(content, filename, config)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify(quiz_data), 200
            
        except Exception as e:
            os.remove(filepath)
            print(f"Error generating quiz: {str(e)}")
            return jsonify({'error': f'Failed to generate quiz: {str(e)}'}), 500
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/generate-quiz-from-text', methods=['POST'])
def generate_quiz_from_text():
    """Generate quiz from direct text input"""
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': 'No content provided'}), 400
        
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': 'Content is empty'}), 400
        
        # Get config from request (if provided)
        config = data.get('config')
        
        # Use a default filename for text input
        filename = 'direct_text_input.txt'
        
        try:
            generator = SoloQuizGenerator()
            quiz_data = generator.generate_quiz(content, filename, config)
            return jsonify(quiz_data), 200
            
        except Exception as e:
            print(f"Error generating quiz: {str(e)}")
            return jsonify({'error': f'Failed to generate quiz: {str(e)}'}), 500
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/save-quiz', methods=['POST'])
def save_quiz():
    """Save quiz to downloaded_quizzes folder"""
    try:
        quiz_data = request.get_json()
        
        if not quiz_data:
            return jsonify({'error': 'No quiz data provided'}), 400
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = quiz_data.get('metadata', {}).get('filename', 'quiz')
        filename = f"{original_filename.replace('.txt', '')}_{timestamp}.json"
        filename = secure_filename(filename)
        
        # Save to download folder
        filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(quiz_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'Quiz saved to {filename}',
            'filename': filename
        }), 200
        
    except Exception as e:
        print(f"Error saving quiz: {str(e)}")
        return jsonify({'error': f'Failed to save quiz: {str(e)}'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File is too large (max 10MB)'}), 413

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)

"""
SOLO Quiz Generator - Backend API
Refactored for Course -> Lesson -> Section -> Learning Object structure
"""

import os
import json
import traceback
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime

# Import our modules
from repository import db, init_database
from models import LearningObject, Question, Lesson, Section, Course
from core import content_parser, SoloQuizGeneratorLocal as SoloQuizGenerator
from services import (
    LessonService, QuestionService, QuizService, gemini_service,
    generate_owl_from_relationships, generate_turtle_from_relationships
)

app = Flask(__name__)
CORS(app)

print("[STARTUP] Flask app initialized")


# ==================== CONFIGURATION ====================

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
LESSON_FOLDER = os.path.join(os.path.dirname(__file__), 'lessons')  # Permanent storage for lesson PDFs
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'downloaded_quizzes')
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 30 * 1024 * 1024  # 30MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LESSON_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['LESSON_FOLDER'] = LESSON_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize database and quiz generator
init_database()
quiz_generator = SoloQuizGenerator()

print("[STARTUP] Database initialized")
print("[STARTUP] Starting SOLO Quiz Generator API...")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Local version doesn't have API keys, just return basic status
    return jsonify({
        'status': 'ok', 
        'message': 'API is running',
        'provider': 'ollama_local',
        'ai_mode': 'Local Ollama (no API keys needed)'
    }), 200


# ==================== COURSE ENDPOINTS ====================

@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all courses"""
    try:
        courses = db.get_all_courses()
        return jsonify({'courses': courses}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/courses', methods=['POST'])
def create_course():
    """Create a new course"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Course name is required'}), 400
        
        course = db.create_course(
            name=data['name'],
            code=data.get('code'),
            description=data.get('description')
        )
        return jsonify({'course': course}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """Get a specific course with its lessons"""
    try:
        course = db.get_course(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        lessons = db.get_lessons_for_course(course_id)
        course['lessons'] = lessons
        return jsonify({'course': course}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    """Delete a course and all its lessons"""
    try:
        success = db.delete_course(course_id)
        if success:
            return jsonify({'message': 'Course deleted successfully'}), 200
        return jsonify({'error': 'Course not found'}), 404
    except Exception as e:
        print(f'[ERROR] delete_course: {str(e)}')
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== LESSON ENDPOINTS ====================

@app.route('/api/courses/<int:course_id>/lessons', methods=['GET'])
def get_lessons(course_id):
    """Get all lessons for a course"""
    try:
        lessons = db.get_lessons_for_course(course_id)
        return jsonify({'lessons': lessons}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/courses/<int:course_id>/lessons', methods=['POST'])
def upload_lesson(course_id):
    """Upload a new lesson (PDF file) to a course"""
    try:
        # Check if course exists
        course = db.get_course(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        # Check for file
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Get optional title (default to filename without extension)
        title = request.form.get('title') or file.filename.rsplit('.', 1)[0]
        filename = secure_filename(file.filename)
        
        # Extract text from PDF directly (without saving to disk)
        try:
            pdf_data = content_parser.extract_pdf_text_from_stream(file.stream)
            raw_content = pdf_data['full_text']
        except Exception as e:
            return jsonify({'error': f'Failed to extract PDF text: {str(e)}'}), 500
        
        # Create lesson in database (no file_path since we don't save PDFs)
        lesson = db.create_lesson(
            course_id=course_id,
            title=title,
            filename=filename,
            file_path=None,
            raw_content=raw_content
        )
        
        return jsonify({
            'lesson': lesson,
            'message': 'Lesson uploaded successfully. Use /parse endpoint to extract sections and learning objects.'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/lessons/<int:lesson_id>', methods=['GET'])
def get_lesson(lesson_id):
    """Get a specific lesson with its sections"""
    try:
        lesson = db.get_lesson_with_sections(lesson_id)
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        return jsonify({'lesson': lesson}), 200
    except Exception as e:
        import traceback
        print(f"[ERROR] get_lesson({lesson_id}): {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/lessons/<int:lesson_id>', methods=['DELETE'])
def delete_lesson(lesson_id):
    """Delete a lesson"""
    try:
        lesson = db.get_lesson(lesson_id)
        if lesson and lesson.get('file_path'):
            # Delete the PDF file
            if os.path.exists(lesson['file_path']):
                os.remove(lesson['file_path'])
        
        success = db.delete_lesson(lesson_id)
        if success:
            return jsonify({'message': 'Lesson deleted successfully'}), 200
        return jsonify({'error': 'Lesson not found'}), 404
    except Exception as e:
        print(f'[ERROR] delete_lesson: {str(e)}')
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/lessons/<int:lesson_id>/parse', methods=['POST'])
def parse_lesson(lesson_id):
    """Parse a lesson to extract sections and learning objects using AI"""
    try:
        lesson = db.get_lesson(lesson_id, include_content=True)
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        
        if not lesson.get('raw_content'):
            return jsonify({'error': 'Lesson has no content to parse'}), 400
        
        # Check if already parsed
        existing_sections = db.get_sections_for_lesson(lesson_id)
        if existing_sections:
            return jsonify({
                'message': 'Lesson already parsed',
                'sections': existing_sections
            }), 200
        
        # Parse the lesson content
        print(f"[API] Parsing lesson: {lesson['title']}")
        parsed_sections = content_parser.parse_lesson_structure(
            lesson['raw_content'],
            lesson['title']
        )
        
        # Save to database
        db.bulk_create_sections_and_learning_objects(lesson_id, parsed_sections)
        
        # Return the parsed structure (WITHOUT ontology extraction - that's now Step 2)
        sections = db.get_sections_for_lesson(lesson_id)
        for section in sections:
            section['learning_objects'] = db.get_learning_objects_for_section(section['id'])
        
        return jsonify({
            'message': 'Lesson parsed successfully. Sections and learning objects extracted. Use ontology/generate endpoint to create ontologies.',
            'sections': sections,
            'section_count': len(sections),
            'learning_object_count': sum(len(s.get('learning_objects', [])) for s in sections)
        }), 200
        
    except Exception as e:
        print(f"[API] Parse error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/lessons/<int:lesson_id>/parse-refactored', methods=['POST'])
def parse_lesson_refactored(lesson_id):
    """Refactored parse endpoint using the service layer"""
    try:
        result = LessonService.parse_lesson(lesson_id)
        status = result.pop('status', 200)
        
        if status != 200:
            return jsonify(result), status
        
        # Add learning objects to sections for frontend
        for section in result.get('sections', []):
            section['learning_objects'] = db.get_learning_objects_for_section(section['id'])
        
        return jsonify(result), status
    
    except Exception as e:
        print(f'[ERROR] parse_lesson_refactored: {str(e)}')
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== ONTOLOGY ENDPOINTS ====================

@app.route('/api/lessons/<int:lesson_id>/ontology', methods=['GET'])
def get_lesson_ontology(lesson_id):
    """Get the domain ontology (relationships) for a lesson"""
    try:
        relationships = db.get_relationships_for_lesson(lesson_id)
        return jsonify({'relationships': relationships}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/lessons/<int:lesson_id>/ontology/clear', methods=['POST'])
def clear_ontology(lesson_id):
    """Clear all ontology relationships for a lesson"""
    try:
        lesson = db.get_lesson(lesson_id)
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        
        # Get all relationships and delete them
        relationships = db.get_relationships_for_lesson(lesson_id)
        cleared_count = 0
        
        for rel in relationships:
            try:
                db.delete_relationship(rel['id'])
                cleared_count += 1
            except:
                pass
        
        print(f"[API] Cleared {cleared_count} ontology relationships for lesson {lesson_id}")
        
        return jsonify({
            'message': 'Ontology cleared successfully',
            'cleared_count': cleared_count
        }), 200
    except Exception as e:
        print(f"[API] Error clearing ontology: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/lessons/<int:lesson_id>/ontology/generate', methods=['POST'])
def generate_ontology(lesson_id):
    """Generate ontology relationships based on current sections and learning objects"""
    try:
        lesson = db.get_lesson(lesson_id, include_content=True)
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        
        if not lesson.get('raw_content'):
            return jsonify({'error': 'Lesson has no content to extract relationships from'}), 400
        
        # Get all learning objects for this lesson
        all_sections = db.get_sections_for_lesson(lesson_id)
        all_los = []
        lo_title_to_id = {}
        
        for s in all_sections:
            section_los = db.get_learning_objects_for_section(s['id'])
            all_los.extend(section_los)
            for lo in section_los:
                lo_title_to_id[lo['title']] = lo['id']
        
        if not all_los:
            return jsonify({
                'message': 'No learning objects to create ontology from. Parse the lesson first.',
                'regenerated_count': 0
            }), 400
        
        print(f"[API] Regenerating ontology for lesson: {lesson['title']}")
        print(f"[API] Found {len(all_los)} learning objects")
        
        # Extract ontology relationships from content
        ontology_rels = content_parser.extract_ontology_relationships(
            lesson['raw_content'],
            all_los,
            lesson['title']
        )
        
        print(f"[API] AI returned {len(ontology_rels)} potential relationships")
        
        # Clear existing relationships first
        existing_rels = db.get_relationships_for_lesson(lesson_id)
        for rel in existing_rels:
            try:
                db.delete_relationship(rel['id'])
            except:
                pass
        
        # Save new relationships
        db_rels = []
        for rel in ontology_rels:
            source_id = lo_title_to_id.get(rel['source'])
            target_id = lo_title_to_id.get(rel['target'])
            print(f"[API] Checking rel: {rel['source']} -> {rel['target']} (source_id={source_id}, target_id={target_id})")
            if source_id and target_id:
                db_rels.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'relationship_type': rel['type'],
                    'description': rel.get('description')
                })
        
        print(f"[API] Saving {len(db_rels)} relationships to database")
        if db_rels:
            db.bulk_create_relationships(db_rels)
        
        return jsonify({
            'message': 'Ontology generated successfully',
            'generated_count': len(db_rels)
        }), 200
    except Exception as e:
        print(f"[API] Error generating ontology: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/relationships/<int:rel_id>', methods=['DELETE'])
def delete_relationship(rel_id):
    """Delete a specific relationship"""
    try:
        db.delete_relationship(rel_id)
        return jsonify({'message': 'Relationship deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/lessons/<int:lesson_id>/ontology/export/owl', methods=['GET'])
def export_ontology_owl(lesson_id):
    """Export lesson ontology as OWL (RDF/XML format)"""
    try:
        lesson = db.get_lesson(lesson_id)
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        
        relationships = db.get_relationships_for_lesson(lesson_id)
        
        # Generate OWL/RDF XML
        owl_content = generate_owl_from_relationships(lesson, relationships)
        
        # Use filename if available, otherwise use title
        file_name = lesson.get('filename', lesson.get('title', f'Lesson_{lesson_id}'))
        # Remove extension if present and ensure .owl
        if file_name.endswith('.pdf'):
            file_name = file_name[:-4]
        file_name = f'ontology_{file_name}.owl'
        
        # Return as file download
        from flask import make_response
        response = make_response(owl_content)
        response.headers['Content-Type'] = 'application/rdf+xml'
        response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response, 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/lessons/<int:lesson_id>/ontology/export/turtle', methods=['GET'])
def export_ontology_turtle(lesson_id):
    """Export lesson ontology as Turtle format"""
    try:
        lesson = db.get_lesson(lesson_id)
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        
        relationships = db.get_relationships_for_lesson(lesson_id)
        
        # Generate Turtle format
        turtle_content = generate_turtle_from_relationships(lesson, relationships)
        
        # Use filename if available, otherwise use title
        file_name = lesson.get('filename', lesson.get('title', f'Lesson_{lesson_id}'))
        # Remove extension if present and ensure .ttl
        if file_name.endswith('.pdf'):
            file_name = file_name[:-4]
        file_name = f'ontology_{file_name}.ttl'
        
        # Return as file download
        from flask import make_response
        response = make_response(turtle_content)
        response.headers['Content-Type'] = 'text/turtle'
        response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response, 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== SECTION ENDPOINTS ====================

@app.route('/api/lessons/<int:lesson_id>/sections', methods=['GET'])
def get_sections(lesson_id):
    """Get all sections for a lesson"""
    try:
        sections = db.get_sections_for_lesson(lesson_id)
        return jsonify({'sections': sections}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sections/<int:section_id>', methods=['GET'])
def get_section(section_id):
    """Get a specific section with its learning objects"""
    try:
        section = db.get_section_with_learning_objects(section_id)
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        return jsonify({'section': section}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== LEARNING OBJECT ENDPOINTS ====================

@app.route('/api/sections/<int:section_id>/learning-objects', methods=['GET'])
def get_learning_objects(section_id):
    """Get all learning objects for a section"""
    try:
        learning_objects = db.get_learning_objects_for_section(section_id)
        return jsonify({'learning_objects': learning_objects}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/learning-objects/<int:lo_id>', methods=['GET'])
def get_learning_object(lo_id):
    """Get a specific learning object"""
    try:
        session = db.get_session()
        try:
            lo = session.query(LearningObject).filter(LearningObject.id == lo_id).first()
            if not lo:
                return jsonify({'error': 'Learning object not found'}), 404
            return jsonify({'learning_object': lo.to_dict()}), 200
        finally:
            session.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/learning-objects/<int:lo_id>', methods=['PUT'])
def update_learning_object(lo_id):
    """Update a learning object"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        updated_lo = db.update_learning_object(
            lo_id,
            title=data.get('title'),
            content=data.get('content'),
            object_type=data.get('object_type'),
            keywords=data.get('keywords'),
            mark_as_human_modified=True  # Mark as human-edited when updating
        )
        
        if not updated_lo:
            return jsonify({'error': 'Learning object not found'}), 404
        
        return jsonify({'learning_object': updated_lo}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/learning-objects/<int:lo_id>', methods=['DELETE'])
def delete_learning_object(lo_id):
    """Delete a learning object"""
    try:
        success = db.delete_learning_object(lo_id)
        if success:
            return jsonify({'message': 'Learning object deleted'}), 200
        return jsonify({'error': 'Learning object not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== QUESTION GENERATION ENDPOINTS ====================

@app.route('/api/generate-questions', methods=['POST'])
def generate_questions():
    """
    Generate questions from lessons based on SOLO taxonomy levels (refactored with service layer)
    
    Request body:
    {
        "lesson_ids": [1, 2],  // For extended_abstract, provide 2 lessons
        "solo_levels": ["unistructural", "multistructural", "relational", "extended_abstract"],
        "questions_per_level": 3,
        "section_ids": [1, 2, 3],  // Optional: specific sections to use
        "save_to_db": true  // Whether to save generated questions to database
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        lesson_ids = data.get('lesson_ids', [])
        solo_levels = data.get('solo_levels', ['unistructural', 'multistructural', 'relational'])
        questions_per_level = data.get('questions_per_level', 3)
        section_ids = data.get('section_ids')
        save_to_db = data.get('save_to_db', True)
        
        result = QuestionService.generate_questions(
            lesson_ids=lesson_ids,
            solo_levels=solo_levels,
            questions_per_level=questions_per_level,
            section_ids=section_ids,
            save_to_db=save_to_db
        )
        
        status = result.pop('status', 200)
        if status != 200:
            return jsonify(result), status
        
        return jsonify(result), status
    
    except Exception as e:
        print(f"[API] Question generation error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== QUESTION BANK ENDPOINTS ====================

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """Get all questions, optionally filtered by course or lesson"""
    try:
        course_id = request.args.get('course_id', type=int)
        lesson_id = request.args.get('lesson_id', type=int)
        solo_level = request.args.get('solo_level')
        
        if lesson_id:
            questions = db.get_questions_by_lesson(lesson_id)
        elif solo_level:
            questions = db.get_questions_by_solo_level(solo_level, lesson_id)
        else:
            questions = db.get_all_questions(course_id)
        
        return jsonify({'questions': questions, 'count': len(questions)}), 200
    except Exception as e:
        print(f'[ERROR] get_questions: {str(e)}')
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions', methods=['POST'])
def create_manual_question():
    """Create a manual question (human-generated, not AI)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'question_text' not in data or 'solo_level' not in data:
            return jsonify({'error': 'question_text and solo_level are required'}), 400
        
        # Create question marked as human-generated
        question = db.create_question(
            solo_level=data['solo_level'],
            question_text=data['question_text'],
            question_type=data.get('question_type', 'multiple_choice'),
            primary_lesson_id=data.get('primary_lesson_id'),
            secondary_lesson_id=data.get('secondary_lesson_id'),
            section_id=data.get('section_id'),
            learning_object_id=data.get('learning_object_id'),
            options=data.get('options'),
            correct_answer=data.get('correct_answer'),
            correct_option_index=data.get('correct_option_index'),
            explanation=data.get('explanation'),
            difficulty=data.get('difficulty'),
            bloom_level=data.get('bloom_level'),
            tags=data.get('tags'),
            is_ai_generated=False  # Mark as human-generated
        )
        
        return jsonify({'question': question}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    """Get a specific question"""
    try:
        session = db.get_session()
        try:
            q = session.query(Question).filter(Question.id == question_id).first()
            if not q:
                return jsonify({'error': 'Question not found'}), 404
            return jsonify({'question': q.to_dict()}), 200
        finally:
            session.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions/<int:question_id>', methods=['PUT'])
def update_question(question_id):
    """Update a question"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update question and mark as human-modified
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data['mark_human_modified'] = True  # Mark as human-edited
        
        updated_q = db.update_question(question_id, **update_data)
        
        if not updated_q:
            return jsonify({'error': 'Question not found'}), 404
        
        return jsonify({'question': updated_q}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """Delete a question"""
    try:
        success = db.delete_question(question_id)
        if success:
            return jsonify({'message': 'Question deleted'}), 200
        return jsonify({'error': 'Question not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== QUIZ ENDPOINTS ====================

@app.route('/api/quizzes', methods=['POST'])
def create_quiz():
    """Create a new quiz from selected questions"""
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({'error': 'Quiz title is required'}), 400
        
        quiz = db.create_quiz(
            title=data['title'],
            course_id=data.get('course_id'),
            description=data.get('description'),
            time_limit_minutes=data.get('time_limit_minutes'),
            passing_score=data.get('passing_score'),
            shuffle_questions=data.get('shuffle_questions', False),
            shuffle_options=data.get('shuffle_options', False)
        )
        
        # Add questions if provided
        question_ids = data.get('question_ids', [])
        for qid in question_ids:
            db.add_question_to_quiz(quiz['id'], qid)
        
        return jsonify({'quiz': quiz}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/quizzes/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    """Get a quiz with its questions"""
    try:
        quiz = db.get_quiz(quiz_id, include_questions=True)
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        return jsonify({'quiz': quiz}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/quizzes/<int:quiz_id>/add-questions', methods=['POST'])
def add_questions_to_quiz(quiz_id):
    """Add questions to an existing quiz"""
    try:
        data = request.get_json()
        question_ids = data.get('question_ids', [])
        
        for qid in question_ids:
            db.add_question_to_quiz(quiz_id, qid)
        
        return jsonify({'message': f'Added {len(question_ids)} questions to quiz'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/courses/<int:course_id>/quizzes', methods=['GET'])
def get_course_quizzes(course_id):
    """Get all quizzes for a course"""
    try:
        quizzes = db.get_quizzes_for_course(course_id)
        return jsonify({'quizzes': quizzes}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/quizzes/<int:quiz_id>/export', methods=['GET'])
def export_quiz(quiz_id):
    """Export quiz to JSON file"""
    try:
        quiz = db.get_quiz(quiz_id, include_questions=True)
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"quiz_{quiz['title']}_{timestamp}.json"
        filename = secure_filename(filename)
        
        # Save to download folder
        filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(quiz, f, indent=2)
        
        return jsonify({
            'message': 'Quiz exported successfully',
            'filename': filename
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== GEMINI API ENDPOINTS ====================

@app.route('/api/gemini/health', methods=['GET'])
def gemini_health_check():
    """Check if Gemini API is accessible"""
    try:
        is_connected = gemini_service.test_connection()
        return jsonify({
            'status': 'ok' if is_connected else 'unavailable',
            'connected': is_connected,
            'message': 'Gemini API is accessible' if is_connected else 'Gemini API quota exceeded or unavailable'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'connected': False,
            'error': str(e)
        }), 500


@app.route('/api/gemini/generate-quiz', methods=['POST'])
def generate_quiz_with_gemini():
    """
    Generate quiz questions using Gemini API
    
    Request body:
    {
        "content": "The educational content",
        "num_questions": 10,
        "question_type": "multiple_choice"  # or "true_false", "short_answer"
    }
    """
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Content is required'}), 400
        
        content = data['content']
        num_questions = data.get('num_questions', 10)
        question_type = data.get('question_type', 'multiple_choice')
        
        # Generate quiz using Gemini
        result = gemini_service.generate_quiz_from_content(
            content=content,
            num_questions=num_questions,
            question_type=question_type
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'questions': result['questions'],
                'count': len(result['questions'])
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    except Exception as e:
        print(f'[ERROR] generate_quiz_with_gemini: {str(e)}')
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/gemini/generate-summary', methods=['POST'])
def generate_summary():
    """
    Generate a learning summary from content using Gemini API
    
    Request body:
    {
        "content": "The educational content to summarize"
    }
    """
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Content is required'}), 400
        
        content = data['content']
        
        result = gemini_service.generate_learning_summary(content)
        
        if result['success']:
            return jsonify({
                'success': True,
                'summary': result['summary']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    except Exception as e:
        print(f'[ERROR] generate_summary: {str(e)}')
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/gemini/generate-objectives', methods=['POST'])
def generate_objectives():
    """
    Generate learning objectives for a lesson using Gemini API
    
    Request body:
    {
        "lesson_title": "Title of the lesson",
        "content": "The lesson content"
    }
    """
    try:
        data = request.get_json()
        if not data or 'lesson_title' not in data or 'content' not in data:
            return jsonify({'error': 'Lesson title and content are required'}), 400
        
        lesson_title = data['lesson_title']
        content = data['content']
        
        result = gemini_service.generate_lesson_objectives(lesson_title, content)
        
        if result['success']:
            return jsonify({
                'success': True,
                'objectives': result['objectives']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    except Exception as e:
        print(f'[ERROR] generate_objectives: {str(e)}')
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/gemini/explain-answer', methods=['POST'])
def explain_answer():
    """
    Generate a detailed explanation for a quiz answer using Gemini API
    
    Request body:
    {
        "question": "The quiz question",
        "correct_answer": "The correct answer"
    }
    """
    try:
        data = request.get_json()
        if not data or 'question' not in data or 'correct_answer' not in data:
            return jsonify({'error': 'Question and correct answer are required'}), 400
        
        question = data['question']
        correct_answer = data['correct_answer']
        
        explanation = gemini_service.generate_quiz_explanation(question, correct_answer)
        
        return jsonify({
            'success': True,
            'explanation': explanation
        }), 200
    except Exception as e:
        print(f'[ERROR] explain_answer: {str(e)}')
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== ERROR HANDLERS ====================

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File is too large (max 30MB)'}), 413


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("[STARTUP] Starting SOLO Quiz Generator API...")
    print("[STARTUP] Database initialized")
    app.run(debug=True, host='localhost', port=5000)

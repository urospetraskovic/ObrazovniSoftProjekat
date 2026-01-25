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
from models import LearningObject, Question, Lesson, Section, Course, Session
from core import content_parser, SoloQuizGeneratorLocal as SoloQuizGenerator
from services import (
    LessonService, QuestionService, QuizService,
    generate_owl_from_relationships, generate_turtle_from_relationships,
    ontology_manager
)
from services.sparql_service import sparql_service
from services.chatbot_service import chatbot_service

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
sparql_service.load_ontology()  # Load ontology for SPARQL queries
chatbot_session = Session()  # Create session for chatbot
chatbot_service.set_db_session(chatbot_session)  # Set database session for chatbot

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


# ==================== SPARQL ENDPOINTS ====================

@app.route('/api/sparql', methods=['POST'])
def sparql_query():
    """Execute SPARQL queries on the ontology"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'No SPARQL query provided'}), 400
        
        query = data.get('query').strip()
        result = sparql_service.execute_query(query)
        
        if 'error' in result and result['error']:
            status_code = 408 if 'timeout' in result['error'].lower() else 400
            return jsonify(result), status_code
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Query error: {str(e)}'}), 400



@app.route('/api/sparql/examples', methods=['GET'])
def get_sparql_examples():
    """Get example SPARQL queries"""
    examples = sparql_service.get_examples()
    return jsonify(examples), 200


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


# ==================== KNOWLEDGE BASE ONTOLOGY ENDPOINTS ====================
# These endpoints use the OntologyManager which merges the seed ontology (TBox)
# with the database content (ABox) to produce a complete populated ontology.

@app.route('/api/ontology/stats', methods=['GET'])
def get_ontology_stats():
    """Get statistics about the knowledge base ontology"""
    try:
        stats = ontology_manager.get_ontology_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ontology/export', methods=['GET'])
def export_full_ontology():
    """
    Export the complete knowledge base ontology (seed + all database content).
    
    Query params:
        course_id: Optional - limit to a specific course
        format: Optional - 'owl' (default) or 'download'
    """
    try:
        course_id = request.args.get('course_id', type=int)
        format_type = request.args.get('format', 'owl')
        
        owl_content = ontology_manager.export_full_ontology(course_id=course_id)
        
        if format_type == 'download':
            response = make_response(owl_content)
            response.headers['Content-Type'] = 'application/rdf+xml'
            filename = f'knowledge_base_course_{course_id}.owl' if course_id else 'knowledge_base_full.owl'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response, 200
        else:
            return jsonify({
                'ontology': owl_content,
                'stats': ontology_manager.get_ontology_stats()
            }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ontology/export/course/<int:course_id>', methods=['GET'])
def export_course_ontology(course_id):
    """Export ontology for a specific course"""
    try:
        owl_content = ontology_manager.export_full_ontology(course_id=course_id)
        
        response = make_response(owl_content)
        response.headers['Content-Type'] = 'application/rdf+xml'
        response.headers['Content-Disposition'] = f'attachment; filename="knowledge_base_course_{course_id}.owl"'
        return response, 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ontology/export/lesson/<int:lesson_id>', methods=['GET'])
def export_lesson_knowledge_ontology(lesson_id):
    """
    Export ontology for a specific lesson using the new OntologyManager.
    This produces a complete ontology that imports the seed and adds lesson-specific individuals.
    """
    try:
        owl_content = ontology_manager.export_lesson_ontology(lesson_id=lesson_id)
        
        response = make_response(owl_content)
        response.headers['Content-Type'] = 'application/rdf+xml'
        response.headers['Content-Disposition'] = f'attachment; filename="knowledge_base_lesson_{lesson_id}.owl"'
        return response, 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ontology/save', methods=['POST'])
def save_ontology_to_file():
    """
    Save the knowledge base ontology to a file on the server.
    This can be used for backup or for Protégé to load directly.
    """
    try:
        course_id = request.json.get('course_id') if request.json else None
        file_path = ontology_manager.save_knowledge_base(course_id=course_id)
        
        return jsonify({
            'message': 'Knowledge base saved successfully',
            'file_path': file_path,
            'stats': ontology_manager.get_ontology_stats()
        }), 200
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


# ==================== TRANSLATION ENDPOINTS ====================

@app.route('/api/translations/languages', methods=['GET'])
def get_supported_languages():
    """Get list of supported languages for translation"""
    try:
        from services.translation_service import get_translation_service
        service = get_translation_service()
        return jsonify({
            'languages': [
                {'code': code, 'name': name}
                for code, name in service.supported_languages.items()
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions/<int:question_id>/translate', methods=['POST'])
def translate_question(question_id):
    """Translate a question to target language"""
    try:
        data = request.get_json()
        if not data or 'language_code' not in data:
            return jsonify({'error': 'language_code is required'}), 400
        
        language_code = data['language_code']
        
        # Get question
        session = db.Session()
        question = session.query(db.Question).filter(db.Question.id == question_id).first()
        
        if not question:
            session.close()
            return jsonify({'error': 'Question not found'}), 404
        
        # Translate question
        from services.translation_service import get_translation_service
        service = get_translation_service()
        translation = service.translate_question(question, language_code, session)
        
        session.close()
        
        if not translation:
            return jsonify({'error': 'Translation failed'}), 500
        
        return jsonify({
            'message': 'Question translated successfully',
            'translation': translation.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions/<int:question_id>/translations', methods=['GET'])
def get_question_translations(question_id):
    """Get all available translations for a question"""
    try:
        session = db.Session()
        question = session.query(db.Question).filter(db.Question.id == question_id).first()
        
        if not question:
            session.close()
            return jsonify({'error': 'Question not found'}), 404
        
        from services.translation_service import get_translation_service
        service = get_translation_service()
        translations = service.get_translations(question_id, session)
        
        session.close()
        
        return jsonify({
            'question_id': question_id,
            'original_language': 'English',
            'available_translations': [t.to_dict() for t in translations]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions/<int:question_id>/translations/<language_code>', methods=['GET'])
def get_translated_question(question_id, language_code):
    """Get translated version of a question"""
    try:
        session = db.Session()
        
        from services.translation_service import get_translation_service
        service = get_translation_service()
        translated = service.get_translated_question(question_id, language_code, session)
        
        session.close()
        
        if not translated:
            return jsonify({'error': 'Translation not found'}), 404
        
        return jsonify(translated), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions/batch/translate', methods=['POST'])
def batch_translate_questions():
    """Translate multiple questions to multiple languages"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        question_ids = data.get('question_ids', [])
        target_languages = data.get('target_languages', [])
        
        if not question_ids or not target_languages:
            return jsonify({'error': 'question_ids and target_languages are required'}), 400
        
        session = db.Session()
        
        from services.translation_service import get_translation_service
        service = get_translation_service()
        results = service.translate_batch(question_ids, target_languages, session)
        
        session.close()
        
        return jsonify({
            'message': 'Batch translation completed',
            'results': results
        }), 200
        
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
        
        # Fetch the quiz again to get the updated question count
        updated_quiz = db.get_quiz(quiz['id'], include_questions=False)
        
        return jsonify({'quiz': updated_quiz}), 201
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


@app.route('/api/quizzes/<int:quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    """Delete a quiz"""
    try:
        success = db.delete_quiz(quiz_id)
        if not success:
            return jsonify({'error': 'Quiz not found'}), 404
        return jsonify({'message': 'Quiz deleted successfully'}), 200
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
    """Get all quizzes for a course with available translation languages"""
    try:
        from models.models import Quiz, QuizQuestion, QuestionTranslation
        from sqlalchemy import func
        
        session = db.Session()
        quizzes = session.query(Quiz).filter(Quiz.course_id == course_id).all()
        
        result = []
        for quiz in quizzes:
            quiz_dict = quiz.to_dict()
            
            # Get available languages for this quiz
            quiz_questions = session.query(QuizQuestion).filter_by(quiz_id=quiz.id).all()
            question_ids = [qq.question_id for qq in quiz_questions]
            total_questions = len(question_ids)
            
            if question_ids and total_questions > 0:
                # Only include languages where ALL questions have translations
                # Group by language and count, only keep languages with count == total questions
                lang_counts = session.query(
                    QuestionTranslation.language_code,
                    func.count(QuestionTranslation.question_id)
                ).filter(
                    QuestionTranslation.question_id.in_(question_ids)
                ).group_by(QuestionTranslation.language_code).all()
                
                # Only include languages where translation count matches total questions
                quiz_dict['available_languages'] = [
                    lang for lang, count in lang_counts if count == total_questions
                ]
            else:
                quiz_dict['available_languages'] = []
            
            result.append(quiz_dict)
        
        session.close()
        return jsonify({'quizzes': result}), 200
    except Exception as e:
        print(f'[ERROR] get_course_quizzes: {str(e)}')
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/quizzes', methods=['GET'])
def get_all_quizzes():
    """Get all quizzes with available translation languages"""
    try:
        from models.models import Quiz, QuizQuestion, Question, QuestionTranslation
        from sqlalchemy import func
        
        session = db.Session()
        quizzes = session.query(Quiz).all()
        
        result = []
        for quiz in quizzes:
            quiz_dict = quiz.to_dict()
            
            # Get available languages for this quiz
            quiz_questions = session.query(QuizQuestion).filter_by(quiz_id=quiz.id).all()
            question_ids = [qq.question_id for qq in quiz_questions]
            total_questions = len(question_ids)
            
            if question_ids and total_questions > 0:
                # Only include languages where ALL questions have translations
                lang_counts = session.query(
                    QuestionTranslation.language_code,
                    func.count(QuestionTranslation.question_id)
                ).filter(
                    QuestionTranslation.question_id.in_(question_ids)
                ).group_by(QuestionTranslation.language_code).all()
                
                # Only include languages where translation count matches total questions
                quiz_dict['available_languages'] = [
                    lang for lang, count in lang_counts if count == total_questions
                ]
            else:
                quiz_dict['available_languages'] = []
            
            result.append(quiz_dict)
        
        session.close()
        return jsonify({'quizzes': result}), 200
    except Exception as e:
        print(f'[ERROR] get_all_quizzes: {str(e)}')
        traceback.print_exc()
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



# ==================== TRANSLATION ENDPOINTS ====================

from services import get_translation_service
from models import Lesson, Section, LearningObject, ConceptRelationship

translation_service = get_translation_service()

@app.route('/api/translate/languages', methods=['GET'])
def get_languages():
    """Get list of supported languages for translation"""
    try:
        languages = translation_service.get_supported_languages()
        return jsonify({
            'success': True,
            'languages': languages
        }), 200
    except Exception as e:
        print(f'[ERROR] get_languages: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate/question', methods=['POST'])
def translate_question_api():
    """Translate a single question to target language"""
    try:
        data = request.get_json()
        if not data or 'question_id' not in data or 'target_language' not in data:
            return jsonify({'error': 'question_id and target_language are required'}), 400
        
        question_id = data['question_id']
        target_language = data['target_language']
        
        session = db.Session()
        question = session.get(Question, question_id)
        
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        translation = translation_service.translate_question(question, target_language, session)
        
        if translation:
            return jsonify({
                'success': True,
                'translation': translation.to_dict()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Translation failed'
            }), 500
    except Exception as e:
        print(f'[ERROR] translate_question_api: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate/lesson', methods=['POST'])
def translate_lesson_api():
    """Translate a lesson to target language"""
    try:
        data = request.get_json()
        if not data or 'lesson_id' not in data or 'target_language' not in data:
            return jsonify({'error': 'lesson_id and target_language are required'}), 400
        
        lesson_id = data['lesson_id']
        target_language = data['target_language']
        
        session = db.Session()
        lesson = session.get(Lesson, lesson_id)
        
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        
        translation = translation_service.translate_lesson(lesson, target_language, session)
        
        if translation:
            return jsonify({
                'success': True,
                'translation': translation.to_dict()
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Translation failed'}), 500
    except Exception as e:
        print(f'[ERROR] translate_lesson_api: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate/section', methods=['POST'])
def translate_section_api():
    """Translate a section to target language"""
    try:
        data = request.get_json()
        if not data or 'section_id' not in data or 'target_language' not in data:
            return jsonify({'error': 'section_id and target_language are required'}), 400
        
        section_id = data['section_id']
        target_language = data['target_language']
        
        session = db.Session()
        section = session.get(Section, section_id)
        
        if not section:
            return jsonify({'error': 'Section not found'}), 404
        
        translation = translation_service.translate_section(section, target_language, session)
        
        if translation:
            return jsonify({
                'success': True,
                'translation': translation.to_dict()
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Translation failed'}), 500
    except Exception as e:
        print(f'[ERROR] translate_section_api: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate/learning-object', methods=['POST'])
def translate_learning_object_api():
    """Translate a learning object to target language"""
    try:
        data = request.get_json()
        if not data or 'learning_object_id' not in data or 'target_language' not in data:
            return jsonify({'error': 'learning_object_id and target_language are required'}), 400
        
        lo_id = data['learning_object_id']
        target_language = data['target_language']
        
        session = db.Session()
        learning_object = session.get(LearningObject, lo_id)
        
        if not learning_object:
            return jsonify({'error': 'Learning object not found'}), 404
        
        translation = translation_service.translate_learning_object(learning_object, target_language, session)
        
        if translation:
            return jsonify({
                'success': True,
                'translation': translation.to_dict()
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Translation failed'}), 500
    except Exception as e:
        print(f'[ERROR] translate_learning_object_api: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate/ontology', methods=['POST'])
def translate_ontology_api():
    """Translate an ontology relationship to target language"""
    try:
        data = request.get_json()
        if not data or 'relationship_id' not in data or 'target_language' not in data:
            return jsonify({'error': 'relationship_id and target_language are required'}), 400
        
        rel_id = data['relationship_id']
        target_language = data['target_language']
        
        session = db.Session()
        relationship = session.get(ConceptRelationship, rel_id)
        
        if not relationship:
            return jsonify({'error': 'Relationship not found'}), 404
        
        translation = translation_service.translate_ontology_relationship(relationship, target_language, session)
        
        if translation:
            return jsonify({
                'success': True,
                'translation': translation.to_dict()
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Translation failed'}), 500
    except Exception as e:
        print(f'[ERROR] translate_ontology_api: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate/quiz/<int:quiz_id>', methods=['POST'])
def translate_quiz_api(quiz_id):
    """Translate all questions in a quiz to target language"""
    try:
        from models.models import Quiz, QuizQuestion, Question
        
        data = request.get_json()
        if not data or 'target_language' not in data:
            return jsonify({'error': 'target_language is required'}), 400
        
        target_language = data['target_language']
        
        session = db.Session()
        quiz = session.get(Quiz, quiz_id)
        
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        # Get all questions in this quiz
        quiz_questions = session.query(QuizQuestion).filter_by(quiz_id=quiz_id).all()
        question_ids = [qq.question_id for qq in quiz_questions]
        questions = session.query(Question).filter(Question.id.in_(question_ids)).all()
        
        translated_count = 0
        for question in questions:
            translation = translation_service.translate_question(question, target_language, session)
            if translation:
                translated_count += 1
        
        return jsonify({
            'success': True,
            'quiz_id': quiz_id,
            'quiz_title': quiz.title,
            'questions_translated': translated_count,
            'total_questions': len(questions),
            'target_language': target_language
        }), 200
    except Exception as e:
        print(f'[ERROR] translate_quiz_api: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate/quiz/<int:quiz_id>/status', methods=['GET'])
def get_quiz_translation_status(quiz_id):
    """Get detailed translation status for a quiz - which questions are translated for each language"""
    try:
        from models.models import Quiz, QuizQuestion, Question, QuestionTranslation
        from services.translation_service import SUPPORTED_LANGUAGES
        
        session = db.Session()
        quiz = session.get(Quiz, quiz_id)
        
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        # Get all questions in this quiz
        quiz_questions = session.query(QuizQuestion).filter_by(quiz_id=quiz_id).all()
        question_ids = [qq.question_id for qq in quiz_questions]
        questions = session.query(Question).filter(Question.id.in_(question_ids)).all()
        
        # Get all translations for these questions
        translations = session.query(QuestionTranslation).filter(
            QuestionTranslation.question_id.in_(question_ids)
        ).all()
        
        # Build a map of question_id -> set of translated language codes
        translation_map = {}
        for t in translations:
            if t.question_id not in translation_map:
                translation_map[t.question_id] = set()
            translation_map[t.question_id].add(t.language_code)
        
        # Build detailed status for each language
        language_status = {}
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            translated_count = 0
            missing_questions = []
            
            for q in questions:
                if q.id in translation_map and lang_code in translation_map[q.id]:
                    translated_count += 1
                else:
                    q_data = {
                        'id': q.id,
                        'question_text': q.question_text[:80] + '...' if len(q.question_text) > 80 else q.question_text,
                        'solo_level': q.solo_level
                    }
                    missing_questions.append(q_data)
            
            language_status[lang_code] = {
                'language_name': lang_name,
                'total_questions': len(questions),
                'translated_count': translated_count,
                'missing_count': len(missing_questions),
                'is_complete': len(missing_questions) == 0,
                'missing_questions': missing_questions
            }
        
        session.close()
        
        return jsonify({
            'success': True,
            'quiz_id': quiz_id,
            'quiz_title': quiz.title,
            'total_questions': len(questions),
            'language_status': language_status
        }), 200
        
    except Exception as e:
        print(f'[ERROR] get_quiz_translation_status: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate/quiz/<int:quiz_id>/fix', methods=['POST'])
def fix_quiz_translations(quiz_id):
    """Delete bad translations (identical to original) for a quiz so they can be re-translated"""
    try:
        from models.models import Quiz, QuizQuestion, Question, QuestionTranslation
        
        data = request.get_json() or {}
        target_language = data.get('target_language')
        
        session = db.Session()
        
        # Get all questions in this quiz
        quiz_questions = session.query(QuizQuestion).filter_by(quiz_id=quiz_id).all()
        question_ids = [qq.question_id for qq in quiz_questions]
        questions = session.query(Question).filter(Question.id.in_(question_ids)).all()
        
        # Build a map of question_id -> original question text
        question_map = {q.id: q.question_text.strip().lower() for q in questions}
        
        # Find and delete bad translations
        query = session.query(QuestionTranslation).filter(
            QuestionTranslation.question_id.in_(question_ids)
        )
        if target_language:
            query = query.filter(QuestionTranslation.language_code == target_language)
        
        translations = query.all()
        deleted_count = 0
        
        for t in translations:
            original = question_map.get(t.question_id, '')
            translated = t.translated_question_text.strip().lower() if t.translated_question_text else ''
            
            # Delete if translation is identical or very similar to original
            if translated == original or translated.startswith(original[:50]):
                session.delete(t)
                deleted_count += 1
                print(f"[FIX] Deleted bad translation for question {t.question_id} ({t.language_code})")
        
        session.commit()
        session.close()
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} bad translations. You can now re-translate.'
        }), 200
        
    except Exception as e:
        print(f'[ERROR] fix_quiz_translations: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate/question/<int:question_id>/retranslate', methods=['POST'])
def retranslate_question(question_id):
    """Delete existing translation for a question and retranslate it"""
    try:
        from models.models import Question, QuestionTranslation
        
        data = request.get_json() or {}
        target_language = data.get('target_language')
        
        if not target_language:
            return jsonify({'error': 'target_language is required'}), 400
        
        session = db.Session()
        question = session.get(Question, question_id)
        
        if not question:
            session.close()
            return jsonify({'error': 'Question not found'}), 404
        
        # Delete existing translation for this language
        existing = session.query(QuestionTranslation).filter(
            QuestionTranslation.question_id == question_id,
            QuestionTranslation.language_code == target_language
        ).first()
        
        if existing:
            session.delete(existing)
            session.commit()
            print(f"[RETRANSLATE] Deleted old {target_language} translation for question {question_id}")
        
        # Now translate again
        result = translation_service.translate_question(question, target_language, session)
        session.close()
        
        if result:
            return jsonify({
                'success': True,
                'message': f'Question {question_id} retranslated to {target_language}',
                'translated_text': result.translated_question_text
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Translation failed after multiple attempts'
            }), 500
        
    except Exception as e:
        print(f'[ERROR] retranslate_question: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate/course/<int:course_id>', methods=['POST'])
def translate_course_api(course_id):
    """Translate all content in a course to target language"""
    try:
        data = request.get_json()
        if not data or 'target_language' not in data:
            return jsonify({'error': 'target_language is required'}), 400
        
        target_language = data['target_language']
        
        session = db.Session()
        course = session.get(Course, course_id)
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        lesson_ids = [lesson.id for lesson in course.lessons]
        stats = translation_service.translate_course_content(lesson_ids, target_language, session)
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        print(f'[ERROR] translate_course_api: {str(e)}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ERROR HANDLERS ====================

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File is too large (max 30MB)'}), 413


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ==================== CHATBOT ENDPOINTS ====================

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Learning Assistant chatbot endpoint
    
    Request body:
    {
        "message": "User's question",
        "course_id": optional,
        "lesson_id": optional,
        "conversation_history": optional list of messages
    }
    """
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        course_context = None
        lesson_context = None
        
        # Get course context if provided
        course_id = data.get('course_id')
        if course_id:
            try:
                course = db.session.query(Course).filter_by(id=course_id).first()
                if course:
                    course_context = f"{course.name}: {course.description}"
            except:
                pass
        
        # Get lesson context if provided
        lesson_id = data.get('lesson_id')
        if lesson_id:
            try:
                lesson = db.session.query(Lesson).filter_by(id=lesson_id).first()
                if lesson:
                    lesson_context = f"Lesson: {lesson.title}\n{lesson.description}"
                    # Get lesson sections for more context
                    sections = db.session.query(Section).filter_by(lesson_id=lesson_id).all()
                    if sections:
                        for section in sections[:3]:  # Limit to first 3 sections
                            lesson_context += f"\n\nSection: {section.title}"
                            if section.content:
                                lesson_context += f"\n{section.content[:500]}"
            except:
                pass
        
        # Get conversation history if provided
        conversation_history = data.get('conversation_history')
        
        # Generate response
        result = chatbot_service.generate_response(
            user_message=user_message,
            course_context=course_context,
            lesson_context=lesson_context,
            conversation_history=conversation_history,
            course_id=course_id
        )
        
        return jsonify(result), 200
    except Exception as e:
        print(f"[Chat Error] {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Chat error: {str(e)}'}), 500


@app.route('/api/chat/explain-answer', methods=['POST'])
def chat_explain_answer():
    """
    Generate explanation for quiz answer
    
    Request body:
    {
        "question": "Quiz question text",
        "correct_answer": "The correct answer",
        "user_answer": optional "User's incorrect answer"
    }
    """
    try:
        data = request.get_json()
        if not data or 'question' not in data or 'correct_answer' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = chatbot_service.generate_quiz_explanation(
            question=data.get('question'),
            correct_answer=data.get('correct_answer'),
            user_answer=data.get('user_answer')
        )
        
        return jsonify(result), 200
    except Exception as e:
        print(f"[Explain Answer Error] {str(e)}")
        return jsonify({'error': f'Error: {str(e)}'}), 500


if __name__ == '__main__':
    print("[STARTUP] Starting SOLO Quiz Generator API...")
    print("[STARTUP] Database initialized")
    app.run(debug=True, host='localhost', port=5000)

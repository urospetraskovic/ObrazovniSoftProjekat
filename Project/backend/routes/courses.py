"""Course CRUD routes."""

import traceback

from flask import Blueprint, request, jsonify

from repository import db

courses_bp = Blueprint('courses', __name__, url_prefix='/api/courses')


@courses_bp.route('', methods=['GET'])
def get_courses():
    """Get all courses."""
    try:
        courses = db.get_all_courses()
        return jsonify({'courses': courses}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@courses_bp.route('', methods=['POST'])
def create_course():
    """Create a new course."""
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


@courses_bp.route('/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """Get a specific course with its lessons."""
    try:
        course = db.get_course(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        lessons = db.get_lessons_for_course(course_id)
        course['lessons'] = lessons
        return jsonify({'course': course}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@courses_bp.route('/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    """Delete a course and all its lessons."""
    try:
        success = db.delete_course(course_id)
        if success:
            return jsonify({'message': 'Course deleted successfully'}), 200
        return jsonify({'error': 'Course not found'}), 404
    except Exception as e:
        print(f'[ERROR] delete_course: {str(e)}')
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

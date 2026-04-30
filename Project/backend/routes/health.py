"""Health check routes."""

from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'API is running',
        'provider': 'ollama_local',
        'ai_mode': 'Local Ollama (no API keys needed)'
    }), 200

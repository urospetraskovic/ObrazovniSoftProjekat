"""Global Flask error handlers."""

from flask import jsonify


def register_error_handlers(app):
    """Attach common error handlers to the Flask app."""

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File is too large (max 30MB)'}), 413

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

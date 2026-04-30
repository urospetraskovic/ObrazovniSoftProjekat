"""
SOLO Quiz Generator - Backend API entry point.

Builds the Flask app, wires up shared services, and registers all blueprints.
Routes are defined under the `routes/` package, business logic under `services/`.
"""

from flask import Flask
from flask_cors import CORS

import config
from repository import init_database
from models import Session
from core import SoloQuizGeneratorLocal as SoloQuizGenerator
from services.sparql_service import sparql_service
from services.chatbot_service import chatbot_service
from routes import register_routes


def _bootstrap_services():
    """Initialise shared singletons (DB, SPARQL ontology, chatbot session)."""
    init_database()
    print("[STARTUP] Database initialized")

    # Instantiated for its side effects / so the service is loaded at startup,
    # in line with the historical app.py behaviour.
    SoloQuizGenerator()

    sparql_service.load_ontology()
    chatbot_service.set_db_session(Session())


def create_app():
    """Application factory."""
    app = Flask(__name__)
    CORS(app)

    config.ensure_folders()
    config.apply_to(app)

    print("[STARTUP] Flask app initialized")

    _bootstrap_services()
    register_routes(app)

    print("[STARTUP] Starting SOLO Quiz Generator API...")
    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)

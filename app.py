"""Moriah — Flask application entry point."""
import logging
import os
import re

from flask import Flask

from db.database import init_db
from routes.home import home_bp
from routes.session import session_bp
from routes.dashboard import dashboard_bp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'moriah-dev-key')

    app.register_blueprint(home_bp)
    app.register_blueprint(session_bp, url_prefix='/session')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    @app.template_filter('strip_letter')
    def strip_letter_prefix(text):
        """Remove leading letter prefix like 'A) ' or 'B. ' from MCQ options."""
        return re.sub(r'^[A-Da-d][).\s]+\s*', '', str(text))

    with app.app_context():
        init_db()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5002)

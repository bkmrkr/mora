"""Mora v2 — Flask application entry point."""
import logging
import logging.handlers
import os
import re
import traceback
import argparse

from flask import Flask, render_template, request as flask_request, Response

from db.database import init_db
from routes.home import home_bp
from routes.session import session_bp
from routes.dashboard import dashboard_bp

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mora_debug.log')

file_handler = logging.handlers.TimedRotatingFileHandler(
    LOG_FILE, when='midnight', backupCount=3, encoding='utf-8',
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(), file_handler],
)


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'mora-dev-key')

    app.register_blueprint(home_bp)
    app.register_blueprint(session_bp, url_prefix='/session')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    @app.template_filter('strip_letter')
    def strip_letter_prefix(text):
        return re.sub(r'^[A-Da-d][.)]\s*', '', str(text))

    @app.route('/favicon.ico')
    def favicon():
        return Response(status=204)

    req_logger = logging.getLogger('mora.requests')

    @app.before_request
    def log_request():
        form_data = dict(flask_request.form) if flask_request.form else {}
        req_logger.info('>>> %s %s  form=%s', flask_request.method,
                        flask_request.full_path.rstrip('?'), form_data)

    @app.after_request
    def log_response(response):
        req_logger.info('<<< %s %s  status=%d  location=%s',
                        flask_request.method,
                        flask_request.full_path.rstrip('?'),
                        response.status_code,
                        response.headers.get('Location', '-'))
        return response

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "script-src 'self'"
        )
        return response

    @app.errorhandler(Exception)
    def log_error(error):
        from werkzeug.exceptions import HTTPException
        req_logger.error('!!! %s %s  EXCEPTION:\n%s',
                         flask_request.method,
                         flask_request.full_path.rstrip('?'),
                         traceback.format_exc())
        if isinstance(error, HTTPException):
            return render_template('error.html',
                                   error_code=error.code,
                                   error_message=error.description), error.code
        return render_template('error.html',
                               error_code=500,
                               error_message='Internal Server Error'), 500

    with app.app_context():
        init_db()

    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, nargs='?', default=5002)
    args = parser.parse_args()
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=args.port, threaded=True)

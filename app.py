import logging
from flask import Flask
from flask_cors import CORS

from config import Config
from db import init_db
from routes.auth import auth_bp
from routes.journal import journal_bp
from utils.response import error_response

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for all API endpoints (supports React frontend)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(journal_bp)

    # Health Check Endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return {
            "status": "healthy",
            "message": "Journal App Backend API is up and running!"
        }, 200

    # Global JSON Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        return error_response(getattr(e, "description", "Bad request payload!"), 400)

    @app.errorhandler(404)
    def not_found(e):
        return error_response("Requested API endpoint not found!", 404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error_response("HTTP method not allowed for this endpoint!", 405)

    @app.errorhandler(415)
    def unsupported_media_type(e):
        return error_response("Unsupported Media Type! Please send 'application/json' content.", 415)

    @app.errorhandler(500)
    def server_error(e):
        return error_response("Internal server error. Please try again later.", 500)

    # Initialize Database Connection and Indexes
    with app.app_context():
        init_db()

    return app

app = create_app()

if __name__ == "__main__":
    print(f"Starting Journal App Flask Backend Server on port {Config.PORT}...")
    app.run(host="0.0.0.0", port=Config.PORT, debug=True)

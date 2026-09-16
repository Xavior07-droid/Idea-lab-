import os
from flask import Flask, redirect, url_for
from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Make sure the folders SQLite/uploads need actually exist.
    os.makedirs(os.path.join(app.root_path, "database"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    # Import models so SQLAlchemy knows about every table before create_all().
    from models import User, AuditLog, Asset, Nominee  # noqa: F401

    # Register blueprints.
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.assets import assets_bp
    from routes.nominees import nominees_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(nominees_bp)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    # Friendly error pages instead of stack traces.
    @app.errorhandler(404)
    def not_found(e):
        return "Page not found.", 404

    @app.errorhandler(403)
    def forbidden(e):
        return "You are not authorized to access this resource.", 403

    @app.errorhandler(500)
    def server_error(e):
        return "Something went wrong. Please try again later.", 500

    return app


app = create_app()

if __name__ == "__main__":
    # Debug mode is fine for local student development, but must be off
    # (and a production WSGI server used) in any real deployment.
    app.run(debug=True)

import os
from flask import Flask, session
from flask_wtf.csrf import CSRFProtect

from config import Config
from .extensions import bcrypt, db, login_manager, mail, migrate

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    register_blueprints(app)

    @app.before_request
    def set_session_timeout():
        session.permanent = True

    @app.context_processor
    def inject_role_names():
        return {"ROLE_ADMIN": "admin", "ROLE_TEACHER": "teacher", "ROLE_STUDENT": "student"}

    os.makedirs(os.path.join(app.root_path, "uploads"), exist_ok=True)

    return app


def register_blueprints(app):
    from .blueprints.auth.routes import auth_bp
    from .blueprints.main.routes import main_bp
    from .blueprints.admin.routes import admin_bp
    from .blueprints.teacher.routes import teacher_bp
    from .blueprints.student.routes import student_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
    app.register_blueprint(student_bp, url_prefix="/student")

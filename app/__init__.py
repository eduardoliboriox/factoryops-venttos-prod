from flask import Flask
from datetime import datetime
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Config
from app.extensions import login_manager

from app.routes.pages import bp as pages_bp
from app.routes.api import bp as api_bp
from app.auth.routes import bp as auth_bp
from app.auth.models import User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_port=1,
        x_prefix=1
    )

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY não configurada")

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = ""

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    @app.context_processor
    def inject_globals():
        return {
            "now": datetime.utcnow,
            "ENVIRONMENT": app.config.get("ENVIRONMENT", "production"),

            "APP_NAME": app.config.get("APP_NAME", "FactoryOps"),
            "APP_SHORT_NAME": app.config.get("APP_SHORT_NAME", "FactoryOps"),
            "APP_DESCRIPTION": app.config.get("APP_DESCRIPTION", ""),
            "APP_THEME_COLOR": app.config.get("APP_THEME_COLOR", "#0f172a"),
            "APP_LANG": app.config.get("APP_LANG", "pt-BR"),
            "APP_VERSION": app.config.get("APP_VERSION", "dev"),
        }

    @app.before_request
    def block_restricted_users():
        from flask import request, redirect, url_for, flash
        from flask_login import current_user, logout_user

        if not current_user.is_authenticated:
            return None

        if not getattr(current_user, "is_blocked", False):
            return None

        endpoint = (request.endpoint or "")

        allowed_prefixes = (
            "auth.logout",
            "pages.privacy_policy",
            "pages.cookie_policy",
            "pages.offline_page",
            "pages.pwa_manifest",
            "static",
        )
        if endpoint.startswith(allowed_prefixes):
            return None

        logout_user()
        flash("Seu acesso está bloqueado. Fale com um administrador.", "danger")
        return redirect(url_for("auth.login"))

    @app.before_request
    def block_viewer_mutations():
        from flask import request, redirect, url_for, flash, jsonify
        from flask_login import current_user

        if not current_user.is_authenticated:
            return None

        if not getattr(current_user, "is_viewer", False):
            return None

        if request.method not in ("POST", "PUT", "DELETE", "PATCH"):
            return None

        endpoint = request.endpoint or ""

        if endpoint.startswith("api."):
            return jsonify({"error": "Acesso de visualização apenas."}), 403

        flash("Acesso de visualização apenas — edições não são permitidas.", "warning")
        return redirect(url_for("pages.dashboard"))

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.cli.employees_importer import import_employees
    app.cli.add_command(import_employees)

    from app.cli.employees_code_generator import generate_employee_codes
    app.cli.add_command(generate_employee_codes)

    from app.cli.set_user_password import set_user_password
    app.cli.add_command(set_user_password)

    from app.services.backup_service import start_backup_scheduler
    start_backup_scheduler(app)

    return app

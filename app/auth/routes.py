from flask import Blueprint, redirect, url_for, render_template, current_app, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from user_agents import parse

from app.auth.models import User
from app.auth.decorators import admin_required

from app.auth.service import (
    get_or_create_user,
    register_user,
    authenticate_local,
    change_user_password,
    attach_employee_and_profile,
    request_password_reset,
    reset_password
)

from app.auth.repository import (
    list_pending_users,
    approve_user,
    deny_user,
    list_all_users,
    get_user_by_id
)

bp = Blueprint("auth", __name__)
oauth = OAuth()

@bp.record_once
def setup_oauth(state):
    app = state.app
    oauth.init_app(app)

    google_id = app.config.get("GOOGLE_CLIENT_ID")
    google_secret = app.config.get("GOOGLE_CLIENT_SECRET")
    if google_id and google_secret:
        oauth.register(
            name="google",
            client_id=google_id,
            client_secret=google_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    github_id = app.config.get("GITHUB_CLIENT_ID")
    github_secret = app.config.get("GITHUB_CLIENT_SECRET")
    if github_id and github_secret:
        oauth.register(
            name="github",
            client_id=github_id,
            client_secret=github_secret,
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "user:email"},
        )

@bp.route("/login")
def login():
    user_agent = parse(request.headers.get("User-Agent", ""))

    if user_agent.is_mobile:
        return redirect(url_for("auth.login_mobile_choice"))

    return render_template("auth/login.html")

@bp.route("/login/google")
def login_google():

    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        flash("Login com Google indisponível no momento", "warning")
        return redirect(url_for("auth.login"))

    base_url = current_app.config.get("BASE_URL")

    if base_url:
        redirect_uri = f"{base_url}/auth/google/callback"
    else:
        redirect_uri = url_for("auth.google_callback", _external=True)

    return oauth.google.authorize_redirect(redirect_uri)


@bp.route("/google/callback")
def google_callback():

    try:
        token = oauth.google.authorize_access_token()
    except Exception:
        flash("Erro ao autenticar com Google", "danger")
        return redirect(url_for("auth.login"))

    try:
        userinfo = oauth.google.parse_id_token(token)
    except Exception:
        flash("Erro ao obter dados do Google", "danger")
        return redirect(url_for("auth.login"))

    if not userinfo:
        flash("Falha na autenticação Google", "danger")
        return redirect(url_for("auth.login"))

    user_data = get_or_create_user(userinfo, "google")
    login_user(User(user_data))

    return redirect(url_for("pages.inicio"))

@bp.route("/login/github")
def login_github():

    if not current_app.config.get("GITHUB_CLIENT_ID"):
        flash("Login com GitHub indisponível no momento", "warning")
        return redirect(url_for("auth.login"))

    base_url = current_app.config.get("BASE_URL")

    if base_url:
        redirect_uri = f"{base_url}/auth/github/callback"
    else:
        redirect_uri = url_for("auth.github_callback", _external=True)

    return oauth.github.authorize_redirect(redirect_uri)


@bp.route("/github/callback")
def github_callback():

    try:
        token = oauth.github.authorize_access_token()
    except Exception:
        flash("Erro ao autenticar com GitHub", "danger")
        return redirect(url_for("auth.login"))

    try:
        resp = oauth.github.get("user")
        profile = resp.json()
    except Exception:
        flash("Erro ao obter dados do GitHub", "danger")
        return redirect(url_for("auth.login"))

    if not profile:
        flash("Falha na autenticação GitHub", "danger")
        return redirect(url_for("auth.login"))

    email = profile.get("email")

    if not email:
        try:
            emails = oauth.github.get("user/emails").json()
            primary = next(
                (e for e in emails if e.get("primary") and e.get("verified")),
                None
            )
            if primary:
                email = primary.get("email")
        except Exception:
            pass

    if not email:
        flash("Não foi possível obter o email do GitHub", "danger")
        return redirect(url_for("auth.login"))

    profile["email"] = email

    user_data = get_or_create_user(profile, "github")
    login_user(User(user_data))

    return redirect(url_for("pages.inicio"))

@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@bp.route("/login/local", methods=["POST"])
def login_local():
    username = request.form["username"]
    password = request.form["password"]

    result = authenticate_local(username, password)

    if result == "PENDING":
        flash("Usuário aguardando aprovação", "warning")
        return redirect(url_for("auth.login"))

    if not result:
        flash("Usuário ou senha inválidos", "danger")
        return redirect(url_for("auth.login"))

    login_user(User(result))
    return redirect(url_for("pages.inicio"))

@bp.route("/register", methods=["POST"])
def register():
    try:
        user = register_user(request.form)
        attach_employee_and_profile(user["id"], request.form)
        flash(
            f"Usuário {user['username']} criado. Aguardando aprovação",
            "success"
        )
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("auth.login"))

@bp.route("/admin/users")
@login_required
@admin_required
def admin_users():
    search = request.args.get("q")
    users = list_pending_users(search)
    return render_template("auth/users_admin.html", users=users)

@bp.route("/admin/users/<int:user_id>/approve")
@login_required
def approve_user_route(user_id):
    if not current_user.is_admin:
        return redirect(url_for("pages.dashboard"))

    approve_user(user_id)
    flash("Usuário aprovado com sucesso", "success")
    return redirect(url_for("auth.admin_users"))

@bp.route("/admin/users/<int:user_id>/deny")
@login_required
def reject_user_route(user_id):
    if not current_user.is_admin:
        return redirect(url_for("pages.dashboard"))

    deny_user(user_id)
    flash("Usuário removido", "info")
    return redirect(url_for("auth.admin_users"))

@bp.route("/admin/users/all")
@login_required
@admin_required
def admin_users_all():
    """
    Página para exibir TODOS os usuários (ativos e pendentes)
    """
    search = request.args.get("q")
    users = list_all_users(search)
    return render_template("auth/users_all.html", users=users)

@bp.route("/login/mobile")
def login_mobile_choice():
    return render_template("auth/mobile/login_choice.html")

@bp.route("/login/mobile/form")
def login_mobile_form():
    return render_template("auth/mobile/login_form.html")

@bp.route("/register/mobile")
def register_mobile_form():
    return render_template("auth/mobile/register_form.html")

@bp.route("/meu-perfil", methods=["GET", "POST"])
@login_required
def my_profile():
    user_data = get_user_by_id(current_user.id)

    if request.method == "POST":

        file = request.files.get("profile_image")
        if file:
            from app.auth.service import save_profile_image
            try:
                save_profile_image(current_user.id, file)
            except ValueError as e:
                flash(str(e), "danger")

        attach_employee_and_profile(current_user.id, request.form)

        try:
            change_user_password(
                user_id=current_user.id,
                current_password=request.form.get("current_password"),
                new_password=request.form.get("new_password"),
                confirm_password=request.form.get("confirm_password"),
            )
            flash("Dados atualizados com sucesso", "success")

        except ValueError as e:
            flash(str(e), "danger")

        return redirect(url_for("auth.my_profile"))

    from app.auth.profile_repository import get_profile
    profile = get_profile(current_user.id)

    return render_template(
        "auth/myperfil.html",
        user=user_data,
        profile=profile,
        active_menu="perfil"
    )

@bp.route("/admin/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def update_user_role_route(user_id):
    role = request.form.get("role")
    from app.auth.repository import update_user_role
    update_user_role(user_id, role)
    flash("Perfil do usuário atualizado", "success")
    return redirect(url_for("auth.admin_users_all"))

@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")

        request_password_reset(email)

        flash(
            "Se o email existir, você receberá instruções para redefinir a senha.",
            "info"
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")

@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password_route(token):
    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password != confirm:
            flash("As senhas não conferem", "danger")
            return redirect(request.url)

        try:
            reset_password(token, password)
            flash("Senha redefinida com sucesso", "success")
            return redirect(url_for("auth.login"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("auth/reset_password.html")

@bp.route("/register")
def register_form():
    return render_template("auth/register.html")

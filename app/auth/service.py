import os
import re
import cloudinary
import cloudinary.uploader
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from app.utils.text import normalize_username

from app.auth.repository import (
    get_user_by_provider,
    create_user,
    create_local_user,
    get_user_by_username,
    count_users,
    get_user_by_id,
    update_user_password,
    get_user_by_matricula,
    update_profile_image,
    create_password_reset_token,
    get_password_reset_token,
    mark_token_as_used,
)

from app.auth.profile_repository import (
    find_employee_by_name,
    link_user_to_employee,
    upsert_profile,
)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
_SPECIAL_CHARS = r'[@$#!%&*^()_+\-=\[\]{};\':"\\|,.<>/?]'
_PASSWORD_MAX_AGE_DAYS = 180

# =====================================================
# PASSWORD POLICY
# =====================================================
def _validate_password_complexity(password: str, username: str = ""):
    if len(password) < 10:
        raise ValueError("A senha deve ter pelo menos 10 caracteres")
    if not re.search(r'[A-Z]', password):
        raise ValueError("A senha deve conter pelo menos uma letra maiúscula")
    if not re.search(r'[a-z]', password):
        raise ValueError("A senha deve conter pelo menos uma letra minúscula")
    if not re.search(r'\d', password):
        raise ValueError("A senha deve conter pelo menos um número")
    if not re.search(_SPECIAL_CHARS, password):
        raise ValueError("A senha deve conter pelo menos um caractere especial (@$#!%&*^ etc.)")
    password_lower = password.lower()
    if username and username.lower() in password_lower:
        raise ValueError("A senha não pode conter o nome de usuário")
    if "venttos" in password_lower:
        raise ValueError("A senha não pode conter o nome da empresa")

# =====================================================
# OAUTH
# =====================================================
def get_or_create_user(profile, provider):
    provider_id = str(profile.get("sub") or profile.get("id"))
    email = profile.get("email")

    if not email:
        raise ValueError("NO_EMAIL")

    user = get_user_by_provider(provider, provider_id)
    if user:
        if not user["is_active"]:
            raise ValueError("PENDING")
        return user

    from app.auth.repository import get_user_by_email

    existing_user = get_user_by_email(email)

    if not existing_user:
        raise ValueError("NOT_FOUND")

    if not existing_user["is_active"]:
        raise ValueError("PENDING")

    from app.extensions import get_db

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET provider = %s,
                    provider_id = %s
                WHERE id = %s
            """, (provider, provider_id, existing_user["id"]))
        conn.commit()

    return get_user_by_id(existing_user["id"])

# ====================================================
# REGISTER
# =====================================================
def generate_username(full_name: str) -> str:
    parts = full_name.strip().split()
    raw_username = f"{parts[0]}.{parts[-1]}"
    return normalize_username(raw_username)


def generate_special_matricula(user_type: str) -> str:
    """
    Gera matrícula interna para:
    PJ, DIRECTOR, OWNER
    """

    from app.extensions import get_db
    from psycopg.rows import dict_row

    prefix_map = {
        "PJ": "PJ-",
        "DIRECTOR": "DIR-",
        "OWNER": "OWR-"
    }

    prefix = prefix_map.get(user_type)
    if not prefix:
        return None

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT COUNT(*) AS total
                FROM users
                WHERE matricula LIKE %s
            """, (f"{prefix}%",))
            total = cur.fetchone()["total"] + 1

    return f"{prefix}{str(total).zfill(6)}"


def register_user(form):

    if form["password"] != form["password_confirm"]:
        raise ValueError("As senhas não conferem")

    full_name = form["full_name"]
    username = generate_username(full_name)
    _validate_password_complexity(form["password"], username)
    password_hash = generate_password_hash(form["password"])
    is_first_user = count_users() == 0

    user_type = form.get("user_type") or "CLT"
    matricula = form.get("matricula") or None

    if user_type == "CLT":
        if not matricula:
            raise ValueError("Matrícula obrigatória para colaboradores CLT")
    else:
        matricula = generate_special_matricula(user_type)

    return create_local_user({
        "username": username,
        "email": form["email"],
        "full_name": full_name,
        "matricula": matricula,
        "setor": form["setor"],
        "password_hash": password_hash,
        "is_active": is_first_user,
        "is_admin": is_first_user,
        "user_type": user_type
    })

# =====================================================
# LOGIN LOCAL
# =====================================================
def authenticate_local(username, password):
    from datetime import datetime, timedelta

    user = get_user_by_username(username)

    if not user:
        return None

    if not user["is_active"]:
        return "PENDING"

    if not check_password_hash(user["password_hash"], password):
        return None

    password_changed_at = user.get("password_changed_at")
    if password_changed_at:
        age = datetime.utcnow() - password_changed_at.replace(tzinfo=None)
        if age > timedelta(days=_PASSWORD_MAX_AGE_DAYS):
            return {"status": "EXPIRED", "user": user}

    return user

# =====================================================
# PASSWORD
# =====================================================
def change_user_password(user_id, current_password, new_password, confirm_password):
    if not new_password:
        return "EMPTY"

    if new_password != confirm_password:
        raise ValueError("Nova senha e confirmação não conferem")

    user = get_user_by_id(user_id)

    if not check_password_hash(user["password_hash"], current_password):
        raise ValueError("Senha atual incorreta")

    if check_password_hash(user["password_hash"], new_password):
        raise ValueError("A nova senha não pode ser igual à senha atual")

    _validate_password_complexity(new_password, user.get("username", ""))
    update_user_password(user_id, new_password)

    return "OK"

# =====================================================
# PROFILE + EMPLOYEE LINK
# =====================================================
def attach_employee_and_profile(user_id: int, form):
    """
    - link user to employee by full_name (se existir)
    - save contact/address profile
    """

    full_name = form.get("full_name")
    if full_name:
        employee = find_employee_by_name(full_name)
        if employee:
            link_user_to_employee(user_id, employee["id"])

    upsert_profile(user_id, form)

def confirm_employee_extra(identifier: str, password: str):
    """
    Confirma assinatura por:
    - matrícula (CLT)
    - username (PJ / Diretor / Admin)
    """

    identifier = identifier.strip()

    user = get_user_by_matricula(identifier)

    if not user:
        from app.auth.repository import get_user_by_username
        user = get_user_by_username(identifier)

    if not user:
        return {"success": False, "error": "Usuário não encontrado"}

    if not user["is_active"]:
        return {"success": False, "error": "Usuário inativo"}

    if not check_password_hash(user["password_hash"], password):
        return {"success": False, "error": "Senha inválida"}

    return {
        "success": True,
        "username": user["username"]
    }

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_image(user_id: int, file):
    if not file or file.filename == "":
        return None

    if not allowed_file(file.filename):
        raise ValueError("Formato de imagem não suportado")

    cloud_name = current_app.config.get("CLOUDINARY_CLOUD_NAME")
    api_key = current_app.config.get("CLOUDINARY_API_KEY")
    api_secret = current_app.config.get("CLOUDINARY_API_SECRET")

    if not all([cloud_name, api_key, api_secret]):
        raise ValueError("Serviço de upload de imagem não configurado")

    cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)

    result = cloudinary.uploader.upload(
        file,
        public_id=f"smt_manager/avatars/user_{user_id}",
        overwrite=True,
        resource_type="image",
        transformation={"width": 200, "height": 200, "crop": "fill", "gravity": "face"},
    )

    url = result["secure_url"]
    update_profile_image(user_id, url)
    return url


def remove_profile_image(user_id: int):
    from app.auth.repository import get_user_by_id

    user = get_user_by_id(user_id)
    if not user or not user.get("profile_image"):
        return

    cloud_name = current_app.config.get("CLOUDINARY_CLOUD_NAME")
    api_key = current_app.config.get("CLOUDINARY_API_KEY")
    api_secret = current_app.config.get("CLOUDINARY_API_SECRET")

    if all([cloud_name, api_key, api_secret]):
        cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)
        cloudinary.uploader.destroy(f"smt_manager/avatars/user_{user_id}", resource_type="image")

    update_profile_image(user_id, None)

# =====================================================
# RESET SENHA
# =====================================================
def _build_external_url(path: str) -> str:
    """
    Gera URL externa priorizando BASE_URL (Railway/proxy),
    e cai para url_for(_external=True) quando BASE_URL não existir.
    """
    path = "/" + (path or "").lstrip("/")
    base = (current_app.config.get("BASE_URL") or "").rstrip("/")
    if base:
        return f"{base}{path}"

    from flask import url_for
    return url_for(path, _external=True)


def request_password_reset(email: str):
    from app.extensions import get_db
    from psycopg.rows import dict_row
    from app.services.email_service import send_email
    from flask import url_for

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone()

    if not user:
        return None

    token = create_password_reset_token(user["id"])

    base = (current_app.config.get("BASE_URL") or "").rstrip("/")
    if base:
        reset_url = f"{base}/auth/reset-password/{token}"
    else:
        reset_url = url_for("auth.reset_password_route", token=token, _external=True)

    subject = "Redefinição de senha - FactoryOps"
    body = f"""
Olá {user.get('full_name') or user.get('username')},

Você solicitou a redefinição de senha no FactoryOps.

Clique no link abaixo para criar uma nova senha:

{reset_url}

Este link expira em 1 hora.

Se você não solicitou isso, ignore este email.
"""

    ok = send_email(user["email"], subject, body)

    if not ok:
        current_app.logger.error("Password reset email failed to send (SendGrid/SMTP).")

    return token


def reset_password(token: str, new_password: str):
    token_data = get_password_reset_token(token)
    if not token_data:
        raise ValueError("Token inválido ou expirado")

    user = get_user_by_id(token_data["user_id"])
    _validate_password_complexity(new_password, user.get("username", "") if user else "")
    update_user_password(token_data["user_id"], new_password)
    mark_token_as_used(token)

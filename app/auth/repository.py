import uuid
from app.extensions import get_db
from psycopg.rows import dict_row
from werkzeug.security import generate_password_hash
from app.utils.text import normalize_username
from datetime import datetime, timedelta


def get_user_by_id(user_id):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM users WHERE id=%s",
                (user_id,)
            )
            return cur.fetchone()


def get_owner_user_id():
    """
    Retorna o ID do "Owner" do sistema:
    - o primeiro usuário criado (menor created_at; fallback por menor id)
    Regras de segurança:
    - este usuário NÃO pode ser rebaixado (perder admin)
    - este usuário NÃO pode ser bloqueado
    """
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id
                FROM users
                ORDER BY created_at ASC NULLS LAST, id ASC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            return row["id"] if row else None


def get_user_by_provider(provider, provider_id):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT * FROM users
                WHERE provider=%s AND provider_id=%s
                """,
                (provider, provider_id),
            )
            return cur.fetchone()


def create_user(data):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO users
                (username, email, provider, provider_id, is_active)
                VALUES (%s,%s,%s,%s,TRUE)
                RETURNING *
                """,
                (
                    data["username"],
                    data["email"],
                    data["provider"],
                    data["provider_id"],
                ),
            )
            conn.commit()
            return cur.fetchone()


def get_user_by_username(username: str):
    """
    Busca usuário por username de forma accent-insensitive.
    - Normaliza o username digitado
    - Normaliza TODOS os usernames do banco
    - Compara em Python (fonte da verdade)
    """
    username_norm = normalize_username(username)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT *
                FROM users
                WHERE provider = 'local'
            """)
            users = cur.fetchall()

    for user in users:
        db_username = user.get("username", "")
        if normalize_username(db_username) == username_norm:
            return user

    return None


def create_local_user(data):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO users
                (username, email, full_name, matricula, setor,
                 password_hash, provider, is_active, is_admin, user_type)
                VALUES (%s,%s,%s,%s,%s,%s,'local',%s,%s,%s)
                RETURNING *
                """,
                (
                    data["username"],
                    data["email"],
                    data["full_name"],
                    data.get("matricula"),
                    data["setor"],
                    data["password_hash"],
                    data["is_active"],
                    data["is_admin"],
                    data.get("user_type", "CLT")
                ),
            )
            conn.commit()
            return cur.fetchone()


def list_pending_users(search=None):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if search:
                cur.execute(
                    """
                    SELECT * FROM users
                    WHERE is_active=FALSE
                      AND provider='local'
                      AND full_name ILIKE %s
                    ORDER BY created_at DESC
                    """,
                    (f"%{search}%",),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM users
                    WHERE is_active=FALSE
                      AND provider='local'
                    ORDER BY created_at DESC
                    """
                )
            return cur.fetchall()


def approve_user(user_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET is_active=TRUE WHERE id=%s",
                (user_id,),
            )
            conn.commit()


def deny_user(user_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM users WHERE id=%s",
                (user_id,),
            )
            conn.commit()


def delete_user(user_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM users WHERE id=%s",
                (user_id,),
            )
            conn.commit()


def count_users():
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT COUNT(*) AS total FROM users")
            row = cur.fetchone()
            return row["total"]


def list_all_users(search=None):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if search:
                cur.execute(
                    """
                    SELECT * FROM users
                    WHERE full_name ILIKE %s OR username ILIKE %s OR setor ILIKE %s
                    ORDER BY created_at DESC
                    """,
                    (f"%{search}%", f"%{search}%", f"%{search}%")
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM users
                    ORDER BY created_at DESC
                    """
                )
            return cur.fetchall()


def update_user_password(user_id: int, new_password: str):
    password_hash = generate_password_hash(new_password)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
                """,
                (password_hash, user_id),
            )
            conn.commit()


def update_user_role(user_id: int, role: str):
    """
    Perfis:
    - admin: is_admin = TRUE, extra_authorized = FALSE
    - blocked: extra_authorized = TRUE (novo significado: usuário bloqueado)
    - none: remove admin e remove bloqueio

    Observação:
    - Mantém compatibilidade: se a UI antiga enviar "extra", trata como "blocked".

    Regra crítica:
    - O primeiro usuário do sistema (OWNER) não pode ser rebaixado nem bloqueado.
    """
    role = (role or "").strip().lower()
    if role == "extra":
        role = "blocked"

    owner_id = get_owner_user_id()
    if owner_id is not None and int(user_id) == int(owner_id):
        # owner só pode ficar como admin, sempre ativo e não bloqueado
        if role != "admin":
            raise ValueError("A conta OWNER (primeiro administrador) não pode ser rebaixada ou bloqueada.")

    with get_db() as conn:
        with conn.cursor() as cur:
            if role == "admin":
                cur.execute(
                    """
                    UPDATE users
                    SET is_admin=TRUE,
                        extra_authorized=FALSE
                    WHERE id=%s
                    """,
                    (user_id,)
                )
            elif role == "blocked":
                cur.execute(
                    """
                    UPDATE users
                    SET is_admin=FALSE,
                        extra_authorized=TRUE
                    WHERE id=%s
                    """,
                    (user_id,)
                )
            else:
                cur.execute(
                    """
                    UPDATE users
                    SET is_admin=FALSE,
                        extra_authorized=FALSE
                    WHERE id=%s
                    """,
                    (user_id,)
                )
        conn.commit()


def get_user_by_matricula(matricula: str):
    """
    Normaliza matrícula removendo zeros à esquerda
    para evitar inconsistência entre cadastro e uso.
    """
    matricula_normalizada = matricula.lstrip("0")

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, username, password_hash, is_active
                FROM users
                WHERE ltrim(matricula, '0') = %s
                LIMIT 1
            """, (matricula_normalizada,))
            return cur.fetchone()


def update_profile_image(user_id: int, image_path: str):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET profile_image = %s
                WHERE id = %s
                """,
                (image_path, user_id),
            )
        conn.commit()


def create_password_reset_token(user_id: int):
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (%s,%s,%s)
            """, (user_id, token, expires_at))
        conn.commit()

    return token


def get_password_reset_token(token: str):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT *
                FROM password_reset_tokens
                WHERE token=%s
                  AND used=FALSE
                  AND expires_at > now()
            """, (token,))
            return cur.fetchone()


def mark_token_as_used(token: str):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE password_reset_tokens
                SET used=TRUE
                WHERE token=%s
            """, (token,))
        conn.commit()


def get_user_by_email(email: str):
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM users WHERE LOWER(email)=LOWER(%s)",
                (email,)
            )
            return cur.fetchone()

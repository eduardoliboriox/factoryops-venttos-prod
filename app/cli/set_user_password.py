import click
from werkzeug.security import generate_password_hash
from app.extensions import get_db
from psycopg.rows import dict_row


@click.command("set-user-password")
@click.argument("username")
@click.argument("password")
def set_user_password(username, password):
    """Set password and activate a user by username (admin CLI, bypasses policy)."""
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT id, username, is_active, provider FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

        if not user:
            click.echo(f"Usuário '{username}' não encontrado.")
            return

        password_hash = generate_password_hash(password)

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET password_hash = %s,
                    provider = 'local',
                    is_active = TRUE,
                    password_changed_at = NOW()
                WHERE username = %s
                """,
                (password_hash, username),
            )
        conn.commit()

    click.echo(f"Usuário '{username}' atualizado: senha definida, provider=local, is_active=TRUE.")

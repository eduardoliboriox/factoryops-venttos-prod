import psycopg
from psycopg.rows import dict_row
from flask_login import LoginManager
from flask import current_app

login_manager = LoginManager()

def get_db():
    return psycopg.connect(
        current_app.config["DATABASE_URL"],
        row_factory=dict_row,
        sslmode="require"
    )

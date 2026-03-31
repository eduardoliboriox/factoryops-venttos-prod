from __future__ import annotations

from typing import Optional
from psycopg.rows import dict_row

from app.extensions import get_db


_SCHEMA_READY: bool = False


def _ensure_schema():
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    id         BIGSERIAL PRIMARY KEY,
                    user_id    BIGINT,
                    endpoint   TEXT NOT NULL UNIQUE,
                    p256dh     TEXT NOT NULL,
                    auth       TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user_id
                ON push_subscriptions (user_id)
                """
            )
        conn.commit()

    _SCHEMA_READY = True


def upsert_subscription(
    endpoint: str,
    p256dh: str,
    auth: str,
    user_id: Optional[int] = None,
) -> None:
    _ensure_schema()
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (endpoint) DO UPDATE
                  SET user_id = EXCLUDED.user_id,
                      p256dh  = EXCLUDED.p256dh,
                      auth    = EXCLUDED.auth
                """,
                (user_id, endpoint, p256dh, auth),
            )
        conn.commit()


def delete_subscription(endpoint: str) -> None:
    _ensure_schema()
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM push_subscriptions WHERE endpoint = %s",
                (endpoint,),
            )
        conn.commit()


def list_all_subscriptions() -> list[dict]:
    _ensure_schema()
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, user_id, endpoint, p256dh, auth
                FROM push_subscriptions
                ORDER BY id ASC
                """
            )
            return cur.fetchall() or []


def list_subscriptions_by_user_ids(user_ids: list[int]) -> list[dict]:
    if not user_ids:
        return []
    _ensure_schema()
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, user_id, endpoint, p256dh, auth
                FROM push_subscriptions
                WHERE user_id = ANY(%s)
                ORDER BY id ASC
                """,
                (user_ids,),
            )
            return cur.fetchall() or []

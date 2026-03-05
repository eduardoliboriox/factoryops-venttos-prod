from __future__ import annotations

from typing import Optional
from psycopg.rows import dict_row

from app.extensions import get_db


def upsert_subscription(
    endpoint: str,
    p256dh: str,
    auth: str,
    user_id: Optional[int] = None,
) -> None:
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
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM push_subscriptions WHERE endpoint = %s",
                (endpoint,),
            )
        conn.commit()


def list_all_subscriptions() -> list[dict]:
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

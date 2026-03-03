from __future__ import annotations

from typing import Optional
from psycopg.rows import dict_row

from app.extensions import get_db


_SCHEMA_READY: bool = False
_SEEDED: bool = False


def _ensure_schema():
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS production_lines (
                  setor TEXT NOT NULL,
                  nome  TEXT NOT NULL,
                  ativo BOOLEAN NOT NULL DEFAULT true,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                  PRIMARY KEY (setor, nome)
                )
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_production_lines_setor_ativo
                ON production_lines (setor, ativo)
                """
            )

        conn.commit()

    _SCHEMA_READY = True


def _seed_defaults_if_empty():
    """
    Semeia valores default apenas se a tabela estiver vazia.
    Idempotente e seguro (não duplica por PK).
    """
    global _SEEDED
    if _SEEDED:
        return

    _ensure_schema()

    defaults = {
        "IM": ["IM-01", "IM-02", "IM-03", "IM-04", "IM-05", "IM-06"],
        "PA": ["IP-COM", "PA-01", "PA-03", "PA-04", "PA-07", "PA-08", "PA-09", "PA-13", "WIFI"],
        "PTH": ["ADE-01", "AXI-01", "AXI-02", "AXI-03", "JUM-01", "JUM-02", "RAD-01", "RAD-02", "RAD-03", "ROU-01", "ROU-02", "ROU-03"],
        "SMT": ["SMT-01", "SMT-02", "SMT-03", "SMT-04", "SMT-05", "SMT-06", "SMT-07", "SMT-08", "SMT-09"],
    }

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT COUNT(*) AS n FROM production_lines")
            n = int((cur.fetchone() or {}).get("n") or 0)

            if n == 0:
                for setor, linhas in defaults.items():
                    for nome in linhas:
                        cur.execute(
                            """
                            INSERT INTO production_lines (setor, nome, ativo)
                            VALUES (%s, %s, true)
                            ON CONFLICT (setor, nome) DO NOTHING
                            """,
                            (setor, nome),
                        )

        conn.commit()

    _SEEDED = True


def list_sectors() -> list[str]:
    _seed_defaults_if_empty()

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT DISTINCT setor
                FROM production_lines
                WHERE ativo = true
                ORDER BY setor ASC
                """
            )
            return [r["setor"] for r in (cur.fetchall() or [])]


def list_lines_by_sector(setor: str) -> list[str]:
    _seed_defaults_if_empty()

    setor = (setor or "").strip()
    if not setor:
        return []

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT nome
                FROM production_lines
                WHERE setor = %s
                  AND ativo = true
                ORDER BY nome ASC
                """,
                (setor,),
            )
            return [r["nome"] for r in (cur.fetchall() or [])]

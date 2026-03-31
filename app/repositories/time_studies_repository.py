from __future__ import annotations

from typing import Optional, Any

from psycopg.rows import dict_row
from psycopg import sql

from app.extensions import get_db


_SCHEMA_READY: bool = False


def _ensure_schema():
    """
    Cria as tabelas do módulo Time Study de forma idempotente.
    Seguro para prod e develop (sem Alembic).
    """
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS time_studies (
                  id BIGSERIAL PRIMARY KEY,
                  produto TEXT NOT NULL,
                  cliente TEXT,
                  setor TEXT NOT NULL,
                  linha TEXT NOT NULL,

                  uph_meta INTEGER NOT NULL DEFAULT 0,
                  hc_meta NUMERIC(10,2) NOT NULL DEFAULT 0,

                  perda_padrao NUMERIC(10,2) NOT NULL DEFAULT 0.10,
                  horas_turno NUMERIC(10,2) NOT NULL DEFAULT 8.30,

                  info_adicionais TEXT,

                  created_by_user_id BIGINT,
                  created_by_username TEXT,

                  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS time_study_operations (
                  id BIGSERIAL PRIMARY KEY,
                  study_id BIGINT NOT NULL REFERENCES time_studies(id) ON DELETE CASCADE,

                  ordem INTEGER NOT NULL DEFAULT 1,
                  operacao TEXT NOT NULL,

                  tempo_ciclo_sec NUMERIC(12,2) NOT NULL,
                  posto_trabalho INTEGER NOT NULL DEFAULT 1,
                  hc NUMERIC(10,2) NOT NULL DEFAULT 1.00,

                  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_time_studies_created_at
                ON time_studies (created_at DESC)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ts_ops_study_ordem
                ON time_study_operations (study_id, ordem ASC, id ASC)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ts_ops_study_id
                ON time_study_operations (study_id)
                """
            )

        conn.commit()

    _SCHEMA_READY = True


# ==========================================================
# STUDIES (CRUD)
# ==========================================================

def list_studies(limit: int = 50) -> list[dict]:
    _ensure_schema()

    limit = int(limit or 50)
    limit = min(max(limit, 1), 200)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                  id,
                  produto,
                  cliente,
                  setor,
                  linha,
                  uph_meta,
                  hc_meta,
                  perda_padrao,
                  horas_turno,
                  info_adicionais,
                  created_by_user_id,
                  created_by_username,
                  created_at
                FROM time_studies
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall() or []


def create_study(data: dict, *, user_id: Optional[int] = None, username: Optional[str] = None) -> dict:
    _ensure_schema()

    produto = (data.get("produto") or "").strip()
    cliente = (data.get("cliente") or "").strip() or None
    setor = (data.get("setor") or "").strip() or "SMT"
    linha = (data.get("linha") or "").strip()

    uph_meta = int(data.get("uph_meta") or 0)
    hc_meta = float(data.get("hc_meta") or 0)

    perda_padrao = float(data.get("perda_padrao") or 0.10)
    horas_turno = float(data.get("horas_turno") or 8.30)

    info = (data.get("info_adicionais") or "").strip() or None

    if not produto:
        raise ValueError("Produto é obrigatório")
    if not linha:
        raise ValueError("Linha é obrigatória")

    perda_padrao = min(max(perda_padrao, 0.0), 0.80)
    horas_turno = min(max(horas_turno, 1.0), 24.0)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO time_studies
                  (produto, cliente, setor, linha, uph_meta, hc_meta, perda_padrao, horas_turno, info_adicionais,
                   created_by_user_id, created_by_username)
                VALUES
                  (%s, %s, %s, %s, %s, %s::numeric, %s::numeric, %s::numeric, %s, %s, %s)
                RETURNING
                  id, produto, cliente, setor, linha, uph_meta, hc_meta, perda_padrao, horas_turno, info_adicionais,
                  created_by_user_id, created_by_username, created_at
                """,
                (
                    produto,
                    cliente,
                    setor,
                    linha,
                    uph_meta,
                    hc_meta,
                    perda_padrao,
                    horas_turno,
                    info,
                    user_id,
                    username,
                ),
            )
            row = cur.fetchone()

        conn.commit()

    return row or {}


def delete_study(study_id: int) -> None:
    _ensure_schema()

    sid = int(study_id)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM time_studies WHERE id = %s", (sid,))
        conn.commit()


def get_study(study_id: int) -> Optional[dict]:
    _ensure_schema()

    sid = int(study_id)
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                  id,
                  produto,
                  cliente,
                  setor,
                  linha,
                  uph_meta,
                  hc_meta,
                  perda_padrao,
                  horas_turno,
                  info_adicionais,
                  created_by_user_id,
                  created_by_username,
                  created_at
                FROM time_studies
                WHERE id = %s
                LIMIT 1
                """,
                (sid,),
            )
            return cur.fetchone()


# ==========================================================
# OPERATIONS (CRUD)
# ==========================================================

def list_operations(study_id: int) -> list[dict]:
    _ensure_schema()

    sid = int(study_id)
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                  id,
                  study_id,
                  ordem,
                  operacao,
                  tempo_ciclo_sec,
                  posto_trabalho,
                  hc,
                  created_at
                FROM time_study_operations
                WHERE study_id = %s
                ORDER BY ordem ASC, id ASC
                """,
                (sid,),
            )
            return cur.fetchall() or []


def add_operation(study_id: int, data: dict) -> dict:
    _ensure_schema()

    sid = int(study_id)

    ordem = int(data.get("ordem") or 1)
    operacao = (data.get("operacao") or "").strip()
    tempo = float(data.get("tempo_ciclo_sec") or 0)
    posto = int(data.get("posto_trabalho") or 1)
    hc = float(data.get("hc") or 1.0)

    if not operacao:
        raise ValueError("Operação é obrigatória")
    if tempo <= 0:
        raise ValueError("Tempo de ciclo inválido")
    if ordem <= 0:
        ordem = 1
    if posto <= 0:
        posto = 1
    if hc <= 0:
        hc = 1.0

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO time_study_operations
                  (study_id, ordem, operacao, tempo_ciclo_sec, posto_trabalho, hc)
                VALUES
                  (%s, %s, %s, %s::numeric, %s, %s::numeric)
                RETURNING
                  id, study_id, ordem, operacao, tempo_ciclo_sec, posto_trabalho, hc, created_at
                """,
                (sid, ordem, operacao, tempo, posto, hc),
            )
            row = cur.fetchone()

        conn.commit()

    return row or {}


def update_operation(op_id: int, data: dict) -> dict:
    _ensure_schema()

    oid = int(op_id)

    allowed = {
        "ordem": "ordem",
        "operacao": "operacao",
        "tempo_ciclo_sec": "tempo_ciclo_sec",
        "posto_trabalho": "posto_trabalho",
        "hc": "hc",
    }

    sets = []
    values: list[Any] = []

    for k, col in allowed.items():
        if k not in data:
            continue

        v = data.get(k)

        if k == "operacao":
            v = (v or "").strip()
            if not v:
                raise ValueError("Operação é obrigatória")
            sets.append(sql.SQL("{} = %s").format(sql.Identifier(col)))
            values.append(v)

        elif k == "tempo_ciclo_sec":
            vnum = float(v or 0)
            if vnum <= 0:
                raise ValueError("Tempo de ciclo inválido")
            sets.append(sql.SQL("{} = %s::numeric").format(sql.Identifier(col)))
            values.append(vnum)

        elif k == "hc":
            vnum = float(v or 0)
            if vnum <= 0:
                raise ValueError("HC inválido")
            sets.append(sql.SQL("{} = %s::numeric").format(sql.Identifier(col)))
            values.append(vnum)

        elif k in ("ordem", "posto_trabalho"):
            vint = int(v or 0)
            if vint <= 0:
                vint = 1
            sets.append(sql.SQL("{} = %s").format(sql.Identifier(col)))
            values.append(vint)

    if not sets:
        # nada para atualizar -> retorna registro atual
        with get_db() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT id, study_id, ordem, operacao, tempo_ciclo_sec, posto_trabalho, hc, created_at
                    FROM time_study_operations
                    WHERE id = %s
                    """,
                    (oid,),
                )
                return cur.fetchone() or {}

    q = sql.SQL("UPDATE time_study_operations SET ") + sql.SQL(", ").join(sets) + sql.SQL(" WHERE id = %s RETURNING ") + sql.SQL(
        "id, study_id, ordem, operacao, tempo_ciclo_sec, posto_trabalho, hc, created_at"
    )

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, values + [oid])
            row = cur.fetchone()
        conn.commit()

    return row or {}


def delete_operation(op_id: int) -> None:
    _ensure_schema()

    oid = int(op_id)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM time_study_operations WHERE id = %s", (oid,))
        conn.commit()

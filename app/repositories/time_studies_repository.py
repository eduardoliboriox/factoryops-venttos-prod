from __future__ import annotations

from typing import Optional, Any

from psycopg.rows import dict_row

from app.extensions import get_db


_SCHEMA_READY: bool = False


def _ensure_schema():
    """
    Garante (idempotente) que a tabela de operações exista.
    Isso evita crash em ambientes novos/clonados sem Alembic.
    """
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS time_study_operations (
                  id BIGSERIAL PRIMARY KEY,
                  study_id BIGINT NOT NULL REFERENCES time_studies(id) ON DELETE CASCADE,
                  ordem INT NOT NULL,
                  operacao TEXT NOT NULL,
                  tempo_ciclo_sec NUMERIC(12,2) NOT NULL,
                  posto_trabalho INT NOT NULL,
                  hc NUMERIC(12,2) NOT NULL,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                  updated_at TIMESTAMPTZ
                )
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_time_study_operations_study_ordem
                ON time_study_operations (study_id, ordem ASC, id ASC)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_time_study_operations_study_id
                ON time_study_operations (study_id)
                """
            )

        conn.commit()

    _SCHEMA_READY = True


def list_studies(limit: int = 50):
    limit = int(limit or 50)
    limit = max(1, min(limit, 200))

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
                  revisao,
                  numero_estudo,
                  uph_meta,
                  hc_meta,
                  perda_padrao,
                  horas_turno,
                  created_at,
                  created_by_username
                FROM time_studies
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall() or []


def get_study(study_id: int) -> Optional[dict]:
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
                  revisao,
                  numero_estudo,
                  uph_meta,
                  hc_meta,
                  perda_padrao,
                  horas_turno,
                  info_adicionais,
                  velocidade_esteira,
                  controlador_inversor,
                  created_at,
                  updated_at,
                  created_by_user_id,
                  created_by_username
                FROM time_studies
                WHERE id = %s
                """,
                (study_id,),
            )
            return cur.fetchone()


def create_study(data: dict, *, user_id: Optional[int] = None, username: Optional[str] = None) -> dict:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO time_studies (
                  produto, cliente, setor, linha, revisao, numero_estudo,
                  uph_meta, hc_meta, perda_padrao, horas_turno,
                  info_adicionais, velocidade_esteira, controlador_inversor,
                  created_by_user_id, created_by_username
                )
                VALUES (
                  %s,%s,%s,%s,%s,%s,
                  %s,%s,%s,%s,
                  %s,%s,%s,
                  %s,%s
                )
                RETURNING *
                """,
                (
                    (data.get("produto") or "").strip(),
                    (data.get("cliente") or "").strip() or None,
                    (data.get("setor") or "").strip() or None,
                    (data.get("linha") or "").strip() or None,
                    (data.get("revisao") or "").strip() or None,
                    (data.get("numero_estudo") or "").strip() or None,
                    int(data.get("uph_meta") or 0),
                    float(data.get("hc_meta") or 0),
                    float(data.get("perda_padrao") or 0.10),
                    float(data.get("horas_turno") or 8.30),
                    (data.get("info_adicionais") or "").strip() or None,
                    (data.get("velocidade_esteira") or "").strip() or None,
                    (data.get("controlador_inversor") or "").strip() or None,
                    user_id,
                    username,
                ),
            )
            conn.commit()
            return cur.fetchone()


# ==========================================================
# OPERAÇÕES (TIME STUDY)
# ==========================================================

def list_operations(study_id: int):
    _ensure_schema()

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
                  created_at,
                  updated_at
                FROM time_study_operations
                WHERE study_id = %s
                ORDER BY ordem ASC, id ASC
                """,
                (study_id,),
            )
            return cur.fetchall() or []


def add_operation(study_id: int, data: dict) -> dict:
    _ensure_schema()

    ordem = int(data.get("ordem") or 0)
    operacao = (data.get("operacao") or "").strip()
    tempo_ciclo_sec = float(data.get("tempo_ciclo_sec") or 0)
    posto_trabalho = int(data.get("posto_trabalho") or 0)
    hc = float(data.get("hc") or 0)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO time_study_operations (
                  study_id, ordem, operacao, tempo_ciclo_sec, posto_trabalho, hc
                )
                VALUES (%s, %s, %s, %s::numeric, %s, %s::numeric)
                RETURNING *
                """,
                (study_id, ordem, operacao, tempo_ciclo_sec, posto_trabalho, hc),
            )
            conn.commit()
            return cur.fetchone()


def update_operation(op_id: int, data: dict) -> dict:
    _ensure_schema()

    allowed = {"ordem", "operacao", "tempo_ciclo_sec", "posto_trabalho", "hc"}

    sets = []
    values: list[Any] = []

    for k, v in (data or {}).items():
        if k not in allowed:
            continue

        if k in ("ordem", "posto_trabalho"):
            v = int(v)
        elif k in ("tempo_ciclo_sec", "hc"):
            v = float(v)
        elif k == "operacao":
            v = (str(v) or "").strip()

        sets.append(f"{k} = %s")
        values.append(v)

    if not sets:
        raise ValueError("Nada para atualizar")

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                UPDATE time_study_operations
                SET {", ".join(sets)}, updated_at = now()
                WHERE id = %s
                RETURNING *
                """,
                (*values, op_id),
            )
            row = cur.fetchone()
            conn.commit()

            if not row:
                raise ValueError("Operação não encontrada")

            return row


def delete_operation(op_id: int):
    _ensure_schema()

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM time_study_operations WHERE id = %s", (op_id,))
        conn.commit()


def delete_study(study_id: int):
    """
    Remove o estudo. As operações caem em cascade (FK ON DELETE CASCADE).
    Mesmo assim, deixamos o _ensure_schema para garantir consistência.
    """
    _ensure_schema()

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM time_studies WHERE id = %s", (study_id,))
        conn.commit()

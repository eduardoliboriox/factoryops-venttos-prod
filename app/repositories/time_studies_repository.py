from __future__ import annotations

from typing import Optional, Any

from psycopg.rows import dict_row

from app.extensions import get_db


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
                  produto, cliente, linha, revisao, numero_estudo,
                  uph_meta, hc_meta, perda_padrao, horas_turno,
                  info_adicionais, velocidade_esteira, controlador_inversor,
                  created_by_user_id, created_by_username
                )
                VALUES (
                  %s,%s,%s,%s,%s,
                  %s,%s,%s,%s,
                  %s,%s,%s,
                  %s,%s
                )
                RETURNING *
                """,
                (
                    (data.get("produto") or "").strip(),
                    (data.get("cliente") or "").strip() or None,
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


def delete_study(study_id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM time_studies WHERE id = %s", (study_id,))
        conn.commit()


def list_operations(study_id: int):
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
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO time_study_operations (
                  study_id, ordem, operacao, tempo_ciclo_sec, posto_trabalho, hc
                )
                VALUES (%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    study_id,
                    int(data.get("ordem") or 1),
                    (data.get("operacao") or "").strip(),
                    float(data.get("tempo_ciclo_sec") or 0),
                    int(data.get("posto_trabalho") or 1),
                    float(data.get("hc") or 1.0),
                ),
            )
            conn.commit()
            return cur.fetchone()


def update_operation(op_id: int, data: dict) -> dict:
    fields = []
    params: list[Any] = []

    if "ordem" in data:
        fields.append("ordem=%s")
        params.append(int(data.get("ordem") or 1))

    if "operacao" in data:
        fields.append("operacao=%s")
        params.append((data.get("operacao") or "").strip())

    if "tempo_ciclo_sec" in data:
        fields.append("tempo_ciclo_sec=%s")
        params.append(float(data.get("tempo_ciclo_sec") or 0))

    if "posto_trabalho" in data:
        fields.append("posto_trabalho=%s")
        params.append(int(data.get("posto_trabalho") or 1))

    if "hc" in data:
        fields.append("hc=%s")
        params.append(float(data.get("hc") or 1.0))

    if not fields:
        raise ValueError("Nada para atualizar")

    q = "UPDATE time_study_operations SET " + ", ".join(fields) + " WHERE id=%s RETURNING *"
    params.append(op_id)

    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, tuple(params))
            row = cur.fetchone()
        conn.commit()

    if not row:
        raise ValueError("Operação não encontrada")

    return row


def delete_operation(op_id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM time_study_operations WHERE id = %s", (op_id,))
        conn.commit()

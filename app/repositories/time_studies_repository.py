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

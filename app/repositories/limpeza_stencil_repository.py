import datetime
from psycopg.rows import dict_row
from app.extensions import get_db


def _to_time(val) -> datetime.time | None:
    if not val:
        return None
    try:
        parts = str(val).split(':')
        return datetime.time(int(parts[0]), int(parts[1]))
    except (ValueError, AttributeError, IndexError):
        return None


def create_registro(data: dict, user_id: int) -> dict:
    ano = datetime.date.today().year
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT COALESCE(MAX(sequencia), 0) + 1 FROM limpeza_stencil_registros WHERE ano=%s",
                (ano,),
            )
            sequencia = cur.fetchone()["coalesce"]
            doc_id = f"LS-{sequencia}-{ano}"

            cur.execute(
                """
                INSERT INTO limpeza_stencil_registros
                (data, cliente, setor, linha, identificacao_stencil, espessura,
                 created_by, ano, sequencia, doc_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    data["data"],
                    data.get("cliente"),
                    data.get("setor"),
                    data["linha"],
                    data.get("identificacao_stencil"),
                    data.get("espessura"),
                    user_id,
                    ano,
                    sequencia,
                    doc_id,
                ),
            )
            registro = cur.fetchone()
        conn.commit()
    return registro


def update_registro(registro_id: int, data: dict) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                UPDATE limpeza_stencil_registros
                SET data=%s, cliente=%s, setor=%s, linha=%s,
                    identificacao_stencil=%s, espessura=%s
                WHERE id=%s
                RETURNING *
                """,
                (
                    data["data"],
                    data.get("cliente"),
                    data.get("setor"),
                    data["linha"],
                    data.get("identificacao_stencil"),
                    data.get("espessura"),
                    registro_id,
                ),
            )
            registro = cur.fetchone()
        conn.commit()
    return registro


def upsert_horarios(registro_id: int, horarios: list):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM limpeza_stencil_horarios WHERE registro_id=%s",
                (registro_id,),
            )
            for h in horarios:
                cur.execute(
                    """
                    INSERT INTO limpeza_stencil_horarios
                    (registro_id, posicao, horario_inicio, horario_fim,
                     modelo, fase, status, observacao)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        registro_id,
                        int(h["posicao"]),
                        _to_time(h.get("horario_inicio")),
                        _to_time(h.get("horario_fim")),
                        h.get("modelo") or None,
                        h.get("fase") or None,
                        h.get("status") or None,
                        h.get("observacao") or None,
                    ),
                )
        conn.commit()


def upsert_assinaturas(registro_id: int, assinaturas: list):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM limpeza_stencil_assinaturas WHERE registro_id=%s",
                (registro_id,),
            )
            for a in assinaturas:
                cur.execute(
                    """
                    INSERT INTO limpeza_stencil_assinaturas
                    (registro_id, campo, username, timestamp)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (
                        registro_id,
                        a["campo"],
                        a["username"],
                        a.get("timestamp"),
                    ),
                )
        conn.commit()


def get_registro_by_id(registro_id: int) -> dict | None:
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT r.*, u.username AS created_username
                FROM limpeza_stencil_registros r
                LEFT JOIN users u ON u.id = r.created_by
                WHERE r.id=%s
                """,
                (registro_id,),
            )
            registro = cur.fetchone()
            if not registro:
                return None

            cur.execute(
                """
                SELECT posicao, horario_inicio, horario_fim,
                       modelo, fase, status, observacao
                FROM limpeza_stencil_horarios
                WHERE registro_id=%s
                ORDER BY posicao
                """,
                (registro_id,),
            )
            horarios = cur.fetchall()

            cur.execute(
                """
                SELECT campo, username, timestamp
                FROM limpeza_stencil_assinaturas
                WHERE registro_id=%s
                """,
                (registro_id,),
            )
            assinaturas = cur.fetchall()

    return {**registro, "horarios": list(horarios), "assinaturas": list(assinaturas)}


def list_registros(data=None, linha=None, limit=100) -> list:
    filters = []
    params = []
    if data:
        filters.append("r.data=%s")
        params.append(data)
    if linha:
        filters.append("r.linha=%s")
        params.append(linha)
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    params.append(limit)
    with get_db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT r.id, r.doc_id, r.data, r.setor, r.linha, r.cliente,
                       r.created_at, u.username
                FROM limpeza_stencil_registros r
                LEFT JOIN users u ON u.id = r.created_by
                {where}
                ORDER BY r.created_at DESC
                LIMIT %s
                """,
                params,
            )
            return cur.fetchall()
